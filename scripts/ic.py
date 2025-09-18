import click
from ironclad.runner.run_preslate import run as run_preslate
from ironclad.settings import get_settings
from ironclad.logging import setup_logging
from rich import print as rprint

@click.group()
def cli():
    "Ironclad control CLI"

@cli.command("config-validate")
def config_validate():
    s = get_settings()
    rprint({"TZ": s.TZ, "SEASON": s.SEASON, "WEEK": s.WEEK, "DUCKDB": s.DUCKDB__PATH})

@cli.command("run-preslate")
def cmd_run_preslate():
    log = setup_logging()
    log.info("preslate.start")
    try:
        run_preslate()
        log.info("preslate.success")
    except Exception as e:
        log.exception("preslate.error", err=str(e))
        raise

if __name__ == "__main__":
    cli()
