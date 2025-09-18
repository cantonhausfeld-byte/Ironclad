import json
import sys

import click

from ironclad.analytics.guardrails import ExposureCaps, caps_from_settings, check_exposure
from ironclad.settings import get_settings


@click.command()
@click.option("--duck", default=None, help="Path to DuckDB file.")
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option("--sized/--no-sized", default=True, help="Use picks_sized (default) or picks.")
@click.option("--max_total_u", type=float, default=None)
@click.option("--max_team_u", type=float, default=None)
@click.option("--max_market_u", type=float, default=None)
@click.option("--max_game_u", type=float, default=None)
@click.option("--require_min_picks", type=int, default=None)
def main(
    duck,
    season,
    week,
    sized,
    max_total_u,
    max_team_u,
    max_market_u,
    max_game_u,
    require_min_picks,
):
    duck = duck or get_settings().DUCKDB__PATH

    caps = caps_from_settings()
    if max_total_u is not None:
        caps.max_total_u = max_total_u
    if max_team_u is not None:
        caps.max_team_u = max_team_u
    if max_market_u is not None:
        caps.max_market_u = max_market_u
    if max_game_u is not None:
        caps.max_game_u = max_game_u
    if require_min_picks is not None:
        caps.require_min_picks = require_min_picks

    ok, violations = check_exposure(duck, season, week, caps, sized=sized)
    out = {
        "ok": ok,
        "violations": violations,
        "season": season,
        "week": week,
        "sized": sized,
        "caps": caps.__dict__,
        "duck_path": duck,
    }
    print(json.dumps(out, indent=2))
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
