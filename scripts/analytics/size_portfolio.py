import os, glob, pandas as pd, click
from ironclad.portfolio.sizer import size_portfolio


def _latest_picks_csv() -> str | None:
    files = sorted(glob.glob("out/picks/*_picks.csv"))
    return files[-1] if files else None


@click.command()
@click.option("--bankroll_units", type=float, default=100.0)
@click.option("--kelly_scale", type=float, default=0.25)
@click.option("--max_per_bet_u", type=float, default=3.0)
@click.option("--max_per_game_u", type=float, default=10.0)
@click.option("--max_total_u", type=float, default=25.0)
def main(bankroll_units, kelly_scale, max_per_bet_u, max_per_game_u, max_total_u):
    latest = _latest_picks_csv()
    if not latest:
        print("No picks CSVs found in out/picks.")
        return
    df = pd.read_csv(latest)
    sized = size_portfolio(
        df,
        bankroll_units=bankroll_units,
        kelly_scale=kelly_scale,
        max_per_bet_u=max_per_bet_u,
        max_per_game_u=max_per_game_u,
        max_total_u=max_total_u,
    )
    out = latest.replace("_picks.csv", "_picks_sized.csv")
    sized.to_csv(out, index=False)
    print("Wrote sized picks:", out, "rows=", len(sized))


if __name__ == "__main__":
    main()
