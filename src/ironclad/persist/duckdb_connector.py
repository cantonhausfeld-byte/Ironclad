from __future__ import annotations

import json
from pathlib import Path

import duckdb
from pandas import DataFrame

DDL = """
CREATE TABLE IF NOT EXISTS runs(
  run_id TEXT PRIMARY KEY,
  season INT, week INT, profile TEXT, started_at TIMESTAMP, settings_json JSON
);
CREATE TABLE IF NOT EXISTS picks(
  run_id TEXT, game_id TEXT, season INT, week INT, market TEXT, side TEXT, line DOUBLE,
  price_american INT, model_prob DOUBLE, fair_price_american INT, ev_percent DOUBLE,
  z_score DOUBLE, robust_ev_percent DOUBLE, grade TEXT, kelly_fraction DOUBLE,
  stake_units DOUBLE, book TEXT, ts_created TIMESTAMP
);
"""


def connect(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(path)
    con.execute(DDL)
    return con


def write_run(con, manifest: dict) -> None:
    con.execute(
        "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, now(), ?)",
        [
            manifest["run_id"],
            manifest["season"],
            manifest["week"],
            manifest.get("profile", "local"),
            json.dumps(manifest.get("settings_json", {})),
        ],
    )


def write_picks(con, df: DataFrame) -> None:
    con.register("picks_df", df)
    con.execute("INSERT INTO picks SELECT * FROM picks_df")
    con.unregister("picks_df")
