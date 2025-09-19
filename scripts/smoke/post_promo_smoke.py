from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ironclad.persist.duckdb_store import DuckDBStore
from ironclad.runner.context import RunContext
from ironclad.runner.pipeline import run_pipeline
from ironclad.settings import settings

REPORT_DIR = Path("out/reports")


def _write_reports(payload: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    stem = REPORT_DIR / f"smoke_{payload['run_id']}_{timestamp}"

    json_path = stem.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)

    md_path = stem.with_suffix(".md")
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write("# Post-promo Smoke Report\n\n")
        fh.write(f"* Run ID: `{payload['run_id']}`\n")
        fh.write(f"* Picks: {payload['pick_count']}\n")
        fh.write(f"* Guardrails: {len(payload['guardrails'])}\n")
        fh.write("\n## Guardrail Results\n")
        for check in payload["guardrails"]:
            status = "✅" if check.get("passed") else "❌"
            fh.write(f"- {status} **{check.get('name')}**\n")
    print(f"Smoke report written to {json_path}")


def main(season: int = 2025, week: int = 1, profile: str | None = None) -> None:
    profile_value = profile or settings.profile
    context = RunContext.new(season=season, week=week, profile=profile_value)
    store = DuckDBStore(settings.duckdb_path)

    print(f"[harvest] profile={profile_value} season={season} week={week}")
    result = run_pipeline(context, store=store)

    payload = {
        "run_id": result.context.run_id,
        "profile": result.context.profile,
        "season": result.context.season,
        "week": result.context.week,
        "duckdb_path": str(store.path),
        "pick_count": len(result.picks),
        "guardrails": result.guardrails,
    }
    _write_reports(payload)


def cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the post-promo smoke pipeline")
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--profile", type=str, default=None)
    args = parser.parse_args()
    main(season=args.season, week=args.week, profile=args.profile)


if __name__ == "__main__":
    cli()
