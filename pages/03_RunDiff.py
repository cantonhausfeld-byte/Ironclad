import streamlit as st
import duckdb

st.set_page_config(page_title="Run Diff", layout="wide")
st.title("Run Diff Explorer")

duck_path = st.text_input("DuckDB path", value="out/ironclad.duckdb")
col_a, col_b = st.columns(2)
run_a = col_a.text_input("Baseline run_id", key="run_diff_a")
run_b = col_b.text_input("Challenger run_id", key="run_diff_b")

if duck_path and run_a and run_b:
    try:
        con = duckdb.connect(duck_path, read_only=True)
        query = """
        SELECT season, week, game_id, market, side, line, book, price_american,
               grade, stake_units
        FROM picks WHERE run_id = ?
        ORDER BY season, week, game_id, market, side, line, book
        """
        df_a = con.execute(query, [run_a]).df()
        df_b = con.execute(query, [run_b]).df()
        con.close()
        st.write("Baseline picks", df_a)
        st.write("Challenger picks", df_b)
    except Exception as exc:
        st.error(f"Failed to load runs: {exc}")

st.divider()
st.subheader("Promote challenger to prod (guardrails-gated)")
cmd = f'RUN_A={run_a} RUN_B={run_b} make promote'
st.code(cmd, language="bash")
st.caption("This will validate guardrails first; add FORCE=1 to override:  RUN_A=… RUN_B=… FORCE=1 make promote")
