import json, glob, os, pandas as pd, click
from ironclad.portfolio.sizer import size_portfolio
from ironclad.settings import get_settings
from ironclad.persist.duckdb_connector import connect, write_picks_sized

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
    settings = get_settings()
    duckdb_path = getattr(settings, "duckdb_path", getattr(settings, "DUCKDB__PATH", "out/ironclad.duckdb"))
    con = connect(duckdb_path)

    latest = _latest_picks_csv()
    if not latest:
        print("No picks CSVs found in out/picks.")
        con.close()
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
    out = latest.replace("_picks.csv", "_picks_sized.csv")
    sized.to_csv(out, index=False)
    os.makedirs("out/analytics", exist_ok=True)
    with open("out/analytics/last_sized.json","w") as f:
        json.dump({"input": os.path.basename(latest), "output": os.path.basename(out)}, f)
    print("Sized and wrote CSV:", out)

    # Persist to DuckDB (picks_sized)
    # Try to propagate run_id/ts_created if present in base
    if "run_id" not in sized.columns and "run_id" in base.columns:
        sized["run_id"] = base["run_id"]
    if "ts_created" not in sized.columns and "ts_created" in base.columns:
        sized["ts_created"] = base["ts_created"]
    if "season" not in sized.columns and "season" in base.columns:
        sized["season"] = base["season"]
    if "week" not in sized.columns and "week" in base.columns:
        sized["week"] = base["week"]
    if "book" not in sized.columns and "book" in base.columns:
        sized["book"] = base["book"]
    if "fair_price_american" not in sized.columns and "fair_price_american" in base.columns:
        sized["fair_price_american"] = base["fair_price_american"]

    write_picks_sized(con, sized)
    con.close()
    print("Persisted sized stakes → DuckDB:", duckdb_path)

if __name__ == "__main__":
    main()
