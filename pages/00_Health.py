import os
import subprocess

import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ironclad — Health", layout="wide")
st.title("Ironclad — Health / Smoke")

profile = st.selectbox("Profile", ["prod", "qa", "replay"], index=0)
season = st.text_input("Season (optional)", value="")
week = st.text_input("Week (optional)", value="")
slack = st.text_input("Slack webhook (optional)", type="password")

if st.button("Run smoke now"):
    env = os.environ.copy()
    env["PROFILE"] = profile
    if season:
        env["SEASON"] = season
    if week:
        env["WEEK"] = week
    if slack:
        env["SLACK_WEBHOOK"] = slack
    code = subprocess.call(["python", "scripts/smoke/post_promo_smoke.py"], env=env)
    st.write(f"Smoke finished with exit code {code} (see out/reports/ for artifacts)")

query = (
    "SELECT run_id, season, week, profile, started_at FROM runs ORDER BY started_at DESC "
    "NULLS LAST LIMIT 10"
)
df = pd.DataFrame()
try:
    with duckdb.connect("out/ironclad.duckdb", read_only=True) as con:
        df = con.execute(query).df()
except Exception as exc:  # pragma: no cover - UI helper
    st.warning(f"Could not load recent runs: {exc}")

st.subheader("Recent runs")
st.dataframe(df, use_container_width=True, hide_index=True)
