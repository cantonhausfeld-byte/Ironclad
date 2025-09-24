
from __future__ import annotations

import glob
import json
import os
from pathlib import Path

import click
import pandas as pd

from ironclad.persist.duckdb_connector import connect, write_sized_picks
from ironclad.portfolio.sizer import size_portfolio
from ironclad.settings import settings

PICKS_DIR = Path("out/picks")
ANALYTICS_DIR = Path("out/analytics")


def _latest_picks_csv() -> str | None:
    files = sorted(glob.glob(str(PICKS_DIR / "*_picks.csv")))
    return files[-1] if files else None


@click.command()
@click.option("--bankroll_units", type=float, default=100.0)
@click.option("--kelly_scale", type=float, default=0.25)
@click.option("--max_per_bet_u", type=float, default=3.0)
@click.option("--max_per_game_u", type=float, default=10.0)
@click.option("--max_total_u", type=float, default=25.0)
def main(
    bankroll_units: float,
    kelly_scale: float,
    max_per_bet_u: float,
    max_per_game_u: float,
    max_total_u: float,
) -> None:
    """Size the latest picks CSV and persist metadata about the run."""

    latest = _latest_picks_csv()
    if not latest:
        click.echo("No picks CSVs found in out/picks.")
        return

    df = pd.read_csv(latest)
    sizing_config = {
        "bankroll_units": bankroll_units,
        "kelly_scale": kelly_scale,
        "max_per_bet_u": max_per_bet_u,
        "max_per_game_u": max_per_game_u,
        "max_total_u": max_total_u,
    }
    sized = size_portfolio(
        df,
        bankroll_units=bankroll_units,
        kelly_scale=kelly_scale,
        max_per_bet_u=max_per_bet_u,
        max_per_game_u=max_per_game_u,
        max_total_u=max_total_u,
    )

    out_path = Path(latest.replace("_picks.csv", "_picks_sized.csv"))
    sized.to_csv(out_path, index=False)
    os.makedirs(ANALYTICS_DIR, exist_ok=True)
    with open(ANALYTICS_DIR / "last_sized.json", "w", encoding="utf-8") as file:
        json.dump(
            {
                "input": os.path.basename(latest),
                "output": os.path.basename(out_path),
                "config": sizing_config,
            },
            file,
        )
    con = connect(settings.duckdb_path)
    write_sized_picks(
        con,
        sized.to_dict(orient="records"),
        input_csv=os.path.basename(latest),
        output_csv=os.path.basename(out_path),
        sizing_config=sizing_config,
    )
    click.echo(f"Sized and wrote: {out_path}")


if __name__ == "__main__":
    main()
