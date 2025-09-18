"""CLI helper to highlight exposure deltas between two runs."""

from __future__ import annotations

from pathlib import Path

import click
import duckdb
import pandas as pd

_KEY_COLS = ["season", "week", "game_id", "market", "side", "line", "book"]


@click.command()
@click.option("--duck", "duck_path", default="out/ironclad.duckdb", show_default=True)
@click.option("--a", "run_a", required=True, help="Baseline run identifier")
@click.option("--b", "run_b", required=True, help="Challenger run identifier")
@click.option("--top", type=int, default=20, show_default=True, help="Rows to print")
def main(duck_path: str, run_a: str, run_b: str, top: int) -> None:
    """Print the largest exposure deltas between two runs."""
    db_path = Path(duck_path).expanduser()
    if not db_path.exists():
        raise click.ClickException(f"DuckDB not found at {db_path}")

    try:
        con = duckdb.connect(str(db_path), read_only=True)
    except duckdb.Error as exc:  # pragma: no cover - CLI guard
        raise click.ClickException(f"Failed to open {db_path}: {exc}") from exc

    query = """
    SELECT season, week, game_id, market, side, line, book,
           stake_units, run_id
    FROM picks
    WHERE run_id IN (?, ?)
    """
    try:
        df = con.execute(query, [run_a, run_b]).df()
    finally:
        con.close()

    if df.empty:
        raise click.ClickException("No picks found for the provided runs.")

    a = (
        df[df["run_id"] == run_a]
        .drop(columns=["run_id"])
        .rename(columns={"stake_units": "stake_A"})
    )
    b = (
        df[df["run_id"] == run_b]
        .drop(columns=["run_id"])
        .rename(columns={"stake_units": "stake_B"})
    )
    merged = a.merge(b, on=_KEY_COLS, how="outer")
    merged["stake_A"] = merged["stake_A"].fillna(0.0)
    merged["stake_B"] = merged["stake_B"].fillna(0.0)

    exposure = (
        merged.groupby(["market", "side"], dropna=False)[["stake_A", "stake_B"]]
        .sum()
        .assign(delta=lambda d: d["stake_B"] - d["stake_A"])
        .reset_index()
        .sort_values("delta", ascending=False)
    )

    if exposure.empty:
        click.echo("No exposure differences found.")
        return

    with pd.option_context("display.max_rows", top, "display.max_columns", None):
        click.echo(exposure.head(top).to_string(index=False))


if __name__ == "__main__":
    main()
