from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from ..schemas.pick import Pick
from ..schemas.run_manifest import RunManifest


@dataclass(slots=True)
class RunSummary:
    run_id: str
    season: int
    week: int
    profile: str
    started_at: datetime
    settings: Mapping[str, Any]
    pick_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "season": self.season,
            "week": self.week,
            "profile": self.profile,
            "started_at": self.started_at.isoformat(),
            "settings": dict(self.settings),
            "pick_count": self.pick_count,
        }


class DuckDBStore:
    """Simple DuckDB-backed persistence for pipeline runs and picks."""

    def __init__(self, db_path: str) -> None:
        self.path = Path(db_path)
        self._con: duckdb.DuckDBPyConnection | None = None

    # ------------------------------------------------------------------
    # connection + schema helpers
    # ------------------------------------------------------------------
    def connect(self) -> duckdb.DuckDBPyConnection:
        if self._con is None:
            if self.path.suffix and not self.path.name:
                raise ValueError(f"Invalid DuckDB path: {self.path}")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._con = duckdb.connect(str(self.path))
            self._ensure_schema(self._con)
        return self._con

    def close(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None

    @staticmethod
    def _ensure_schema(con: duckdb.DuckDBPyConnection) -> None:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS runs(
                run_id TEXT PRIMARY KEY,
                season INTEGER,
                week INTEGER,
                profile TEXT,
                settings_json JSON,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        con.execute(
            """
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
            );
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots(
                run_id TEXT,
                stage TEXT,
                payload JSON,
                ts_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(run_id, stage)
            );
            """
        )
        con.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_picks_run ON picks(run_id);
            """
        )

    # ------------------------------------------------------------------
    # run + pick persistence
    # ------------------------------------------------------------------
    def write_run(self, manifest: RunManifest, *, started_at: datetime | None = None) -> None:
        con = self.connect()
        ts = (started_at or datetime.now(UTC)).replace(tzinfo=None)
        con.execute(
            """
            INSERT OR REPLACE INTO runs(run_id, season, week, profile, settings_json, started_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            [
                manifest.run_id,
                manifest.season,
                manifest.week,
                manifest.profile,
                json.dumps(manifest.settings_json, default=str),
                ts,
            ],
        )

    def write_picks(self, picks: Iterable[Pick]) -> int:
        picks_iter = list(picks)
        if not picks_iter:
            return 0
        con = self.connect()
        run_ids = {p.run_id for p in picks_iter}
        if len(run_ids) != 1:
            raise ValueError("All picks must belong to the same run_id")
        (run_id,) = tuple(run_ids)
        con.execute("DELETE FROM picks WHERE run_id = ?;", [run_id])
        con.executemany(
            """
            INSERT INTO picks(
                run_id, game_id, season, week, market, side, line, price_american,
                model_prob, fair_price_american, ev_percent, z_score, robust_ev_percent,
                grade, kelly_fraction, stake_units, book, ts_created
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    p.run_id,
                    p.game_id,
                    p.season,
                    p.week,
                    p.market.value,
                    p.side,
                    p.line,
                    p.price_american,
                    p.model_prob,
                    p.fair_price_american,
                    p.ev_percent,
                    p.z_score,
                    p.robust_ev_percent,
                    p.grade.value,
                    p.kelly_fraction,
                    p.stake_units,
                    p.book,
                    p.ts_created.replace(tzinfo=None),
                )
                for p in picks_iter
            ],
        )
        return len(picks_iter)

    # ------------------------------------------------------------------
    # run queries
    # ------------------------------------------------------------------
    def get_run_manifest(self, run_id: str) -> RunManifest | None:
        con = self.connect()
        row = con.execute(
            "SELECT run_id, season, week, profile, settings_json FROM runs WHERE run_id = ?;",
            [run_id],
        ).fetchone()
        if row is None:
            return None
        settings_json = json.loads(row[4]) if row[4] is not None else {}
        return RunManifest(
            run_id=row[0],
            season=int(row[1]),
            week=int(row[2]),
            profile=str(row[3]),
            settings_json=settings_json,
        )

    def list_runs(self, limit: int = 20) -> list[RunSummary]:
        con = self.connect()
        rows = con.execute(
            """
            SELECT
                r.run_id,
                r.season,
                r.week,
                r.profile,
                r.started_at,
                r.settings_json,
                COUNT(p.run_id) AS pick_count
            FROM runs r
            LEFT JOIN picks p ON p.run_id = r.run_id
            GROUP BY r.run_id, r.season, r.week, r.profile, r.started_at, r.settings_json
            ORDER BY r.started_at DESC
            LIMIT ?;
            """,
            [limit],
        ).fetchall()
        summaries: list[RunSummary] = []
        for row in rows:
            summaries.append(
                RunSummary(
                    run_id=str(row[0]),
                    season=int(row[1]),
                    week=int(row[2]),
                    profile=str(row[3]),
                    started_at=_coerce_datetime(row[4]),
                    settings=json.loads(row[5]) if row[5] else {},
                    pick_count=int(row[6] or 0),
                )
            )
        return summaries

    def latest_run(self) -> RunSummary | None:
        runs = self.list_runs(limit=1)
        return runs[0] if runs else None

    def fetch_picks(self, run_id: str) -> list[Pick]:
        con = self.connect()
        rows = con.execute(
            """
            SELECT run_id, game_id, season, week, market, side, line, price_american,
                   model_prob, fair_price_american, ev_percent, z_score, robust_ev_percent,
                   grade, kelly_fraction, stake_units, book, ts_created
            FROM picks WHERE run_id = ? ORDER BY game_id;
            """,
            [run_id],
        ).fetchall()
        picks: list[Pick] = []
        for row in rows:
            picks.append(
                Pick(
                    run_id=str(row[0]),
                    game_id=str(row[1]),
                    season=int(row[2]),
                    week=int(row[3]),
                    market=row[4],
                    side=str(row[5]),
                    line=float(row[6]) if row[6] is not None else None,
                    price_american=int(row[7]),
                    model_prob=float(row[8]),
                    fair_price_american=int(row[9]),
                    ev_percent=float(row[10]),
                    z_score=float(row[11]),
                    robust_ev_percent=float(row[12]),
                    grade=row[13],
                    kelly_fraction=float(row[14]),
                    stake_units=float(row[15]),
                    book=str(row[16]),
                    ts_created=_coerce_datetime(row[17]),
                )
            )
        return picks

    def iter_run_ids(self) -> Iterator[str]:
        con = self.connect()
        rows = con.execute("SELECT run_id FROM runs ORDER BY started_at DESC;").fetchall()
        return (str(r[0]) for r in rows)

    def status_summary(self) -> dict[str, Any]:
        con = self.connect()
        run_count = con.execute("SELECT COUNT(*) FROM runs;").fetchone()[0]
        pick_count = con.execute("SELECT COUNT(*) FROM picks;").fetchone()[0]
        latest = self.latest_run()
        return {
            "runs": int(run_count or 0),
            "picks": int(pick_count or 0),
            "latest_run": latest.to_dict() if latest else None,
        }

    # ------------------------------------------------------------------
    # snapshot helpers
    # ------------------------------------------------------------------
    def save_snapshot(self, run_id: str, stage: str, payload: Mapping[str, Any]) -> None:
        con = self.connect()
        con.execute(
            """
            INSERT OR REPLACE INTO snapshots(run_id, stage, payload, ts_created)
            VALUES (?, ?, ?, ?);
            """,
            [
                run_id,
                stage,
                json.dumps(dict(payload), default=str),
                datetime.now(UTC).replace(tzinfo=None),
            ],
        )

    def get_snapshot(self, run_id: str, stage: str) -> Mapping[str, Any] | None:
        con = self.connect()
        row = con.execute(
            "SELECT payload FROM snapshots WHERE run_id = ? AND stage = ?;",
            [run_id, stage],
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0]) if row[0] else {}

    def list_snapshots(self, run_id: str) -> list[str]:
        con = self.connect()
        rows = con.execute(
            "SELECT stage FROM snapshots WHERE run_id = ? ORDER BY stage;", [run_id]
        ).fetchall()
        return [str(r[0]) for r in rows]


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return (
            value.replace(tzinfo=UTC)
            if value.tzinfo is None
            else value.astimezone(UTC)
        )
    return datetime.fromisoformat(str(value)).replace(tzinfo=UTC)
