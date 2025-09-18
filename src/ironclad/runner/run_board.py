import argparse
import uuid
from datetime import datetime

from ..persist.duckdb_connector import connect, write_picks, write_run
from ..schemas.pick import Grade, Market, Pick
from ..schemas.run_manifest import RunManifest
from ..services.odds_client import OddsClient
from ..settings import settings
from ..utils.odds import american_to_prob, prob_to_american


def synthesize_picks(run_id: str, season: int, week: int):
    now = datetime.utcnow().isoformat()
    client = OddsClient()
    board = client.fetch_board(season, week)
    picks: list[Pick] = []
    for line in board:
        if line.market != "ML":
            continue
        p_market = american_to_prob(line.price_american)
        p_model = min(max(p_market + 0.02, 0.02), 0.98)
        fair_price = prob_to_american(p_model)
        ev = p_model * (
            100 / abs(line.price_american) if line.price_american < 0 else line.price_american / 100
        ) - (1 - p_model)
        grade = (
            Grade.A
            if ev * 100 >= 2.5
            else Grade.B if ev * 100 >= 1.2 else Grade.C if ev > 0 else Grade.NO_PICK
        )
        picks.append(
            Pick(
                run_id=run_id,
                game_id=line.game_id,
                season=season,
                week=week,
                market=Market.ML,
                side=line.side,
                line=None,
                price_american=line.price_american,
                model_prob=p_model,
                fair_price_american=fair_price,
                ev_percent=ev * 100,
                z_score=0.0,
                robust_ev_percent=ev * 100,
                grade=grade,
                kelly_fraction=(
                    0.05 if grade in (Grade.A, Grade.B) else 0.02 if grade == Grade.C else 0.0
                ),
                stake_units=0.0,
                book=line.book,
                ts_created=now,
            )
        )
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    args = ap.parse_args()
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    manifest = RunManifest(
        run_id=run_id,
        season=args.season,
        week=args.week,
        profile=settings.profile,
        settings_json={"demo": settings.demo},
    )
    con = connect(settings.duckdb_path)
    write_run(con, manifest)
    picks = synthesize_picks(run_id, args.season, args.week)
    write_picks(con, picks)
    print(f"Run {run_id} wrote {len(picks)} picks to {settings.duckdb_path}")


if __name__ == "__main__":
    main()
