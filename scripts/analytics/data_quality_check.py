import json
import sys

import click

from ironclad.analytics.data_quality import check_freshness, check_quorum


@click.command()
@click.option("--duck", default="out/ironclad.duckdb")
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option("--max_age_minutes", type=int, default=180)
@click.option("--min_odds_rows", type=int, default=10)
def main(duck, season, week, max_age_minutes, min_odds_rows):
    freshness = check_freshness(duck, season, week, max_age_minutes=max_age_minutes)
    quorum = check_quorum(duck, season, week, min_odds_rows=min_odds_rows)
    out = {"freshness": freshness, "quorum": quorum}
    print(json.dumps(out, indent=2))

    bad = [name for name, meta in freshness.items() if not meta.get("ok", False)]
    if bad or not quorum.get("ok", False):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
