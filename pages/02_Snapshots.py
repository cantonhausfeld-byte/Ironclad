import streamlit as st, duckdb, pandas as pd, os

st.set_page_config(page_title="Ironclad — Snapshots", layout="wide")
st.title("Ironclad — Snapshots")

DUCK = "out/ironclad.duckdb"

try:
    con = duckdb.connect(DUCK, read_only=True)
except Exception as e:
    st.error(f"Could not open DuckDB: {e}")
    st.stop()

# Season/week selectors from snapshots if available; else fallback to picks
def seasons_weeks():
    q = """
    WITH base AS (
      SELECT season, week FROM odds_snapshots
      UNION ALL SELECT season, week FROM injury_snapshots
      UNION ALL SELECT season, week FROM weather_snapshots
      UNION ALL SELECT season, week FROM picks
    )
    SELECT season, week
    FROM base
    WHERE season IS NOT NULL AND week IS NOT NULL
    GROUP BY season, week
    ORDER BY season DESC, week DESC
    """
    return con.execute(q).df()

sw = seasons_weeks()
if sw.empty:
    st.info("No snapshots yet. Run a recorded run first.")
    st.stop()

c1,c2 = st.columns(2)
with c1:
    season = st.selectbox("Season", sorted(sw["season"].unique(), reverse=True))
with c2:
    week = st.selectbox("Week", sorted(sw.query("season == @season")["week"].unique(), reverse=True))

tabs = st.tabs(["Odds","Injuries","Weather"])
with tabs[0]:
    df = con.execute("SELECT * FROM odds_snapshots WHERE season=? AND week=? ORDER BY ts_utc DESC", [int(season), int(week)]).df()
    st.caption(f"{len(df)} rows")
    st.dataframe(df, use_container_width=True, hide_index=True)
with tabs[1]:
    df = con.execute("SELECT * FROM injury_snapshots WHERE season=? AND week=? ORDER BY ts_utc DESC", [int(season), int(week)]).df()
    st.caption(f"{len(df)} rows")
    st.dataframe(df, use_container_width=True, hide_index=True)
with tabs[2]:
    df = con.execute("SELECT * FROM weather_snapshots WHERE season=? AND week=? ORDER BY ts_utc DESC", [int(season), int(week)]).df()
    st.caption(f"{len(df)} rows")
    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Latest run artifacts (CSV)")
snaproot = "out/snapshots"
if not os.path.isdir(snaproot):
    st.caption("No snapshot folders yet.")
else:
    runs = sorted(os.listdir(snaproot), reverse=True)[:8]
    for r in runs:
        p = os.path.join(snaproot, r)
        st.write(f"**{r}** — {p}")
        st.write(", ".join(sorted([f for f in os.listdir(p) if f.endswith('.csv') or f.endswith('.json')])))
