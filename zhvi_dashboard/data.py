from __future__ import annotations

import statistics
from copy import deepcopy
from typing import Optional

import pandas as pd

from .settings import Settings
from .state_meta import STATE_META


class DataStore:
    """In-memory data cache for ZHVI rows grouped by state/zip."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._rows: Optional[list[dict]] = None
        self._dates: Optional[list[str]] = None
        self._rows_by_state: Optional[dict[str, list[dict]]] = None
        self._rows_by_zip: Optional[dict[str, dict]] = None
        self._state_zip_summaries: Optional[dict[str, list[dict]]] = None
        self._state_summaries: Optional[dict[str, dict]] = None
        self._states: Optional[list[str]] = None

    # Public API -----------------------------------------------------------------
    def get_rows_for_state(self, state: str) -> list[dict]:
        self._ensure_loaded()
        if not state:
            return self._rows or []
        return self._rows_by_state.get(state, []) if self._rows_by_state else []

    def get_row_for_zip(self, zip_code: str) -> Optional[dict]:
        self._ensure_loaded()
        if not self._rows_by_zip:
            return None
        return self._rows_by_zip.get(zip_code)

    def get_zip_summaries_for_state(self, state: str) -> list[dict]:
        self._ensure_loaded()
        if not state:
            all_rows: list[dict] = []
            for rows in (self._state_zip_summaries or {}).values():
                all_rows.extend(rows)
            return all_rows
        return deepcopy((self._state_zip_summaries or {}).get(state, []))

    def get_state_summary(self, state: str) -> Optional[dict]:
        self._ensure_loaded()
        if not self._state_summaries:
            return None
        return deepcopy(self._state_summaries.get(state))

    @property
    def states(self) -> list[str]:
        self._ensure_loaded()
        return self._states or []

    @property
    def dates(self) -> list[str]:
        self._ensure_loaded()
        return self._dates or []

    @property
    def rows(self) -> list[dict]:
        self._ensure_loaded()
        return self._rows or []

    def ensure_loaded(self) -> None:
        """Public hook to warm caches."""
        self._ensure_loaded()

    # Internal helpers -----------------------------------------------------------
    def _ensure_loaded(self) -> None:
        if self._rows is not None:
            return
        self._load_data()

    def _load_data(self) -> None:
        settings = self.settings
        if not settings.data_file.exists():
            raise FileNotFoundError(
                f"Could not find Zillow data file at {settings.data_file}. "
                "Download it with scripts/download-data.sh or set ZILLOW_CSV."
            )

        frame = pd.read_csv(
            settings.data_file,
            dtype={
                "RegionID": "string",
                "RegionName": "string",
                "RegionType": "string",
                "StateName": "string",
                "State": "string",
                "City": "string",
                "Metro": "string",
                "CountyName": "string",
            },
        )
        frame.columns = [str(col).strip() for col in frame.columns]
        date_cols = [col for col in frame.columns if col and col[0].isdigit()]
        frame["RegionName"] = frame["RegionName"].fillna("").str.strip().str.zfill(5)
        frame["State"] = frame["State"].fillna("").str.strip()
        frame["City"] = frame["City"].fillna("").str.strip()
        frame["Metro"] = frame["Metro"].fillna("").str.strip()
        frame["CountyName"] = frame["CountyName"].fillna("").str.strip()
        frame["SizeRank"] = pd.to_numeric(frame["SizeRank"], errors="coerce").fillna(0).astype(int)
        frame[date_cols] = frame[date_cols].apply(pd.to_numeric, errors="coerce")
        frame = frame[frame["State"] != ""].copy()
        frame = frame[frame["State"].isin(STATE_META)].copy()

        rows: list[dict] = []
        dates = date_cols
        for item in frame.to_dict(orient="records"):
            values = {d: (float(item[d]) if pd.notna(item[d]) else None) for d in date_cols}
            parsed = {
                "region_id": item["RegionID"] or "",
                "zip": item["RegionName"],
                "state": item["State"],
                "city": item["City"],
                "metro": item["Metro"],
                "county": item["CountyName"],
                "size_rank": int(item["SizeRank"]),
                "values": values,
            }
            parsed["search_blob"] = " ".join(
                part.lower()
                for part in (parsed["zip"], parsed["city"], parsed["state"], parsed["county"], parsed["metro"])
                if part
            )

            valid = [v for v in values.values() if v is not None]
            if valid:
                parsed["latest"] = valid[-1]
                parsed["earliest"] = valid[0]
                parsed["change_pct"] = ((valid[-1] - valid[0]) / valid[0] * 100) if valid[0] else 0
                parsed["peak"] = max(valid)
                parsed["trough"] = min(valid)
                parsed["yoy_pct"] = (
                    (valid[-1] - valid[-13]) / valid[-13] * 100 if len(valid) >= 13 and valid[-13] else 0
                )
            else:
                parsed["latest"] = None
                parsed["earliest"] = None
                parsed["change_pct"] = 0
                parsed["peak"] = None
                parsed["trough"] = None
                parsed["yoy_pct"] = 0

            rows.append(parsed)

        rows_by_state: dict[str, list[dict]] = {}
        rows_by_zip: dict[str, dict] = {}
        for row in rows:
            rows_by_state.setdefault(row["state"], []).append(row)
            rows_by_zip[row["zip"]] = row

        state_zip_summaries: dict[str, list[dict]] = {}
        state_summaries: dict[str, dict] = {}
        for state, state_rows in rows_by_state.items():
            ranked_rows = sorted(
                [r for r in state_rows if r["latest"] is not None],
                key=lambda item: item["latest"],
                reverse=True,
            )
            rows_by_state[state] = ranked_rows

            summaries: list[dict] = []
            for r in ranked_rows:
                summaries.append(
                    {
                        "zip": r["zip"],
                        "city": r["city"],
                        "state": r["state"],
                        "county": r["county"],
                        "metro": r["metro"],
                        "latest": r["latest"],
                        "change_pct": round(r["change_pct"], 1),
                        "yoy_pct": round(r["yoy_pct"], 1),
                        "peak": r["peak"],
                        "search_blob": r["search_blob"],
                    }
                )
            state_zip_summaries[state] = summaries

            if summaries:
                latest_values = [r["latest"] for r in ranked_rows if r["latest"] is not None]
                yoy_values = [r["yoy_pct"] for r in ranked_rows]
                change_values = [r["change_pct"] for r in ranked_rows]
                county_groups: dict[str, list[float]] = {}
                for r in ranked_rows:
                    county_groups.setdefault(r["county"], []).append(r["latest"])
                county_highlights = sorted(
                    (
                        {
                            "county": county,
                            "median_value": round(statistics.median(vals)),
                        }
                        for county, vals in county_groups.items()
                        if vals
                    ),
                    key=lambda item: item["median_value"],
                    reverse=True,
                )[:3]

                state_summaries[state] = {
                    "state": state,
                    "zip_count": len(ranked_rows),
                    "latest_date": dates[-1],
                    "median_value": round(statistics.median(latest_values)),
                    "average_yoy": round(statistics.mean(yoy_values), 1),
                    "average_change": round(statistics.mean(change_values), 1),
                    "highest_value_zip": {
                        "zip": ranked_rows[0]["zip"],
                        "city": ranked_rows[0]["city"],
                        "latest": ranked_rows[0]["latest"],
                    },
                    "lowest_value_zip": {
                        "zip": ranked_rows[-1]["zip"],
                        "city": ranked_rows[-1]["city"],
                        "latest": ranked_rows[-1]["latest"],
                    },
                    "top_gainer": {
                        "zip": max(ranked_rows, key=lambda item: item["change_pct"])["zip"],
                        "city": max(ranked_rows, key=lambda item: item["change_pct"])["city"],
                        "change_pct": round(max(ranked_rows, key=lambda item: item["change_pct"])["change_pct"], 1),
                    },
                    "strongest_yoy": {
                        "zip": max(ranked_rows, key=lambda item: item["yoy_pct"])["zip"],
                        "city": max(ranked_rows, key=lambda item: item["yoy_pct"])["city"],
                        "yoy_pct": round(max(ranked_rows, key=lambda item: item["yoy_pct"])["yoy_pct"], 1),
                    },
                    "softest_yoy": {
                        "zip": min(ranked_rows, key=lambda item: item["yoy_pct"])["zip"],
                        "city": min(ranked_rows, key=lambda item: item["yoy_pct"])["city"],
                        "yoy_pct": round(min(ranked_rows, key=lambda item: item["yoy_pct"])["yoy_pct"], 1),
                    },
                    "county_highlights": county_highlights,
                }

        self._rows = rows
        self._dates = dates
        self._rows_by_state = rows_by_state
        self._rows_by_zip = rows_by_zip
        self._state_zip_summaries = state_zip_summaries
        self._state_summaries = state_summaries
        self._states = sorted(state for state in rows_by_state if state)
        print(f"[data] Loaded {len(rows)} zip codes, {len(dates)} time points")  # noqa: T201
