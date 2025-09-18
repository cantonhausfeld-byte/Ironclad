from __future__ import annotations

import os
from typing import Iterable, Sequence

import duckdb
import pandas as pd

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
    "odds_snapshots": """
    CREATE TABLE IF NOT EXISTS odds_snapshots(
        ts_utc TIMESTAMP,
        book TEXT,
        game_id TEXT,
        market TEXT,
        line DOUBLE,
        price_american INTEGER,
        source TEXT,
        season INTEGER,
        week INTEGER
    );""",
    "injury_snapshots": """
    CREATE TABLE IF NOT EXISTS injury_snapshots(
        ts_utc TIMESTAMP,
        player_id TEXT,
        player_name TEXT,
        team TEXT,
        status TEXT,
        prob_active DOUBLE,
        game_id TEXT,
        season INTEGER,
        week INTEGER
    );""",
    "weather_snapshots": """
    CREATE TABLE IF NOT EXISTS weather_snapshots(
        ts_utc TIMESTAMP,
        venue_id TEXT,
        game_id TEXT,
        temp_f DOUBLE,
        wind_mph DOUBLE,
        precip_prob DOUBLE,
        season INTEGER,
        week INTEGER
    );""",
}

PICKS_COLUMNS: Sequence[str] = (
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
)


def connect(db_path: str):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = duckdb.connect(db_path)
    for ddl in DDL.values():
        con.execute(ddl)
    return con


def _normalize_picks(picks: Iterable[Pick] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(picks, pd.DataFrame):
        df = picks.copy()
    else:
        rows = []
        for p in picks:
            if hasattr(p, "model_dump"):
                rows.append(p.model_dump())
            else:
                rows.append(dict(p))  # type: ignore[arg-type]
        if not rows:
            return pd.DataFrame(columns=PICKS_COLUMNS)
        df = pd.DataFrame(rows)
    for col in PICKS_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[list(PICKS_COLUMNS)]


def write_run(con, manifest: RunManifest):
    con.execute(
        "INSERT OR REPLACE INTO runs(run_id, season, week, profile, settings_json) VALUES (?, ?, ?, ?, ?);",
        [manifest.run_id, manifest.season, manifest.week, manifest.profile, manifest.settings_json],
    )


def write_picks(con, picks: Iterable[Pick] | pd.DataFrame):
    df = _normalize_picks(picks)
    if df.empty:
        return
    con.register("picks_df", df)
    con.execute("INSERT INTO picks SELECT * FROM picks_df")
    con.unregister("picks_df")


def write_picks_sized(con, picks_df: pd.DataFrame):
    if picks_df is None or picks_df.empty:
        return
    con.register("picks_sized_df", picks_df)
    con.execute(
        "CREATE TABLE IF NOT EXISTS picks_sized AS SELECT * FROM picks_sized_df WHERE 1=0"
    )
    con.execute("INSERT INTO picks_sized SELECT * FROM picks_sized_df")
    con.unregister("picks_sized_df")


def write_odds_snapshots(con, df: pd.DataFrame):
    if df is None or df.empty:
        return
    con.register("odds_snapshots_df", df)
    con.execute("INSERT INTO odds_snapshots SELECT * FROM odds_snapshots_df")
    con.unregister("odds_snapshots_df")


def write_injury_snapshots(con, df: pd.DataFrame):
    if df is None or df.empty:
        return
    con.register("injury_snapshots_df", df)
    con.execute("INSERT INTO injury_snapshots SELECT * FROM injury_snapshots_df")
    con.unregister("injury_snapshots_df")


def write_weather_snapshots(con, df: pd.DataFrame):
    if df is None or df.empty:
        return
    con.register("weather_snapshots_df", df)
    con.execute("INSERT INTO weather_snapshots SELECT * FROM weather_snapshots_df")
    con.unregister("weather_snapshots_df")
