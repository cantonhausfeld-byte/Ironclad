from pathlib import Path
from typing import Any

import click
import duckdb
import pandas as pd

JOIN_KEYS = ["season", "week", "game_id", "market", "side", "line", "book"]


def _load_picks(con: duckdb.DuckDBPyConnection, run_id: str) -> pd.DataFrame:
    q = """
    SELECT run_id, season, week, game_id, market, side, line, book,
           price_american, model_prob, fair_price_american, ev_percent,
           grade, kelly_fraction, stake_units, ts_created,
           snapshot_odds_ts, snapshot_inj_ts, snapshot_wx_ts
    FROM picks
    WHERE run_id = ?
    """
    return con.execute(q, [run_id]).df()


def _suffix(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    keep = [c for c in df.columns if c not in JOIN_KEYS]
    suffixed = df.copy()
    suffixed.rename(columns={c: f"{c}_{tag}" for c in keep if c != "run_id"}, inplace=True)
    return suffixed


@click.command()
@click.option("--duck", default="out/ironclad.duckdb", show_default=True)
@click.option("--a", "run_a", required=True, help="Baseline run_id")
@click.option("--b", "run_b", required=True, help="Challenger run_id")
@click.option("--outfile", default=None, help="CSV path to write; default under out/diffs/")
def main(duck: str, run_a: str, run_b: str, outfile: str | None) -> None:
    con = duckdb.connect(duck, read_only=True)
    a = _load_picks(con, run_a)
    b = _load_picks(con, run_b)
    if a.empty and b.empty:
        raise SystemExit("No picks for either run.")
    if a.empty:
        raise SystemExit(f"No picks for {run_a}")
    if b.empty:
        raise SystemExit(f"No picks for {run_b}")

    # Align season/week from data (safeguard)
    seasons_a = a[["season", "week"]].drop_duplicates().sort_values(by=["season", "week"])
    seasons_b = b[["season", "week"]].drop_duplicates().sort_values(by=["season", "week"])
    if not seasons_a.reset_index(drop=True).equals(seasons_b.reset_index(drop=True)):
        click.echo(
            "Warning: runs include different season/week combinations; review the diff carefully.",
            err=True,
        )

    aj = _suffix(a, "A")
    bj = _suffix(b, "B")

    merged = aj.merge(bj, on=JOIN_KEYS, how="outer", indicator=True)

    # Classify changes
    def _chg(row: pd.Series, col: str) -> bool:
        va: Any = row.get(f"{col}_A")
        vb: Any = row.get(f"{col}_B")
        if pd.isna(va) and pd.isna(vb):
            return False
        return (va != vb) and not (pd.isna(va) and pd.isna(vb))

    for col in [
        "price_american",
        "model_prob",
        "fair_price_american",
        "ev_percent",
        "grade",
        "stake_units",
        "kelly_fraction",
    ]:
        merged[f"chg_{col}"] = merged.apply(lambda r: _chg(r, col), axis=1)

    # Simple deltas
    merged["delta_ev_pct"] = merged["ev_percent_B"] - merged["ev_percent_A"]
    merged["delta_stake_u"] = merged["stake_units_B"] - merged["stake_units_A"]
    merged["delta_price"] = merged["price_american_B"] - merged["price_american_A"]
    merged["delta_prob"] = merged["model_prob_B"] - merged["model_prob_A"]

    # Counts
    only_a = (merged["_merge"] == "left_only").sum()
    only_b = (merged["_merge"] == "right_only").sum()
    both = (merged["_merge"] == "both").sum()
    grade_swaps = merged["chg_grade"].sum()
    stake_swaps = merged["chg_stake_units"].sum()

    # Exposure deltas by team/market (quick view)
    exposure = (
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

    # Write CSV
    outdir = Path("out/diffs")
    outdir.mkdir(parents=True, exist_ok=True)
    if outfile is None:
        outfile_path: Path = outdir / f"{run_a}__vs__{run_b}.csv"
    else:
        outfile_path = Path(outfile)
    merged.to_csv(outfile_path, index=False)

    # Print summary
    print(f"Compared runs: A={run_a} vs B={run_b}")
    print(f"Rows only in A: {only_a} | only in B: {only_b} | in both: {both}")
    print(f"Grade changes: {grade_swaps} | Stake changes: {stake_swaps}")
    print(f"CSV → {outfile_path}")
    print("\nTop exposure deltas:")
    with pd.option_context("display.max_rows", 20, "display.max_columns", 10):
        print(exposure.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
