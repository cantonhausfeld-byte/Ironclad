
"""Streamlit dashboard for Ironclad picks."""

from __future__ import annotations

import glob
import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ironclad Picks", layout="wide")
st.title("Ironclad — Picks")

DB_PATH = Path("out/ironclad.duckdb")
PICKS_DIR = Path("out/picks")
REQUIRED_COLUMNS = [
    "stake_units",
    "grade",
    "market",
    "side",
    "price_american",
    "model_prob",
    "ev_percent",
    "game_id",
    "book",
    "line",
]


def _latest(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def _load_latest_df() -> pd.DataFrame:
    sized = _latest(str(PICKS_DIR / "*_picks_sized.csv"))
    base = _latest(str(PICKS_DIR / "*_picks.csv"))
    if sized:
        df = pd.read_csv(sized)
        df["__source"] = os.path.basename(sized)
        st.caption(f"Loaded sized picks: `{os.path.basename(sized)}`")
        return df
    if base:
        df = pd.read_csv(base)
        df["__source"] = os.path.basename(base)
        st.caption(f"Loaded base picks: `{os.path.basename(base)}` (no sized stakes yet)")
        return df
    return pd.DataFrame()


df = _load_latest_df()
if df.empty:
    st.info("No picks yet. Run: `make preslate` (and `make size` for stakes).")
    st.stop()

for column in REQUIRED_COLUMNS:
    if column not in df.columns:
        df[column] = None

cols = st.columns(3)
grade_options = sorted(df["grade"].dropna().unique())
market_options = sorted(df["market"].dropna().unique())
with cols[0]:
    gsel = st.multiselect("Grade filter", options=grade_options, default=list(grade_options))
with cols[1]:
    msel = st.multiselect("Market filter", options=market_options, default=list(market_options))
with cols[2]:
    min_stake = st.number_input("Min stake (u)", value=0.0, min_value=0.0, step=0.5)

mask = (
    df["grade"].isin(gsel)
    & df["market"].isin(msel)
    & (df["stake_units"].fillna(0) >= min_stake)
)
view = df[mask].copy()

st.subheader("Board")
display_cols = [
    "game_id",
    "market",
    "side",
    "line",
    "price_american",
    "model_prob",
    "ev_percent",
    "grade",
    "stake_units",
    "book",
    "__source",
]
st.dataframe(view[display_cols], use_container_width=True, hide_index=True)

st.subheader("Exposure")
view["team_key"] = view["side"].astype(str).str.split(":").str[0]
view.loc[:, "stake_units"] = view["stake_units"].fillna(0.0)
stake_units = view["stake_units"]
exp_by_team = (
    view.groupby("team_key", dropna=False)["stake_units"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
exp_by_mkt = (
    view.groupby("market")["stake_units"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
c1, c2, c3 = st.columns(3)
total_units = float(stake_units.sum())
avg_units = float(stake_units.mean()) if not view.empty else 0.0
with c1:
    st.metric("Total Units", f"{total_units:.2f}")
with c2:
    st.metric("Avg Units / Pick", f"{avg_units:.2f}")
with c3:
    st.metric("# Picks", f"{len(view)}")
st.write("**By Team**")
st.dataframe(exp_by_team, hide_index=True, use_container_width=True)
st.write("**By Market**")
st.dataframe(exp_by_mkt, hide_index=True, use_container_width=True)

csv_bytes = view.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered CSV",
    data=csv_bytes,
    file_name="ironclad_picks_filtered.csv",
    mime="text/csv",
)

try:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    cnt = con.execute("select count(*) from picks").fetchone()[0]
    st.caption(f"DuckDB rows in picks: {cnt}")
except Exception as exc:  # pragma: no cover - optional display
    st.caption(f"DuckDB not available: {exc}")
