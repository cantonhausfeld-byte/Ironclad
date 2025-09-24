import json, sys, click
from ironclad.analytics.guardrails import check_exposure, ExposureCaps

@click.command()
@click.option("--duck", default="out/ironclad.duckdb", help="Path to DuckDB file.")
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option("--sized/--no-sized", default=True, help="Use picks_sized (default) or picks.")
@click.option("--max_total_u", type=float, default=25.0)
@click.option("--max_team_u", type=float, default=10.0)
@click.option("--max_market_u", type=float, default=15.0)
@click.option("--max_game_u", type=float, default=10.0)
@click.option("--require_min_picks", type=int, default=1)
def main(duck, season, week, sized, max_total_u, max_team_u, max_market_u, max_game_u, require_min_picks):
    caps = ExposureCaps(
        max_total_u=max_total_u, max_team_u=max_team_u,
        max_market_u=max_market_u, max_game_u=max_game_u,
        require_min_picks=require_min_picks
    )
    ok, violations = check_exposure(duck, season, week, caps, sized=sized)
    out = {"ok": ok, "violations": violations, "season": season, "week": week, "sized": sized}
    print(json.dumps(out, indent=2))
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()
