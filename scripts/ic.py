
"""Ironclad helper CLI."""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import click
import pandas as pd

from ironclad.persist.duckdb_connector import connect, write_picks, write_run
from ironclad.runner.run_board import synthesize_picks
from ironclad.schemas.run_manifest import RunManifest
from ironclad.settings import settings

DEFAULT_SEASON = 2025
DEFAULT_WEEK = 1
PICKS_DIR = Path("out/picks")


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise click.BadParameter(f"Environment variable {name} must be an integer") from exc


@click.group()
def cli() -> None:
    """Entry point for Ironclad utility commands."""


@cli.command("run-preslate")
@click.option(
    "--season",
    type=int,
    default=None,
    help="Season to run (defaults to $SEASON or 2025)",
)
@click.option(
    "--week",
    type=int,
    default=None,
    help="Week to run (defaults to $WEEK or 1)",
)
def run_preslate(season: int | None, week: int | None) -> None:
    """Generate a pre-slate picks CSV using the run_board synthesizer."""

    season = season if season is not None else _env_int("SEASON", DEFAULT_SEASON)
    week = week if week is not None else _env_int("WEEK", DEFAULT_WEEK)

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    manifest = RunManifest(
        run_id=run_id,
        season=season,
        week=week,
        profile=settings.profile,
        settings_json={"demo": settings.demo_enabled()},
    )

    picks = synthesize_picks(run_id, season, week)
    if not picks:
        click.echo("No picks generated.")
        return

    con = connect(settings.duckdb_path)
    write_run(con, manifest)
    write_picks(con, picks)

    df = pd.DataFrame([p.model_dump() for p in picks])
    PICKS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    csv_path = PICKS_DIR / f"{timestamp}_picks.csv"
    df.to_csv(csv_path, index=False)
    click.echo(f"Run {run_id} wrote {len(df)} picks -> {csv_path}")


def main(argv: Iterable[str] | None = None) -> None:
    """CLI entrypoint wrapper for Click."""

    cli.main(args=list(argv) if argv is not None else None, prog_name="ic")


if __name__ == "__main__":
    main(sys.argv[1:])
