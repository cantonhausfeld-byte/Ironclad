from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ironclad.persist.duckdb_connector import (
    connect,
    latest_snapshot_ts,
    write_picks,
    write_picks_sized,
    write_run,
)
from ironclad.runner.run_board import synthesize_picks
from ironclad.schemas.run_manifest import RunManifest
from ironclad.settings import settings


@dataclass
class RunContext:
    run_id: str
    season: int
    week: int
    profile: str
    settings_json: dict[str, Any]

    def manifest(self) -> RunManifest:
        return RunManifest(
            run_id=self.run_id,
            season=self.season,
            week=self.week,
            profile=self.profile,
            settings_json=self.settings_json,
        )


def _serialize_lineage(raw: dict[str, Any]) -> dict[str, Any]:
    serialised: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            else:
                value = value.astimezone(UTC)
            serialised[key] = value.isoformat()
        elif value is None:
            serialised[key] = None
        else:
            serialised[key] = str(value)
    return serialised


def _coerce_cols(
    df: pd.DataFrame,
    run_id: str,
    season: int,
    week: int,
    *,
    lineage: dict[str, Any] | None = None,
) -> pd.DataFrame:
    need = [
        "run_id",
        "season",
        "week",
        "game_id",
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
        "snapshot_odds_ts",
        "snapshot_inj_ts",
        "snapshot_wx_ts",
    ]
    out = df.copy()
    if "run_id" not in out.columns:
        out["run_id"] = run_id
    if "season" not in out.columns:
        out["season"] = season
    if "week" not in out.columns:
        out["week"] = week
    if "ts_created" not in out.columns:
        out["ts_created"] = datetime.now(UTC).isoformat()

    out["snapshot_odds_ts"] = None
    out["snapshot_inj_ts"] = None
    out["snapshot_wx_ts"] = None
    if lineage:
        out["snapshot_odds_ts"] = lineage.get("odds_snapshots")
        out["snapshot_inj_ts"] = lineage.get("injury_snapshots")
        out["snapshot_wx_ts"] = lineage.get("weather_snapshots")

    for col in need:
        if col not in out.columns:
            out[col] = None
    return out[need]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a synthetic picks run to DuckDB.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--sized-csv", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    ctx = RunContext(
        run_id=run_id,
        season=args.season,
        week=args.week,
        profile=settings.profile,
        settings_json={"demo": settings.demo_enabled()},
    )
    con = connect(settings.duckdb_path)
    try:
        write_run(con, ctx.manifest())
        raw_lineage = latest_snapshot_ts(con, args.season, args.week)
        lineage = _serialize_lineage(raw_lineage)

        picks = synthesize_picks(ctx.run_id, ctx.season, ctx.week)
        base = pd.DataFrame([p.model_dump() for p in picks])
        base2 = _coerce_cols(base, ctx.run_id, ctx.season, ctx.week, lineage=lineage)
        if not base2.empty:
            write_picks(con, base2.to_dict("records"))

        sized_csv = args.sized_csv
        if sized_csv:
            sized = pd.read_csv(sized_csv)
            if "run_id" not in sized.columns:
                sized["run_id"] = ctx.run_id
            if "season" not in sized.columns:
                sized["season"] = ctx.season
            if "week" not in sized.columns:
                sized["week"] = ctx.week
            if "ts_created" not in sized.columns:
                if not base2.empty and len(base2) == len(sized):
                    sized["ts_created"] = list(base2["ts_created"])
                elif not base2.empty:
                    sized["ts_created"] = base2["ts_created"].iloc[0]
                else:
                    sized["ts_created"] = datetime.now(UTC).isoformat()
            lineage_map = {
                "snapshot_odds_ts": "odds_snapshots",
                "snapshot_inj_ts": "injury_snapshots",
                "snapshot_wx_ts": "weather_snapshots",
            }
            for col in ("snapshot_odds_ts", "snapshot_inj_ts", "snapshot_wx_ts"):
                if col not in sized.columns:
                    if not base2.empty:
                        sized[col] = base2[col].iloc[0]
                    elif lineage:
                        sized[col] = lineage.get(lineage_map[col])
                    else:
                        sized[col] = None
            write_picks_sized(con, sized.to_dict("records"))

        print(
            f"Recorded run {ctx.run_id} for season={ctx.season} week={ctx.week}"
            f" ({len(base2)} picks)"
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
