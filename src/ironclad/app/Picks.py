import streamlit as st, pandas as pd
from ..settings import settings
from ..services.odds_client import OddsClient
from ..services.base import ServiceState
from ..runner.run_board import synthesize_picks
from datetime import datetime

st.set_page_config(page_title="Ironclad Picks (Phase 1)", layout="wide")
st.title("Ironclad — Picks (Phase 1 Foundation)")
col1, col2, col3 = st.columns(3)
season = col1.number_input("Season", min_value=2018, max_value=2030, value=2025, step=1)
week = col2.number_input("Week", min_value=1, max_value=23, value=1, step=1)
profile = col3.selectbox(
    "Profile",
    options=["local", "qa", "prod"],
    index=["local", "qa", "prod"].index(settings.profile),
)

if settings.demo_enabled():
    st.info("Demo mode enabled — synthetic board will be used when services are missing.", icon="ℹ️")

client = OddsClient()
if client.state != ServiceState.AVAILABLE and not settings.demo_enabled():
    st.error("Odds service unavailable — check API keys. Enable demo to proceed.", icon="🚫")

if st.button("Run"):
    run_id = f"ui-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    picks = synthesize_picks(run_id, int(season), int(week))
    if not picks:
        st.warning("No picks produced.", icon="⚠️")
    else:
        df = pd.DataFrame([p.model_dump() for p in picks])
        st.dataframe(df, use_container_width=True)
