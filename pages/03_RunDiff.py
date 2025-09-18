"""Streamlit page to compare two Ironclad runs."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Ensure the project source is importable when running via ``streamlit run``.
ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from ironclad.settings import settings  # noqa: E402  (added after sys.path tweak)

st.set_page_config(page_title="Run Diff", layout="wide")
st.title("Run Diff — compare Run A vs Run B")


@st.cache_data(show_spinner=False)
def fetch_runs(db_path: str) -> pd.DataFrame:
    """Return available runs ordered from newest to oldest."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
        SELECT run_id, season, week, profile, started_at
        FROM runs
        ORDER BY started_at DESC
        """
        return con.execute(query).df()
    finally:
        con.close()


@st.cache_data(show_spinner=False)
def fetch_picks(db_path: str, run_id: str) -> pd.DataFrame:
    """Load picks for a run."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = """
        SELECT season, week, game_id, market, side, line, book,
               grade, stake_units, price_american, model_prob,
               fair_price_american, robust_ev_percent, ev_percent, kelly_fraction
        FROM picks
        WHERE run_id = ?
        """
        return con.execute(query, [run_id]).df()
    finally:
        con.close()


def prepare_table(picks_a: pd.DataFrame, picks_b: pd.DataFrame) -> pd.DataFrame:
    """Merge runs A and B into a comparison frame."""
    picks_a = picks_a.copy()
    picks_b = picks_b.copy()
    key_cols: list[str] = [
        "season",
        "week",
        "game_id",
        "market",
        "side",
        "line",
        "book",
    ]
    # Ensure both frames contain the same value columns for merging.
    value_cols: list[str] = [
        "grade",
        "stake_units",
        "price_american",
        "model_prob",
        "fair_price_american",
        "robust_ev_percent",
        "ev_percent",
        "kelly_fraction",
    ]
    for frame in (picks_a, picks_b):
        for col in value_cols:
            if col not in frame.columns:
                frame[col] = pd.NA

    a = picks_a[key_cols + value_cols].rename(columns={c: f"{c}_A" for c in value_cols})
    b = picks_b[key_cols + value_cols].rename(columns={c: f"{c}_B" for c in value_cols})

    merged = a.merge(b, on=key_cols, how="outer")

    for col in ("stake_units_A", "stake_units_B"):
        if col in merged.columns:
            merged[col] = merged[col].fillna(0.0)

    for col in ("grade_A", "grade_B"):
        if col in merged.columns:
            merged[col] = merged[col].fillna("NA").astype(str)

    merged["in_A"] = ~merged["grade_A"].eq("NA")
    merged["in_B"] = ~merged["grade_B"].eq("NA")

    merged["stake_delta"] = merged["stake_units_B"] - merged["stake_units_A"]
    merged["abs_stake_delta"] = merged["stake_delta"].abs()
    merged["grade_changed"] = merged["grade_A"] != merged["grade_B"]

    merged["change_type"] = np.select(
        [
            merged["in_A"]
            & merged["in_B"]
            & ~(merged["grade_changed"] | merged["stake_delta"].ne(0.0)),
            merged["in_A"] & ~merged["in_B"],
            ~merged["in_A"] & merged["in_B"],
        ],
        ["Unchanged", "Only in A", "Only in B"],
        default="Changed",
    )

    display_cols: Iterable[str] = list(key_cols) + [
        "grade_A",
        "grade_B",
        "stake_units_A",
        "stake_units_B",
        "stake_delta",
        "abs_stake_delta",
        "grade_changed",
        "change_type",
    ]
    return merged.loc[:, display_cols].sort_values(by="abs_stake_delta", ascending=False)


def format_run_label(row: pd.Series) -> str:
    started = row.get("started_at")
    started_fmt = started.strftime("%Y-%m-%d %H:%M") if pd.notna(started) else ""
    return (
        f"{row['run_id']} — S{int(row['season'])} W{int(row['week'])} "
        f"[{row['profile']}] {started_fmt}"
    ).strip()


# --- Input controls -------------------------------------------------------------------------

default_db = settings.duckdb_path

col_db_path = st.text_input("DuckDB path", value=str(default_db))
duck_path = Path(col_db_path).expanduser()

if not col_db_path:
    st.info("Provide a DuckDB path to compare runs.")
    st.stop()

if not duck_path.exists():
    st.warning(f"DuckDB not found at {duck_path}. Run a board to generate runs first.")
    st.stop()

try:
    runs_df = fetch_runs(str(duck_path))
except duckdb.Error as exc:  # pragma: no cover - streamlit guard
    st.error(f"Unable to read runs from {duck_path}: {exc}")
    st.stop()

if runs_df.empty:
    st.info("No runs found in DuckDB yet. Generate runs before diffing.")
    st.stop()

run_labels = {row["run_id"]: format_run_label(row) for _, row in runs_df.iterrows()}
run_ids = list(run_labels.keys())

col_a, col_b = st.columns(2)
def_idx_b = 1 if len(run_ids) > 1 else 0
run_a = col_a.selectbox("Run A (baseline)", options=run_ids, format_func=run_labels.get, index=0)
run_b = col_b.selectbox(
    "Run B (challenger)", options=run_ids, format_func=run_labels.get, index=def_idx_b
)

picks_a = fetch_picks(str(duck_path), run_a)
picks_b = fetch_picks(str(duck_path), run_b)

if picks_a.empty and picks_b.empty:
    st.warning("Neither run has picks recorded.")
    st.stop()

merged = prepare_table(picks_a, picks_b)

# Tabs showing merged + raw tables.
tab_diff, tab_a, tab_b = st.tabs(
    [
        "Diff table",
        f"Run A: {run_a}",
        f"Run B: {run_b}",
    ]
)

with tab_diff:
    st.caption("Merged comparison highlighting stake deltas and grade changes.")
    st.dataframe(merged, use_container_width=True)

with tab_a:
    st.dataframe(picks_a, use_container_width=True)

with tab_b:
    st.dataframe(picks_b, use_container_width=True)


# --- Delta exposure by team/market (bar chart) ---
st.divider()
st.subheader("Delta exposure by team/market")

exp = (
    merged.assign(
        stake_A=merged["stake_units_A"].fillna(0.0),
        stake_B=merged["stake_units_B"].fillna(0.0),
    )
    .groupby(["market", "side"], dropna=False)[["stake_A", "stake_B"]]
    .sum()
    .assign(delta=lambda d: d["stake_B"] - d["stake_A"])
    .reset_index()
    .sort_values("delta", ascending=False)
)

st.dataframe(exp, use_container_width=True, hide_index=True)

fig = plt.figure()
plt.bar(range(len(exp)), exp["delta"])
plt.xticks(
    range(len(exp)),
    [f"{row['market']}:{row['side']}" for _, row in exp.iterrows()],
    rotation=90,
)
plt.title("Δ Stake Units (B - A) by Market:Side")
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# --- Grade-change heatmap (A→B, etc.) ---
st.divider()
st.subheader("Grade-change heatmap (A → B/C/…)")

ga = merged["grade_A"].astype(str).fillna("NA")
gb = merged["grade_B"].astype(str).fillna("NA")

cross_counts = pd.DataFrame({"from": ga, "to": gb}).value_counts().rename("count").reset_index()

if cross_counts.empty:
    cross = pd.DataFrame()
else:
    cross = cross_counts.pivot(index="from", columns="to", values="count").fillna(0).astype(int)
    cross = cross.reindex(sorted(cross.index))
    cross = cross.reindex(sorted(cross.columns), axis=1)

st.caption("Counts of picks moving from grade in Run A (rows) to grade in Run B (columns).")
st.dataframe(cross, use_container_width=True)

fig2 = plt.figure()
plt.imshow(cross.values if not cross.empty else [[0]], aspect="auto")
plt.xticks(range(cross.shape[1]), cross.columns if not cross.empty else [])
plt.yticks(range(cross.shape[0]), cross.index if not cross.empty else [])
plt.title("Grade changes A → B (counts)")
for i in range(cross.shape[0]):
    for j in range(cross.shape[1]):
        plt.text(j, i, str(int(cross.iat[i, j])), ha="center", va="center")
plt.tight_layout()
st.pyplot(fig2)
plt.close(fig2)

# --- Optional: save the diff table automatically ---
outdir = Path("out/diffs")
outdir.mkdir(parents=True, exist_ok=True)
save_csv = outdir / f"{run_a}__vs__{run_b}.ui.csv"
merged.to_csv(save_csv, index=False)
st.caption(f"Saved current diff to {save_csv}")
