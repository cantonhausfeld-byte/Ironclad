from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ironclad — Run Diff", layout="wide")
st.title("Ironclad — Run Diff")

DUCK = "out/ironclad.duckdb"
con = duckdb.connect(DUCK, read_only=True)

runs_query = (
    "SELECT run_id, season, week, started_at "
    "FROM runs ORDER BY started_at DESC NULLS LAST LIMIT 100"
)
runs = con.execute(runs_query).df()
if runs.empty:
    st.info("No runs recorded yet. Use 'record-run' first.")
    st.stop()

c1, c2 = st.columns(2)
run_a = c1.selectbox("Baseline run (A)", runs["run_id"].tolist())
run_b = c2.selectbox(
    "Challenger run (B)", [r for r in runs["run_id"].tolist() if r != run_a]
)


def _load(run_id: str) -> pd.DataFrame:
    q = """
    SELECT run_id, season, week, game_id, market, side, line, book,
           price_american, model_prob, fair_price_american, ev_percent,
           grade, kelly_fraction, stake_units, ts_created
    FROM picks WHERE run_id = ?
    """
    return con.execute(q, [run_id]).df()


a = _load(run_a)
b = _load(run_b)

JOIN_KEYS = ["season", "week", "game_id", "market", "side", "line", "book"]
aj = a.rename(columns={c: f"{c}_A" for c in a.columns if c not in JOIN_KEYS})
bj = b.rename(columns={c: f"{c}_B" for c in b.columns if c not in JOIN_KEYS})

m = aj.merge(bj, on=JOIN_KEYS, how="outer", indicator=True)
m["delta_ev_pct"] = m["ev_percent_B"] - m["ev_percent_A"]
m["delta_stake_u"] = m["stake_units_B"] - m["stake_units_A"]
m["delta_price"] = m["price_american_B"] - m["price_american_A"]

only_a = (m["_merge"] == "left_only").sum()
only_b = (m["_merge"] == "right_only").sum()
both = (m["_merge"] == "both").sum()
st.caption(f"Only in A: {only_a} | Only in B: {only_b} | In both: {both}")

tabs = st.tabs(["All", "Changed grades", "Stake deltas", "EV deltas", "Only-in-A/B"])
with tabs[0]:
    st.dataframe(m, use_container_width=True, hide_index=True)

with tabs[1]:
    df = m[(m["grade_A"] != m["grade_B"]) & ~(m["grade_A"].isna() & m["grade_B"].isna())]
    st.dataframe(df, use_container_width=True, hide_index=True)

with tabs[2]:
    df = m[m["delta_stake_u"].fillna(0).abs() > 0]
    st.dataframe(
        df.sort_values("delta_stake_u", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

with tabs[3]:
    df = m[m["delta_ev_pct"].fillna(0).abs() > 0]
    st.dataframe(
        df.sort_values("delta_ev_pct", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

with tabs[4]:
    col_a, col_b = st.columns(2)
    col_a.subheader("Only in A")
    col_a.dataframe(m[m["_merge"] == "left_only"], use_container_width=True, hide_index=True)
    col_b.subheader("Only in B")
    col_b.dataframe(m[m["_merge"] == "right_only"], use_container_width=True, hide_index=True)

outdir = Path("out/diffs")
outdir.mkdir(parents=True, exist_ok=True)
csv_path = outdir / f"{run_a}__vs__{run_b}.streamlit.csv"
m.to_csv(csv_path, index=False)
st.download_button(
    "Download diff CSV",
    data=csv_path.read_bytes(),
    file_name=csv_path.name,
    mime="text/csv",
)
