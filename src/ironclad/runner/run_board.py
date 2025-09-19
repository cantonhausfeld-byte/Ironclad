from __future__ import annotations

import argparse

from ..persist.duckdb_store import DuckDBStore
from ..runner.context import RunContext
from ..runner.pipeline import generate_picks_from_board, run_pipeline
from ..schemas.pick import Pick
from ..services.odds_client import OddsClient
from ..settings import settings


def synthesize_picks(run_id: str, season: int, week: int) -> list[Pick]:
    client = OddsClient()
    board = [
        {
            "game_id": line.game_id,
            "book": line.book,
            "market": line.market,
            "side": line.side,
            "line": line.line,
            "price_american": line.price_american,
            "ts": line.ts,
        }
        for line in client.fetch_board(season, week)
    ]
    return generate_picks_from_board(
        run_id,
        season=season,
        week=week,
        board=board,
        profile=settings.profile,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    args = ap.parse_args()

    context = RunContext.new(season=args.season, week=args.week)
    store = DuckDBStore(settings.duckdb_path)
    result = run_pipeline(context, store=store)
    print(
        f"Run {context.run_id} wrote {len(result.picks)} picks "
        f"to {settings.duckdb_path} (guardrails: {len(result.guardrails)})"
    )


if __name__ == "__main__":
    main()
