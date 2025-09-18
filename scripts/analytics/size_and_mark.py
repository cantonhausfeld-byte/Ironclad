import glob
import json
import os

import click
import pandas as pd

from ironclad.persist.duckdb_connector import connect, write_picks_sized
from ironclad.portfolio.sizer import size_portfolio
from ironclad.settings import get_settings


def _latest_picks_csv() -> str | None:
    files = sorted(glob.glob("out/picks/*_picks.csv"))
    return files[-1] if files else None


@click.command()
@click.option("--bankroll_units", type=float, default=None)
@click.option("--kelly_scale", type=float, default=None)
@click.option("--max_per_bet_u", type=float, default=None)
@click.option("--max_per_game_u", type=float, default=None)
@click.option("--max_total_u", type=float, default=None)
def main(
    bankroll_units,
    kelly_scale,
    max_per_bet_u,
    max_per_game_u,
    max_total_u,
):
    settings = get_settings()
    bankroll_units = bankroll_units if bankroll_units is not None else settings.SIZING__BANKROLL_UNITS
    kelly_scale = kelly_scale if kelly_scale is not None else settings.SIZING__KELLY_SCALE
    max_per_bet_u = max_per_bet_u if max_per_bet_u is not None else settings.SIZING__MAX_PER_BET_U
    max_per_game_u = max_per_game_u if max_per_game_u is not None else settings.SIZING__MAX_PER_GAME_U
    max_total_u = max_total_u if max_total_u is not None else settings.SIZING__MAX_TOTAL_U

    latest = _latest_picks_csv()
    if not latest:
        print("No picks CSVs found in out/picks.")
        return

    base = pd.read_csv(latest)
    sized = size_portfolio(
        base,
        bankroll_units=bankroll_units,
        kelly_scale=kelly_scale,
        max_per_bet_u=max_per_bet_u,
        max_per_game_u=max_per_game_u,
        max_total_u=max_total_u,
    )

    out_path = latest.replace("_picks.csv", "_picks_sized.csv")
    sized.to_csv(out_path, index=False)
    os.makedirs("out/analytics", exist_ok=True)
    with open("out/analytics/last_sized.json", "w", encoding="utf-8") as fh:
        json.dump(
            {
                "input": os.path.basename(latest),
                "output": os.path.basename(out_path),
                "sizing_cfg": {
                    "bankroll_units": bankroll_units,
                    "kelly_scale": kelly_scale,
                    "max_per_bet_u": max_per_bet_u,
                    "max_per_game_u": max_per_game_u,
                    "max_total_u": max_total_u,
                },
            },
            fh,
        )
    print("Sized and wrote CSV:", out_path)

    if "run_id" not in sized.columns and "run_id" in base.columns:
        sized["run_id"] = base["run_id"]
    for col in ("ts_created", "season", "week", "book", "fair_price_american"):
        if col not in sized.columns and col in base.columns:
            sized[col] = base[col]

    con = connect(settings.DUCKDB__PATH)
    write_picks_sized(con, sized)
    print("Persisted sized stakes → DuckDB:", settings.DUCKDB__PATH)


if __name__ == "__main__":
    main()
