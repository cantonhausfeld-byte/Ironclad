import duckdb
import pandas as pd
import streamlit as st
from pathlib import Path

from ironclad.analytics.guardrails import check_exposure, ExposureCaps

DUCK = "out/ironclad.duckdb"

st.set_page_config(page_title="Exposure", layout="wide")
st.title("Exposure Guardrails")

col1, col2, col3 = st.columns(3)
season = col1.number_input("Season", min_value=2018, max_value=2035, value=2025, step=1)
week = col2.number_input("Week", min_value=1, max_value=23, value=1, step=1)
sized = col3.toggle("Use sized picks", value=True)


@st.cache_data(show_spinner=False)
def load_board(duck_path: str, season: int, week: int, sized: bool = True) -> pd.DataFrame:
    if not Path(duck_path).exists():
        return pd.DataFrame()
    table = "picks_sized" if sized else "picks"
    con = duckdb.connect(duck_path, read_only=True)
    try:
        return con.execute(
            """
            SELECT run_id, season, week, game_id, market, side, line, price_american,
                   model_prob, ev_percent, grade, book,
                   kelly_fraction, stake_units, ts_created
            FROM %s
            WHERE season = ? AND week = ?
            ORDER BY ts_created DESC
            """
            % table,
            [season, week],
        ).df()
    except duckdb.CatalogException:
        return pd.DataFrame()
    finally:
        con.close()


board = load_board(DUCK, int(season), int(week), sized)

caps = ExposureCaps()  # defaults; tweak here if you want different UI caps
ok, violations = check_exposure(DUCK, int(season), int(week), caps, sized=sized)
if not ok:
    st.error(f"Guardrails violated: {len(violations)} issue(s). See details below.")
    st.json(violations)
else:
    st.success("Guardrails OK.")

if board.empty:
    st.warning("No picks found for the selected season/week.")
else:
    st.subheader("KPIs")
    total_units = float(board["stake_units"].fillna(0).sum())
    total_picks = int(len(board))
    unique_games = int(board["game_id"].nunique(dropna=True))
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Picks", total_picks)
    col_b.metric("Total Units", f"{total_units:.2f}u")
    col_c.metric("Unique Games", unique_games)

    st.subheader("Board")
    st.dataframe(board, use_container_width=True)
