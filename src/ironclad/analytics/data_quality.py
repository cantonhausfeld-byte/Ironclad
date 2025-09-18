from __future__ import annotations
import duckdb
from datetime import datetime, timezone, timedelta

def _con(path:str): return duckdb.connect(path, read_only=True)

def check_freshness(duck:str, season:int, week:int, *, max_age_minutes:int=120) -> dict:
    """Return dict with table freshness in minutes and ok flags."""
    con = _con(duck)
    out = {}
    now = datetime.now(timezone.utc)
    for tbl in ["odds_snapshots","injury_snapshots","weather_snapshots"]:
        df = con.execute(f"SELECT max(ts_utc) AS ts FROM {tbl} WHERE season=? AND week=?", [season, week]).df()
        ts = df["ts"].iloc[0]
        if ts is None:
            out[tbl] = {"ok": False, "age_min": None}
            continue
        # DuckDB returns python datetime (naive UTC) or string; normalize
        if isinstance(ts, str): ts = datetime.fromisoformat(ts.replace("Z",""))
        age = (now - ts.replace(tzinfo=timezone.utc)).total_seconds() / 60.0
        out[tbl] = {"ok": age <= max_age_minutes, "age_min": round(age,1)}
    return out

def check_quorum(duck:str, season:int, week:int, *, min_odds_rows:int=10) -> dict:
    con = _con(duck)
    cnt = con.execute("SELECT count(*) c FROM odds_snapshots WHERE season=? AND week=?", [season, week]).fetchone()[0]
    return {"odds_rows": cnt, "ok": cnt >= min_odds_rows}
