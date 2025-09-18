from __future__ import annotations

import duckdb
import pandas as pd
import streamlit as st
from duckdb import DuckDBPyConnection

from ironclad.analytics.data_quality import check_freshness, check_quorum
from ironclad.settings import settings

st.title("Snapshots")

col1, col2 = st.columns(2)
season = col1.number_input("Season", min_value=2018, max_value=2035, value=2025, step=1)
week = col2.number_input("Week", min_value=1, max_value=23, value=1, step=1)

DUCK_PATH = settings.duckdb_path
_connection: DuckDBPyConnection | None = None
try:
    _connection = duckdb.connect(DUCK_PATH, read_only=True)
except Exception as exc:  # pragma: no cover - streamlit surface
    st.error(f"Unable to connect to DuckDB: {exc}", icon="🚫")

source: DuckDBPyConnection | str = _connection if _connection is not None else DUCK_PATH

with st.container():
    freshness = check_freshness(source, int(season), int(week), max_age_minutes=180)
    quorum = check_quorum(source, int(season), int(week), min_odds_rows=10)

    cols = st.columns(3)

    def _chip(ok: bool, label: str, detail: str) -> None:
        if ok:
            cols[0].success(label)
        else:
            cols[0].error(label)
        cols[1].caption(detail)

    _chip(
        freshness.get("odds_snapshots", {}).get("ok", False),
        "Odds fresh",
        f"{freshness.get('odds_snapshots', {}).get('age_min', '?')} min old",
    )

    _chip(
        freshness.get("injury_snapshots", {}).get("ok", False),
        "Injuries fresh",
        f"{freshness.get('injury_snapshots', {}).get('age_min', '?')} min old",
    )

    _chip(
        freshness.get("weather_snapshots", {}).get("ok", False),
        "Weather fresh",
        f"{freshness.get('weather_snapshots', {}).get('age_min', '?')} min old",
    )

    cols[2].markdown(
        ("✅ **Quorum OK**" if quorum.get("ok") else "❌ **Quorum FAIL**")
        + f" — odds rows: {quorum.get('odds_rows', 0)}"
    )


def _load_table(
    con: DuckDBPyConnection | None, table: str, season_val: int, week_val: int
) -> pd.DataFrame | None:
    if con is None:
        return None
    try:
        return con.execute(
            f"SELECT * FROM {table} WHERE season=? AND week=? ORDER BY ts_utc DESC",
            [season_val, week_val],
        ).df()
    except duckdb.CatalogException:
        return None


tabs = st.tabs(["Odds", "Injuries", "Weather"])
for tab, table in zip(tabs, ["odds_snapshots", "injury_snapshots", "weather_snapshots"]):
    with tab:
        df = _load_table(_connection, table, int(season), int(week))
        if df is None or df.empty:
            st.info("No data found for the selected filters.")
        else:
            st.dataframe(df, use_container_width=True)

if _connection is not None:
    _connection.close()
