import streamlit as st
import pandas as pd
from ironclad.analytics import exposure_queries as q

st.set_page_config(page_title="Ironclad — Exposure", layout="wide")
st.title("Ironclad — Exposure")

DUCK = "out/ironclad.duckdb"

# Season/Week selectors
sw = q.seasons_weeks(DUCK)
if sw.empty:
    st.info("No data yet. Run: `make preslate-size` first.")
    st.stop()

c1, c2, c3 = st.columns([2,2,2])
with c1:
    seasons = sorted(sw["season"].dropna().unique(), reverse=True)
    season = st.selectbox("Season", seasons, index=0)
with c2:
    weeks = sorted(sw.query("season == @season")["week"].dropna().unique(), reverse=True)
    week = st.selectbox("Week", weeks, index=0)
with c3:
    sized = st.toggle("Use sized stakes", value=True)

board = q.board(DUCK, season=int(season), week=int(week), sized=sized)
if board.empty:
    st.warning("No rows for this (season,week).")
    st.stop()

# KPIs
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Picks", len(board))
with c2:
    st.metric("Total Units", f"{board['stake_units'].sum():.2f}")
with c3:
    st.metric("Avg Units", f"{(board['stake_units'].mean() if len(board)>0 else 0):.2f}")
with c4:
    st.metric("Distinct Games", board["game_id"].nunique())

# Exposure tables
left, right = st.columns(2)
with left:
    st.subheader("By Team")
    exp_team = q.exposure_by_team(DUCK, season, week, sized)
    st.dataframe(exp_team, hide_index=True, use_container_width=True)
with right:
    st.subheader("By Market")
    exp_mkt = q.exposure_by_market(DUCK, season, week, sized)
    st.dataframe(exp_mkt, hide_index=True, use_container_width=True)

st.subheader("By Book")
st.dataframe(q.exposure_by_book(DUCK, season, week, sized), hide_index=True, use_container_width=True)

# Top picks
st.subheader("Top Positions")
st.dataframe(q.top_picks(DUCK, season, week, sized, k=30), hide_index=True, use_container_width=True)

# Download
st.download_button(
    "Download board (CSV)",
    data=board.to_csv(index=False).encode("utf-8"),
    file_name=f"ironclad_board_{season}_W{week}{'_sized' if sized else ''}.csv",
    mime="text/csv",
)
