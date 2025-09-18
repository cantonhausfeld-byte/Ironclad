import duckdb
import pandas as pd
import streamlit as st
st.set_page_config(page_title="Ironclad Picks", layout="wide")
st.title("Ironclad — Picks")
db = "out/ironclad.duckdb"
try:
    con = duckdb.connect(db, read_only=True)
    df = con.execute("select * from picks order by ts_created desc").df()
    if df.empty:
        st.info("No picks yet. Run: `python scripts/ic.py run-preslate`")
    else:
        cols = ["run_id","season","week","game_id","market","side","line","price_american",
                "model_prob","ev_percent","grade","stake_units","book","ts_created"]
        for c in cols:
            if c not in df.columns:
                df[c] = None
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Could not read DuckDB at {db}: {e}")
