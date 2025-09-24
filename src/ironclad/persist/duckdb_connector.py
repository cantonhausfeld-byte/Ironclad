
"""DuckDB persistence helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

import duckdb

from ..schemas.pick import Pick
from ..schemas.run_manifest import RunManifest

PICK_COLUMNS: Sequence[str] = (
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
    "picks_sized": """
    CREATE TABLE IF NOT EXISTS picks_sized(
        sized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        input_csv TEXT,
        output_csv TEXT,
        sizing_config_json JSON,
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


def _pick_row(row: Mapping[str, object]) -> tuple[object, ...]:
    """Return a tuple matching the order of :data:`PICK_COLUMNS`."""

    return tuple(row.get(column) for column in PICK_COLUMNS)


def connect(db_path: str):
    """Open a DuckDB connection, ensuring the destination path exists."""

    db_path_obj = Path(db_path)
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path_obj))
    for ddl in DDL.values():
        con.execute(ddl)
    return con


def write_run(con, manifest: RunManifest) -> None:
    """Persist run metadata into DuckDB."""

    con.execute(
        (
            "INSERT OR REPLACE INTO runs(run_id, season, week, profile, settings_json) "
            "VALUES (?, ?, ?, ?, ?);"
        ),
        [manifest.run_id, manifest.season, manifest.week, manifest.profile, manifest.settings_json],
    )


def write_picks(con, picks: Iterable[Pick]) -> None:
    """Persist pick rows into DuckDB."""

    rows = [p.model_dump() for p in picks]
    if not rows:
        return

    con.executemany(
        "INSERT INTO picks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        [_pick_row(r) for r in rows],
    )


def write_sized_picks(
    con,
    rows: Iterable[Mapping[str, object]],
    *,
    input_csv: str,
    output_csv: str,
    sizing_config: Mapping[str, object] | None = None,
) -> None:
    """Persist sized pick rows into DuckDB."""

    rows = list(rows)
    if not rows:
        return

    payload = [
        (
            input_csv,
            output_csv,
            json.dumps(dict(sizing_config or {})),
            *_pick_row(row),
        )
        for row in rows
    ]

    con.executemany(
        """
        INSERT INTO picks_sized (
            input_csv,
            output_csv,
            sizing_config_json,
            run_id,
            game_id,
            season,
            week,
            market,
            side,
            line,
            price_american,
            model_prob,
            fair_price_american,
            ev_percent,
            z_score,
            robust_ev_percent,
            grade,
            kelly_fraction,
            stake_units,
            book,
            ts_created
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        payload,
    )
