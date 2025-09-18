from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import duckdb  # type: ignore[import-untyped]
from duckdb import DuckDBPyConnection  # type: ignore[import-untyped]

SNAPSHOT_TABLES: tuple[str, ...] = (
    "odds_snapshots",
    "injury_snapshots",
    "weather_snapshots",
)


def _resolve_connection(duck: DuckDBPyConnection | str) -> tuple[DuckDBPyConnection, bool]:
    if isinstance(duck, DuckDBPyConnection):
        return duck, False
    con = duckdb.connect(duck)
    return con, True


def _normalize_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        ts = value
    elif isinstance(value, str):
        try:
            ts = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:  # pragma: no cover - defensive branch
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts


def check_freshness(
    duck: DuckDBPyConnection | str,
    season: int,
    week: int,
    *,
    max_age_minutes: int = 180,
) -> dict[str, dict[str, Any]]:
    """Return freshness metadata for each snapshot table."""
    con, should_close = _resolve_connection(duck)
    now = datetime.now(UTC)
    result: dict[str, dict[str, Any]] = {}
    try:
        for table in SNAPSHOT_TABLES:
            entry: dict[str, Any] = {"ok": False, "age_min": None, "ts": None}
            try:
                row = con.execute(
                    f"SELECT max(ts_utc) AS ts FROM {table} WHERE season=? AND week=?",
                    [season, week],
                ).fetchone()
            except duckdb.CatalogException:
                entry["error"] = "missing_table"
            else:
                ts_value = _normalize_ts(row[0] if row else None)
                if ts_value is not None:
                    age_minutes = int(max((now - ts_value).total_seconds() // 60, 0))
                    entry["age_min"] = age_minutes
                    entry["ts"] = ts_value.isoformat()
                    entry["ok"] = age_minutes <= max_age_minutes
                else:
                    entry["age_min"] = None
                    entry["ts"] = None
                    entry["ok"] = False
            result[table] = entry
    finally:
        if should_close:
            con.close()
    return result


def check_quorum(
    duck: DuckDBPyConnection | str,
    season: int,
    week: int,
    *,
    min_odds_rows: int = 10,
) -> dict[str, Any]:
    """Ensure we have at least ``min_odds_rows`` rows in odds snapshots."""
    con, should_close = _resolve_connection(duck)
    try:
        count = 0
        try:
            row = con.execute(
                "SELECT count(*) FROM odds_snapshots WHERE season=? AND week=?",
                [season, week],
            ).fetchone()
            count = int(row[0]) if row else 0
        except duckdb.CatalogException:
            return {
                "ok": False,
                "odds_rows": 0,
                "threshold": min_odds_rows,
                "error": "missing_table",
            }
        return {"ok": count >= min_odds_rows, "odds_rows": count, "threshold": min_odds_rows}
    finally:
        if should_close:
            con.close()
