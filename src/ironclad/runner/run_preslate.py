import uuid, pandas as pd
from datetime import datetime, timezone
from ..settings import get_settings
from ..persist.duckdb_connector import connect, write_run, write_picks
from ..models.baseline import predict, BaselineConfig
from ..schemas.pick import Pick
from ..logging import setup_logging

def load_week_games(season: int, week: int) -> pd.DataFrame:
    try:
        df = pd.read_csv("out/schedules/master_schedule.csv")
        df = df[(df["season"]==season) & (df["week"]==week)]
        if not df.empty:
            return df[["game_id","season","week","home","away","kickoff_utc_iso","venue"]]
    except Exception:
        pass
    return pd.DataFrame([{
        "game_id": f"W{week}_DEMO1", "season": season, "week": week,
        "home": "PHI", "away": "DAL", "kickoff_utc_iso": "2025-09-21T17:00:00Z", "venue": "LFF"
    }])

def run():
    log = setup_logging()
    s = get_settings()
    run_id = str(uuid.uuid4())
    log.info("run.start", run_id=run_id, season=int(s.SEASON), week=int(s.WEEK or 1))

    games = load_week_games(season=s.SEASON, week=int(s.WEEK or 1))
    log.info("run.games_loaded", n=len(games))

    preds = predict(games, BaselineConfig())
    now = datetime.now(timezone.utc).isoformat()
    preds["run_id"] = run_id
    preds["ts_created"] = now

    # schema validation
    _ = [Pick(**row) for row in preds.to_dict(orient="records")]

    con = connect(s.DUCKDB__PATH)
    write_run(con, {"run_id": run_id, "season": int(s.SEASON), "week": int(s.WEEK or 1), "settings_json": {}})
    write_picks(con, preds[["run_id","game_id","season","week","market","side","line","price_american","model_prob","fair_price_american","ev_percent","z_score","robust_ev_percent","grade","kelly_fraction","stake_units","book","ts_created"]])
    out_csv = f"out/picks/{run_id}_picks.csv"
    preds.to_csv(out_csv, index=False)
    log.info("run.written", picks_csv=out_csv, duckdb_path=s.DUCKDB__PATH, rows=len(preds))
    print(f"OK preslate run_id={run_id} rows={len(preds)} → out/picks/, DuckDB={s.DUCKDB__PATH}")
