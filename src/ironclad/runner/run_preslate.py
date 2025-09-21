from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..models.baseline import BaselineConfig, predict
from ..persist.duckdb_connector import connect, write_picks, write_run
from ..schemas.pick import Pick
from ..settings import get_settings


def load_week_games(season: int, week: int) -> pd.DataFrame:
    try:
        df = pd.read_csv("out/schedules/master_schedule.csv")
        df = df[(df["season"] == season) & (df["week"] == week)]
        if not df.empty:
            return df[["game_id", "season", "week", "home", "away", "kickoff_utc_iso", "venue"]]
    except Exception:
        pass
    return pd.DataFrame(
        [
            {
                "game_id": f"W{week}_DEMO1",
                "season": season,
                "week": week,
                "home": "PHI",
                "away": "DAL",
                "kickoff_utc_iso": "2025-09-21T17:00:00Z",
                "venue": "LFF",
            }
        ]
    )


def run() -> None:
    settings = get_settings()
    run_id = str(uuid.uuid4())
    week = int(settings.WEEK or 1)
    games = load_week_games(season=settings.SEASON, week=week)
    predictions = predict(games, BaselineConfig())

    now = datetime.now(timezone.utc).isoformat()
    predictions["run_id"] = run_id
    predictions["ts_created"] = now

    _ = [Pick(**row) for row in predictions.to_dict(orient="records")]

    con = connect(settings.DUCKDB__PATH)
    write_run(
        con,
        {
            "run_id": run_id,
            "season": int(settings.SEASON),
            "week": week,
            "settings_json": {},
        },
    )
    write_picks(
        con,
        predictions[
            [
                "run_id",
                "game_id",
                "season",
                "week",
                "market",
                "side",
                "line",
                "price_american",
                "model_prob",
                "fair_price_american",
                "ev_percent",
                "z_score",
                "robust_ev_percent",
                "grade",
                "kelly_fraction",
                "stake_units",
                "book",
                "ts_created",
            ]
        ],
    )

    picks_dir = Path("out/picks")
    picks_dir.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(picks_dir / f"{run_id}_picks.csv", index=False)
    print(f"OK preslate run_id={run_id} rows={len(predictions)} → out/picks/, DuckDB={settings.DUCKDB__PATH}")
