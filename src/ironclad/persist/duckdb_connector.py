import os
from collections.abc import Iterable, Mapping
from typing import Any

import duckdb  # type: ignore[import-untyped]

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
        ts_created TIMESTAMP,
        snapshot_odds_ts TIMESTAMP,
        snapshot_inj_ts TIMESTAMP,
        snapshot_wx_ts TIMESTAMP
    );""",
    "picks_sized": """
    CREATE TABLE IF NOT EXISTS picks_sized(
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
        ts_created TIMESTAMP,
        snapshot_odds_ts TIMESTAMP,
        snapshot_inj_ts TIMESTAMP,
        snapshot_wx_ts TIMESTAMP
    );""",
}


def connect(db_path: str):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = duckdb.connect(db_path)
    for ddl in DDL.values():
        con.execute(ddl)
    con.execute("ALTER TABLE picks ADD COLUMN IF NOT EXISTS snapshot_odds_ts TIMESTAMP")
    con.execute("ALTER TABLE picks ADD COLUMN IF NOT EXISTS snapshot_inj_ts TIMESTAMP")
    con.execute("ALTER TABLE picks ADD COLUMN IF NOT EXISTS snapshot_wx_ts TIMESTAMP")
    con.execute("ALTER TABLE picks_sized ADD COLUMN IF NOT EXISTS snapshot_odds_ts TIMESTAMP")
    con.execute("ALTER TABLE picks_sized ADD COLUMN IF NOT EXISTS snapshot_inj_ts TIMESTAMP")
    con.execute("ALTER TABLE picks_sized ADD COLUMN IF NOT EXISTS snapshot_wx_ts TIMESTAMP")
    return con


def write_run(con, manifest: RunManifest):
    con.execute(
        (
            "INSERT OR REPLACE INTO runs(run_id, season, week, profile, settings_json) "
            "VALUES (?, ?, ?, ?, ?);"
        ),
        [manifest.run_id, manifest.season, manifest.week, manifest.profile, manifest.settings_json],
    )


def _normalise_pick(row: Pick | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(row, Pick):
        data = row.model_dump()
    else:
        data = dict(row)
    data.setdefault("snapshot_odds_ts", None)
    data.setdefault("snapshot_inj_ts", None)
    data.setdefault("snapshot_wx_ts", None)
    return data


def write_picks(con, picks: Iterable[Pick | Mapping[str, Any]]):
    normalised = [_normalise_pick(p) for p in picks]
    if not normalised:
        return
    con.executemany(
        "INSERT INTO picks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        [
            (
                r["run_id"],
                r["game_id"],
                r["season"],
                r["week"],
                r["market"],
                r["side"],
                r.get("line"),
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
                r.get("snapshot_odds_ts"),
                r.get("snapshot_inj_ts"),
                r.get("snapshot_wx_ts"),
            )
            for r in normalised
        ],
    )


def write_picks_sized(con, rows: Iterable[Mapping[str, Any]]):
    data = [_normalise_pick(r) for r in rows]
    if not data:
        return
    con.executemany(
        (
            "INSERT INTO picks_sized VALUES ("
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        ),
        [
            (
                r["run_id"],
                r["game_id"],
                r["season"],
                r["week"],
                r["market"],
                r["side"],
                r.get("line"),
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
                r.get("snapshot_odds_ts"),
                r.get("snapshot_inj_ts"),
                r.get("snapshot_wx_ts"),
            )
            for r in data
        ],
    )


def latest_snapshot_ts(con, season: int, week: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for tbl in ("odds_snapshots", "injury_snapshots", "weather_snapshots"):
        try:
            row = con.execute(
                f"SELECT max(ts_utc) AS ts FROM {tbl} WHERE season=? AND week=?",
                [season, week],
            ).fetchone()
        except duckdb.CatalogException:
            out[tbl] = None
            continue
        out[tbl] = row[0] if row else None
    return out
