
import os
from typing import Iterable, Mapping, Sequence

import duckdb
import pandas as pd

from ..schemas.pick import Pick
from ..schemas.run_manifest import RunManifest

DDL = {
    "runs": '''
    CREATE TABLE IF NOT EXISTS runs(
        run_id TEXT PRIMARY KEY,
        season INTEGER,
        week INTEGER,
        profile TEXT,
        settings_json JSON,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );''',
    "picks": '''
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
    );'''
}

def connect(db_path: str):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    con = duckdb.connect(db_path)
    for ddl in DDL.values():
        con.execute(ddl)
    return con

def _manifest_to_dict(manifest: RunManifest | Mapping[str, object]) -> dict[str, object]:
    if isinstance(manifest, RunManifest):
        data = manifest.model_dump()
    elif isinstance(manifest, Mapping):
        data = dict(manifest)
    else:
        raise TypeError("manifest must be RunManifest or mapping")
    data.setdefault("profile", "cli")
    data.setdefault("settings_json", {})
    return data


def write_run(con, manifest: RunManifest | Mapping[str, object]):
    data = _manifest_to_dict(manifest)
    con.execute(
        "INSERT OR REPLACE INTO runs(run_id, season, week, profile, settings_json) VALUES (?, ?, ?, ?, ?);",
        [data["run_id"], data["season"], data["week"], data["profile"], data["settings_json"]]
    )


def _normalize_pick_rows(picks: Iterable[Pick] | pd.DataFrame | Sequence[Mapping[str, object]]):
    if isinstance(picks, pd.DataFrame):
        return picks.to_dict(orient="records")

    rows: list[dict[str, object]] = []
    for p in picks:  # type: ignore[assignment]
        if isinstance(p, Pick):
            rows.append(p.model_dump())
        elif isinstance(p, Mapping):
            rows.append(dict(p))
        else:
            raise TypeError("Unsupported pick row type: %r" % (type(p),))
    return rows


def write_picks(con, picks: Iterable[Pick] | pd.DataFrame | Sequence[Mapping[str, object]]):
    rows = _normalize_pick_rows(picks)
    if not rows:
        return
    os.makedirs("out/picks", exist_ok=True)
    tuples = [
        (
            r["run_id"], r["game_id"], r["season"], r["week"], r["market"], r["side"], r["line"],
            r["price_american"], r["model_prob"], r["fair_price_american"], r["ev_percent"], r["z_score"],
            r["robust_ev_percent"], r["grade"], r["kelly_fraction"], r["stake_units"], r["book"], r["ts_created"]
        )
        for r in rows
    ]
    con.executemany(
        "INSERT INTO picks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        tuples,
    )
