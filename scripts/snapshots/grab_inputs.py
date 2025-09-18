from __future__ import annotations

import csv
from dataclasses import asdict, fields
from pathlib import Path
from typing import Iterable, TypeVar

import click

from ironclad.services.vendor_client import InjuryRow, OddsRow, WeatherRow, get_vendor

RowT = TypeVar("RowT", OddsRow, InjuryRow, WeatherRow)


def _write_csv(path: Path, rows: Iterable[RowT], row_type: type[RowT]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [f.name for f in fields(row_type)]
    rows = list(rows)
    with path.open("w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _log_snapshot(name: str, rows: Iterable[RowT]) -> list[RowT]:
    rows = list(rows)
    click.echo(f"Fetched {len(rows)} {name} rows")
    return rows


@click.command()
@click.option("--run_id", required=True, help="Run identifier for the snapshots")
@click.option("--season", type=int, required=True)
@click.option("--week", type=int, required=True)
@click.option(
    "--out-dir",
    type=click.Path(path_type=Path),
    default=Path("out/snapshots"),
    show_default=True,
)
def main(run_id: str, season: int, week: int, out_dir: Path) -> None:
    """Fetch odds/injuries/weather snapshots for a given run."""

    vendor = get_vendor()

    odds_rows = _log_snapshot(
        "odds", vendor.odds_snapshot(run_id, season, week)
    )
    injury_rows = _log_snapshot(
        "injury", vendor.injuries_snapshot(run_id, season, week)
    )
    weather_rows = _log_snapshot(
        "weather", vendor.weather_snapshot(run_id, season, week)
    )

    run_dir = out_dir / run_id
    _write_csv(run_dir / "odds.csv", odds_rows, OddsRow)
    _write_csv(run_dir / "injuries.csv", injury_rows, InjuryRow)
    _write_csv(run_dir / "weather.csv", weather_rows, WeatherRow)

    click.echo(f"Snapshots written to {run_dir}")


if __name__ == "__main__":
    main()
