import sys
from pathlib import Path

# Ensure the src directory is on the path when running from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import click
from rich import print as rprint

from ironclad.runner.run_preslate import run as run_preslate
from ironclad.settings import get_settings


@click.group()
def cli() -> None:
    """Ironclad command line interface."""


@cli.command("config-validate")
def config_validate() -> None:
    settings = get_settings()
    rprint(
        {
            "TZ": settings.TZ,
            "SEASON": settings.SEASON,
            "WEEK": settings.WEEK,
            "DUCKDB": settings.DUCKDB__PATH,
        }
    )


@cli.command("run-preslate")
def cmd_run_preslate() -> None:
    run_preslate()


if __name__ == "__main__":
    cli()
