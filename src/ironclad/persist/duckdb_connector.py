import duckdb, os
from typing import Iterable
from ..schemas.pick import Pick
from ..schemas.run_manifest import RunManifest

DDL = {
    "runs": """
    CREATE TABLE IF NOT EXISTS runs(
        run_id TEXT PRIMARY KEY,
        season INTEGER,
        week INTEGER,
        profile TEXT,
        settings_json JSON,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""",
    "picks": """
    CREATE TABLE IF NOT EXISTS picks(
        run_id TEXT,
        game_id TEXT,
        season INTEGER,
        week INTEGER,
        market TEXT,
        side TEXT,
        line DOUBLE,
        price_american INTEGER,
        model_prob DOUBLE,
        fair_price_american INTEGER,
        ev_percent DOUBLE,
        z_score DOUBLE,
        robust_ev_percent DOUBLE,
        grade TEXT,
        kelly_fraction DOUBLE,
        stake_units DOUBLE,
        book TEXT,
        ts_created TIMESTAMP
    );""",
}


def connect(db_path: str):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = duckdb.connect(db_path)
    for ddl in DDL.values():
        con.execute(ddl)
    return con


def write_run(con, manifest: RunManifest):
    con.execute(
        "INSERT OR REPLACE INTO runs(run_id, season, week, profile, settings_json) VALUES (?, ?, ?, ?, ?);",
        [manifest.run_id, manifest.season, manifest.week, manifest.profile, manifest.settings_json],
    )


def write_picks(con, picks: Iterable[Pick]):
    rows = [p.model_dump() for p in picks]
    if not rows:
        return
    con.execute(
        "INSERT INTO picks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        [
            (
                r["run_id"],
                r["game_id"],
                r["season"],
                r["week"],
                r["market"],
                r["side"],
                r["line"],
                r["price_american"],
                r["model_prob"],
                r["fair_price_american"],
                r["ev_percent"],
                r["z_score"],
                r["robust_ev_percent"],
                r["grade"],
                r["kelly_fraction"],
                r["stake_units"],
                r["book"],
                r["ts_created"],
            )
            for r in rows
        ],
    )
