from __future__ import annotations

from datetime import UTC, datetime, timedelta

import duckdb

from ironclad.analytics.data_quality import check_freshness, check_quorum
from ironclad.persist.duckdb_connector import latest_snapshot_ts


def _setup_snapshots(db_path: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(db_path)
    for table in ("odds_snapshots", "injury_snapshots", "weather_snapshots"):
        con.execute(f"CREATE TABLE {table} (season INTEGER, week INTEGER, ts_utc TIMESTAMP)")
    now = datetime.now(UTC)
    con.executemany(
        "INSERT INTO odds_snapshots VALUES (?, ?, ?)",
        [
            (2025, 1, (now - timedelta(minutes=5)).isoformat()),
            (2025, 1, (now - timedelta(minutes=2)).isoformat()),
        ],
    )
    con.execute(
        "INSERT INTO injury_snapshots VALUES (?, ?, ?)",
        (2025, 1, (now - timedelta(minutes=30)).isoformat()),
    )
    con.execute(
        "INSERT INTO weather_snapshots VALUES (?, ?, ?)",
        (2025, 1, (now - timedelta(hours=6)).isoformat()),
    )
    return con


def test_check_freshness_and_quorum(tmp_path):
    path = tmp_path / "test.duckdb"
    con = _setup_snapshots(str(path))
    con.close()

    freshness = check_freshness(str(path), 2025, 1, max_age_minutes=180)
    assert freshness["odds_snapshots"]["ok"] is True
    assert freshness["injury_snapshots"]["ok"] is True
    assert freshness["weather_snapshots"]["ok"] is False
    assert freshness["weather_snapshots"]["age_min"] >= 180

    quorum = check_quorum(str(path), 2025, 1, min_odds_rows=2)
    assert quorum["ok"] is True
    assert quorum["odds_rows"] == 2


def test_latest_snapshot_ts_handles_missing_tables(tmp_path):
    path = tmp_path / "test.duckdb"
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE odds_snapshots (season INTEGER, week INTEGER, ts_utc TIMESTAMP)")
    con.execute(
        "INSERT INTO odds_snapshots VALUES (?, ?, ?)",
        (2025, 1, datetime.now(UTC).isoformat()),
    )

    lineage = latest_snapshot_ts(con, 2025, 1)
    assert lineage["odds_snapshots"] is not None
    assert lineage["injury_snapshots"] is None
    assert lineage["weather_snapshots"] is None
    con.close()
