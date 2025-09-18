import duckdb
import pandas as pd
import streamlit as st

from ironclad.analytics.guardrails import caps_from_settings, check_exposure
from ironclad.settings import get_settings

st.set_page_config(page_title="Exposure Guardrails", layout="wide")

settings = get_settings()
DUCK = settings.DUCKDB__PATH

st.title("Exposure Guardrails")
col1, col2, col3 = st.columns(3)
season = col1.number_input("Season", min_value=2018, max_value=2035, value=2025, step=1)
week = col2.number_input("Week", min_value=1, max_value=23, value=1, step=1)
sized = col3.toggle("Use sized stakes", value=True)

caps = caps_from_settings()
st.caption(
    f"Caps — Total:{caps.max_total_u}  Team:{caps.max_team_u}  Market:{caps.max_market_u}  "
    f"Game:{caps.max_game_u}  MinPicks:{caps.require_min_picks}"
)

ok, violations = check_exposure(DUCK, int(season), int(week), caps, sized=sized)
if not ok:
    st.error(f"Guardrails violated: {len(violations)} issue(s).")
    with st.expander("View violations JSON"):
        st.json(violations)
else:
    st.success("Guardrails OK.")

df = pd.DataFrame()
try:
    with duckdb.connect(DUCK, read_only=True) as con:
        table = "picks_sized" if sized else "picks"
        df = con.execute(
            "SELECT * FROM {table} WHERE season = ? AND week = ?".format(table=table),
            [int(season), int(week)],
        ).df()
except duckdb.Error as exc:  # pragma: no cover - defensive UI guard
    st.warning(f"Unable to query {DUCK}: {exc}")

st.subheader("Board Snapshot")
if df.empty:
    st.info("No picks found for the selected slate.")
else:
    st.dataframe(df, use_container_width=True)
