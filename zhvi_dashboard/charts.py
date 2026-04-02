from __future__ import annotations

import json
import statistics
from typing import Iterable, List

import plotly.graph_objects as go
import plotly.utils
from plotly.subplots import make_subplots

from .data import DataStore
from .settings import Settings


THEME = dict(
    bg="#0a0d14",
    surface="#111520",
    surface2="#161c2d",
    accent="#e8c87d",
    accent2="#5b9bd5",
    accent3="#8ecfb0",
    text="#e8e8f0",
    subtext="#8890a8",
    grid="#1e2535",
)

LAYOUT_BASE = dict(
    paper_bgcolor=THEME["bg"],
    plot_bgcolor=THEME["surface"],
    font=dict(family="'DM Mono', 'Courier New', monospace", color=THEME["text"], size=12),
    margin=dict(l=60, r=30, t=50, b=50),
    hoverlabel=dict(
        bgcolor=THEME["surface2"],
        bordercolor=THEME["accent"],
        font=dict(family="'DM Mono', monospace", color=THEME["text"], size=12),
    ),
)


def plotly_json(fig: go.Figure) -> str:
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def _layout(**overrides):
    d = dict(**LAYOUT_BASE)
    d.update(overrides)
    return d


class ChartService:
    """Pure chart-building helpers, fed by the DataStore."""

    def __init__(self, store: DataStore, settings: Settings):
        self.store = store
        self.settings = settings

    # Public chart builders -----------------------------------------------------
    def price_history(self, zips: Iterable[str]) -> dict:
        dates = self.store.dates
        fig = go.Figure()

        colors = [
            THEME["accent"],
            THEME["accent2"],
            THEME["accent3"],
            "#e07b7b",
            "#b07dd6",
            "#f0a05a",
            "#6cc8e0",
        ]

        for i, z in enumerate(list(zips)[:7]):
            row = self.store.get_row_for_zip(z)
            if not row:
                continue
            vals = [row["values"].get(d) for d in dates]
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=vals,
                    mode="lines",
                    name=f"{z} — {row['city']}",
                    line=dict(color=color, width=2.5),
                    hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
                )
            )

        fig.update_layout(
            **_layout(
                title=dict(
                    text="Home Value History by ZIP",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                xaxis=dict(showgrid=True, gridcolor=THEME["grid"], tickangle=-30, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor=THEME["grid"], tickformat="$,.0f"),
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=THEME["grid"], font=dict(size=11)),
                hovermode="x unified",
            )
        )
        return {"chart": plotly_json(fig)}

    def yoy_heatmap(self, state: str) -> dict:
        dates = self.store.dates
        subset = self.store.get_rows_for_state(state)[:40]
        year_dates = [d for d in dates if d.endswith("-12-31")]

        zip_labels = [f"{r['zip']} {r['city'][:12]}" for r in subset]
        matrix: List[List[float | None]] = []
        for r in subset:
            row_vals: list[float | None] = []
            prev = None
            for d in year_dates:
                v = r["values"].get(d)
                if v and prev:
                    row_vals.append(round((v - prev) / prev * 100, 1))
                else:
                    row_vals.append(None)
                prev = v
            matrix.append(row_vals)

        years = [d[:4] for d in year_dates]

        fig = go.Figure(
            go.Heatmap(
                z=matrix,
                x=years,
                y=zip_labels,
                colorscale=[
                    [0.0, "#8b1a1a"],
                    [0.25, "#c0392b"],
                    [0.45, THEME["surface2"]],
                    [0.55, THEME["surface2"]],
                    [0.75, "#2e7d5c"],
                    [1.0, "#1a5e3e"],
                ],
                zmid=0,
                text=[[f"{v:.1f}%" if v is not None else "" for v in row] for row in matrix],
                texttemplate="%{text}",
                textfont=dict(size=8),
                hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}%<extra></extra>",
                colorbar=dict(
                    title=dict(text="YoY %", font=dict(color=THEME["subtext"])),
                    tickfont=dict(color=THEME["subtext"]),
                    outlinecolor=THEME["grid"],
                ),
            )
        )

        fig.update_layout(
            **_layout(
                title=dict(
                    text=f"Year-over-Year Price Change — {state}",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                xaxis=dict(showgrid=False, tickfont=dict(size=11)),
                yaxis=dict(showgrid=False, tickfont=dict(size=10), autorange="reversed"),
                height=max(400, len(subset) * 20 + 100),
            )
        )
        return {"chart": plotly_json(fig)}

    def price_distribution(self, state: str) -> dict:
        dates = self.store.dates
        subset = self.store.get_rows_for_state(state)
        latest_date = dates[-1]

        counties: dict[str, list[float | None]] = {}
        for r in subset:
            counties.setdefault(r["county"], []).append(r["latest"])

        county_items = sorted(counties.items(), key=lambda x: statistics.median(x[1]))

        plasma = [
            "#0d0887",
            "#3d049b",
            "#6300a7",
            "#8707a6",
            "#a62098",
            "#c03a83",
            "#d5556f",
            "#e57357",
            "#f89540",
            "#fdb92a",
            "#f0f921",
        ]

        fig = go.Figure()
        for i, (county, vals) in enumerate(county_items):
            t = i / max(len(county_items) - 1, 1)
            color = plasma[int(t * (len(plasma) - 1))]
            fig.add_trace(
                go.Box(
                    y=vals,
                    name=county.replace(" County", ""),
                    marker_color=color,
                    line_color=color,
                    fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.33)",
                    boxmean="sd",
                    hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
                )
            )

        fig.update_layout(
            **_layout(
                title=dict(
                    text=f"Home Value Distribution by County — {state} ({latest_date})",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor=THEME["grid"], tickformat="$,.0f"),
                showlegend=False,
                height=480,
            )
        )
        return {"chart": plotly_json(fig)}

    def top_movers(self, state: str, mode: str) -> dict:
        subset = list(self.store.get_rows_for_state(state))

        if mode == "yoy":
            subset.sort(key=lambda x: x["yoy_pct"], reverse=True)
            top = subset[:20]
            key = "yoy_pct"
            title_suffix = "YoY %"
        elif mode == "loss":
            subset.sort(key=lambda x: x["change_pct"])
            top = subset[:20]
            key = "change_pct"
            title_suffix = "All-time % (lowest)"
        else:
            subset.sort(key=lambda x: x["change_pct"], reverse=True)
            top = subset[:20]
            key = "change_pct"
            title_suffix = "All-time %"

        labels = [f"{r['zip']}<br>{r['city'][:14]}" for r in top]
        values = [r[key] for r in top]
        bar_colors = [THEME["accent3"] if v >= 0 else "#c0392b" for v in values]

        fig = go.Figure(
            go.Bar(
                x=labels,
                y=values,
                marker_color=bar_colors,
                text=[f"{v:+.1f}%" for v in values],
                customdata=[f"{v:+.1f}%" for v in values],
                textposition="outside",
                textfont=dict(size=10, color=THEME["text"]),
                hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>",
            )
        )

        fig.update_layout(
            **_layout(
                title=dict(
                    text=f"Top Movers — {title_suffix} — {state}",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                xaxis=dict(showgrid=False, tickfont=dict(size=9)),
                yaxis=dict(showgrid=True, gridcolor=THEME["grid"], ticksuffix="%"),
                height=440,
            )
        )
        return {"chart": plotly_json(fig)}

    def scatter_rank(self, state: str) -> dict:
        subset = self.store.get_rows_for_state(state)

        fig = go.Figure(
            go.Scatter(
                x=[r["size_rank"] for r in subset],
                y=[r["latest"] for r in subset],
                mode="markers",
                marker=dict(
                    color=[r["yoy_pct"] for r in subset],
                    colorscale="RdYlGn",
                    cmid=0,
                    size=9,
                    opacity=0.85,
                    colorbar=dict(
                        title=dict(text="YoY %", font=dict(color=THEME["subtext"])),
                        tickfont=dict(color=THEME["subtext"]),
                        outlinecolor=THEME["grid"],
                    ),
                    line=dict(width=0.5, color=THEME["surface"]),
                ),
                text=[f"{r['zip']} {r['city']}" for r in subset],
                hovertemplate="<b>%{text}</b><br>Rank: %{x}<br>Value: $%{y:,.0f}<br>YoY: %{marker.color:.1f}%<extra></extra>",
            )
        )

        fig.update_layout(
            **_layout(
                title=dict(
                    text=f"Market Size Rank vs Home Value — {state}",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                xaxis=dict(
                    title="Size Rank (lower = larger market)",
                    showgrid=True,
                    gridcolor=THEME["grid"],
                    tickfont=dict(size=10),
                ),
                yaxis=dict(title="Current Value", showgrid=True, gridcolor=THEME["grid"], tickformat="$,.0f"),
                height=460,
            )
        )
        return {"chart": plotly_json(fig)}

    def metro_comparison(self, state: str) -> dict:
        dates = self.store.dates
        subset = self.store.get_rows_for_state(state)

        metros: dict[str, list[dict]] = {}
        for r in subset:
            m = (r["metro"] or "Unknown")[:40]
            metros.setdefault(m, []).append(r)

        top_metros = sorted(
            metros.items(),
            key=lambda kv: statistics.median(x["latest"] for x in kv[1]),
            reverse=True,
        )[:8]

        colors = [
            THEME["accent"],
            THEME["accent2"],
            THEME["accent3"],
            "#e07b7b",
            "#b07dd6",
            "#f0a05a",
            "#6cc8e0",
            "#d4b896",
        ]

        fig = go.Figure()
        for i, (metro, metro_rows) in enumerate(top_metros):
            avg_vals = []
            for d in dates:
                dvals = [r["values"].get(d) for r in metro_rows if r["values"].get(d) is not None]
                avg_vals.append(statistics.mean(dvals) if dvals else None)

            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=avg_vals,
                    mode="lines",
                    name=metro.split(",")[0],
                    line=dict(color=color, width=2),
                    hovertemplate="<b>%{fullData.name}</b><br>%{x}<br>$%{y:,.0f}<extra></extra>",
                )
            )

        fig.update_layout(
            **_layout(
                title=dict(
                    text=f"Metro Area Average Home Values — {state}",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                xaxis=dict(showgrid=True, gridcolor=THEME["grid"], tickangle=-30, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor=THEME["grid"], tickformat="$,.0f"),
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=THEME["grid"], font=dict(size=10)),
                hovermode="x unified",
                height=460,
            )
        )
        return {"chart": plotly_json(fig)}

    def investment_matrix(self, state: str) -> dict:
        subset = [r for r in self.store.get_rows_for_state(state) if r["change_pct"] != 0]
        med_val = statistics.median(r["latest"] for r in subset)
        med_chg = statistics.median(r["change_pct"] for r in subset)

        fig = go.Figure()
        fig.add_hline(y=med_chg, line=dict(color=THEME["grid"], width=1, dash="dot"))
        fig.add_vline(x=med_val, line=dict(color=THEME["grid"], width=1, dash="dot"))

        for label, x, y, anchor in [
            ("High Value<br>High Growth", med_val * 1.6, med_chg * 1.6, "left"),
            ("Low Value<br>High Growth", med_val * 0.3, med_chg * 1.6, "left"),
            ("High Value<br>Low Growth", med_val * 1.6, med_chg * 0.3, "left"),
            ("Low Value<br>Low Growth", med_val * 0.3, med_chg * 0.3, "left"),
        ]:
            fig.add_annotation(
                x=x,
                y=y,
                text=label,
                showarrow=False,
                font=dict(size=9, color=THEME["subtext"]),
                align="center",
            )

        fig.add_trace(
            go.Scatter(
                x=[r["latest"] for r in subset],
                y=[r["change_pct"] for r in subset],
                mode="markers",
                customdata=[f"{r['change_pct']:+.1f}%" for r in subset],
                marker=dict(
                    color=[r["yoy_pct"] for r in subset],
                    colorscale="Viridis",
                    size=9,
                    opacity=0.8,
                    colorbar=dict(
                        title=dict(text="YoY %", font=dict(color=THEME["subtext"])),
                        tickfont=dict(color=THEME["subtext"]),
                        outlinecolor=THEME["grid"],
                    ),
                    line=dict(width=0.5, color=THEME["surface"]),
                ),
                text=[f"{r['zip']} {r['city']}" for r in subset],
                hovertemplate="<b>%{text}</b><br>Value: $%{x:,.0f}<br>All-time: %{customdata}<extra></extra>",
            )
        )

        fig.update_layout(
            **_layout(
                title=dict(
                    text=f"Investment Matrix: Value vs Appreciation — {state}",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                xaxis=dict(
                    title="Current Home Value ($)",
                    showgrid=True,
                    gridcolor=THEME["grid"],
                    tickformat="$,.0f",
                    tickfont=dict(size=10),
                ),
                yaxis=dict(
                    title="All-time % Change",
                    showgrid=True,
                    gridcolor=THEME["grid"],
                    ticksuffix="%",
                ),
                height=480,
            )
        )
        return {"chart": plotly_json(fig)}

    def zip_detail(self, zip_code: str) -> dict:
        dates = self.store.dates
        row = self.store.get_row_for_zip(zip_code)
        if not row:
            raise KeyError("ZIP not found")

        vals = [row["values"].get(d) for d in dates]
        valid_pairs = [(d, v) for d, v in zip(dates, vals) if v is not None]
        vdates, vvals = zip(*valid_pairs) if valid_pairs else ([], [])

        yoy_dates: list[str] = []
        yoy_vals: list[float] = []
        for i in range(12, len(vvals)):
            if vvals[i - 12]:
                yoy_dates.append(vdates[i])
                yoy_vals.append((vvals[i] - vvals[i - 12]) / vvals[i - 12] * 100)

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=["Home Value History", "Year-over-Year Change %", "Monthly Δ ($)", "Rolling 12-mo Trend"],
            vertical_spacing=0.14,
            horizontal_spacing=0.1,
        )

        fig.add_trace(
            go.Scatter(
                x=vdates,
                y=vvals,
                mode="lines",
                name="Value",
                line=dict(color=THEME["accent"], width=2.5),
                fill="tozeroy",
                fillcolor="rgba(232,200,125,0.08)",
                hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        bar_colors_yoy = [THEME["accent3"] if v >= 0 else "#c0392b" for v in yoy_vals]
        fig.add_trace(
            go.Bar(
                x=yoy_dates,
                y=yoy_vals,
                marker_color=bar_colors_yoy,
                name="YoY %",
                customdata=[f"{v:+.2f}%" for v in yoy_vals],
                hovertemplate="%{x}<br>%{customdata}<extra></extra>",
            ),
            row=1,
            col=2,
        )

        monthly_deltas = [vvals[i] - vvals[i - 1] for i in range(1, len(vvals))]
        delta_colors = [THEME["accent2"] if v >= 0 else "#c0392b" for v in monthly_deltas]
        fig.add_trace(
            go.Bar(
                x=vdates[1:],
                y=monthly_deltas,
                marker_color=delta_colors,
                name="Monthly Δ",
                customdata=[f"{v:+,.0f}" for v in monthly_deltas],
                hovertemplate="%{x}<br>%{customdata}<extra></extra>",
            ),
            row=2,
            col=1,
        )

        rolling: list[float] = []
        for i in range(len(vvals)):
            window = vvals[max(0, i - 11) : i + 1]
            rolling.append(sum(window) / len(window))
        fig.add_trace(
            go.Scatter(
                x=vdates,
                y=vvals,
                mode="lines",
                name="Actual",
                line=dict(color=THEME["subtext"], width=1, dash="dot"),
                hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
            ),
            row=2,
            col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=vdates,
                y=rolling,
                mode="lines",
                name="12-mo MA",
                line=dict(color=THEME["accent"], width=2.5),
                hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            **_layout(
                title=dict(
                    text=f"ZIP {zip_code} — {row['city']}, {row['state']} | {row['county']}",
                    font=dict(size=16, color=THEME["accent"]),
                    x=0.02,
                ),
                height=620,
                showlegend=False,
            )
        )

        for i in range(1, 5):
            row_n = (i - 1) // 2 + 1
            col_n = (i - 1) % 2 + 1
            fig.update_xaxes(
                showgrid=True,
                gridcolor=THEME["grid"],
                tickangle=-30,
                tickfont=dict(size=9),
                row=row_n,
                col=col_n,
            )
            fig.update_yaxes(showgrid=True, gridcolor=THEME["grid"], tickfont=dict(size=9), row=row_n, col=col_n)

        fig.update_annotations(font=dict(color=THEME["subtext"], size=11))

        meta = {
            "zip": zip_code,
            "city": row["city"],
            "state": row["state"],
            "county": row["county"],
            "metro": row["metro"],
            "latest": row["latest"],
            "change_pct": round(row["change_pct"], 2),
            "yoy_pct": round(row["yoy_pct"], 2),
            "peak": row["peak"],
            "trough": row["trough"],
        }
        return {"chart": plotly_json(fig), "meta": meta}

