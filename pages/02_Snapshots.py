from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from ironclad.settings import get_settings

st.set_page_config(page_title="Snapshots", layout="wide")
st.title("Snapshot Browser")

settings = get_settings()
db_path = Path(settings.duckdb_path)
st.caption(f"DuckDB database: {db_path}")

con: duckdb.DuckDBPyConnection | None = None
if db_path.exists():
    try:
        con = duckdb.connect(str(db_path), read_only=True)
    except duckdb.Error as exc:  # pragma: no cover - UI only
        st.error(f"Could not connect to DuckDB: {exc}")
else:
    st.info("No DuckDB database found yet. Run a board to create one.")

snapshots_dir = Path("out/snapshots")
if snapshots_dir.exists():
    run_dirs = sorted([p.name for p in snapshots_dir.iterdir() if p.is_dir()], reverse=True)
    if run_dirs:
        st.subheader("Available snapshot directories")
        st.write(run_dirs)
    else:
        st.caption("Snapshot directory is empty.")
else:
    st.caption("Snapshot output directory not created yet.")

st.divider()
st.subheader("Re-run with these snapshots")

runs_df = pd.DataFrame()
if con is not None:
    try:
        runs_df = con.execute(
            "SELECT run_id, season, week, started_at FROM runs ORDER BY started_at DESC NULLS LAST LIMIT 20"
        ).df()
    except duckdb.Error:
        runs_df = pd.DataFrame()
    finally:
        con.close()

if runs_df.empty:
    st.caption("No runs recorded yet.")
else:
    rid = st.selectbox(
        "Pick a run_id to replay",
        runs_df["run_id"].tolist(),
        format_func=lambda x: f"{x}",
    )
    rrow = runs_df[runs_df["run_id"] == rid].iloc[0]
    cmd = f'RUN_ID={rid} SEASON={int(rrow["season"])} WEEK={int(rrow["week"])} make replay-by-run'
    st.code(cmd, language="bash")
    if st.button("Copy command to clipboard"):
        st.write("Use your terminal to run the command above so it inherits your venv.")
