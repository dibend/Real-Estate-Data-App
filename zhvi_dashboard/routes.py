from __future__ import annotations

import brotli
import json
from quart import Quart, abort, jsonify, render_template, request

from .charts import ChartService
from .data import DataStore
from .settings import Settings
from .state_meta import get_state_meta


def register_routes(app: Quart, store: DataStore, charts: ChartService, settings: Settings) -> None:
    def resolve_state(state: str | None) -> str:
        available_states = store.states
        requested = (state or settings.default_state or "").upper()
        if requested in available_states:
            return requested
        return available_states[0]

    # Startup preload
    @app.before_serving
    async def startup():
        store.ensure_loaded()  # warm cache

    # Compression for chart payloads
    @app.after_request
    async def compress_chart_payloads(response):
        if not request.path.startswith("/chart/"):
            return response
        if response.status_code != 200:
            return response
        if response.headers.get("Content-Encoding"):
            return response
        if "br" not in (request.headers.get("Accept-Encoding", "").lower()):
            return response
        if "application/json" not in (response.content_type or ""):
            return response

        payload = await response.get_data()
        if len(payload) < settings.chart_br_min_bytes:
            return response

        compressed = brotli.compress(payload, quality=5)
        response.set_data(compressed)
        response.headers["Content-Encoding"] = "br"
        response.headers["Content-Length"] = str(len(compressed))
        response.headers["Vary"] = "Accept-Encoding"
        return response

    # Pages ------------------------------------------------------------------
    @app.route("/")
    async def index():
        store.ensure_loaded()
        rows = store.rows
        dates = store.dates
        available_states = store.states
        default_state = resolve_state(settings.default_state)
        state_summary = store.get_state_summary(default_state) or {}
        state_catalog = [
            {
                "code": state_code,
                **get_state_meta(state_code),
            }
            for state_code in available_states
        ]
        stats = {
            "total_zips": len(rows),
            "default_state": default_state,
            "default_state_zips": state_summary.get("zip_count", 0),
            "date_range": f"{dates[0]} → {dates[-1]}",
            "latest_date": dates[-1],
        }
        return await render_template(
            "index.html",
            stats=stats,
            state_catalog=state_catalog,
            state_catalog_json=json.dumps(state_catalog),
        )

    # APIs -------------------------------------------------------------------
    @app.route("/api/zips")
    async def api_zips():
        state = resolve_state(request.args.get("state", settings.default_state))
        city = request.args.get("city", "")
        q = request.args.get("q", "").lower()
        limit = min(int(request.args.get("limit", "500")), 2000)

        rows = store.get_zip_summaries_for_state(state)
        if city:
            city_q = city.lower()
            rows = [r for r in rows if city_q in (r["city"] or "").lower()]
        if q:
            rows = [r for r in rows if q in r["search_blob"]]
        for r in rows:
            r.pop("search_blob", None)
        return jsonify(rows[:limit])

    @app.route("/api/states")
    async def api_states():
        return jsonify(
            [
                {
                    "code": state_code,
                    **get_state_meta(state_code),
                }
                for state_code in store.states
            ]
        )

    @app.route("/api/summary")
    async def api_summary():
        state = resolve_state(request.args.get("state", settings.default_state))
        summary = store.get_state_summary(state)
        if not summary:
            abort(404)
        return jsonify(summary)

    # Chart endpoints --------------------------------------------------------
    @app.route("/chart/price-history")
    async def chart_price_history():
        state = resolve_state(request.args.get("state", settings.default_state))
        default_zip = (store.get_rows_for_state(state)[0]["zip"] if store.get_rows_for_state(state) else "")
        zips_param = request.args.get("zips", default_zip)
        zips = [z.strip() for z in zips_param.split(",") if z.strip()]
        return jsonify(charts.price_history(zips))

    @app.route("/chart/yoy-heatmap")
    async def chart_yoy_heatmap():
        state = resolve_state(request.args.get("state", settings.default_state))
        return jsonify(charts.yoy_heatmap(state))

    @app.route("/chart/price-distribution")
    async def chart_price_distribution():
        state = resolve_state(request.args.get("state", settings.default_state))
        return jsonify(charts.price_distribution(state))

    @app.route("/chart/top-movers")
    async def chart_top_movers():
        state = resolve_state(request.args.get("state", settings.default_state))
        mode = request.args.get("mode", "gain")  # gain | loss | yoy
        return jsonify(charts.top_movers(state, mode))

    @app.route("/chart/scatter-rank")
    async def chart_scatter_rank():
        state = resolve_state(request.args.get("state", settings.default_state))
        return jsonify(charts.scatter_rank(state))

    @app.route("/chart/metro-comparison")
    async def chart_metro_comparison():
        state = resolve_state(request.args.get("state", settings.default_state))
        return jsonify(charts.metro_comparison(state))

    @app.route("/chart/investment-matrix")
    async def chart_investment_matrix():
        state = resolve_state(request.args.get("state", settings.default_state))
        return jsonify(charts.investment_matrix(state))

    @app.route("/chart/zip-detail")
    async def chart_zip_detail():
        state = resolve_state(request.args.get("state", settings.default_state))
        default_zip = (store.get_rows_for_state(state)[0]["zip"] if store.get_rows_for_state(state) else "")
        zip_code = request.args.get("zip", default_zip)
        try:
            payload = charts.zip_detail(zip_code)
        except KeyError:
            abort(404)
        return jsonify(payload)
