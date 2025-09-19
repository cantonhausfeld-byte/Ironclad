from __future__ import annotations

import json

import typer

from ironclad.persist.duckdb_store import DuckDBStore
from ironclad.runner.context import RunContext
from ironclad.runner.pipeline import run_pipeline
from ironclad.runner.replay import replay_run
from ironclad.settings import settings

app = typer.Typer(help="Ironclad pipeline CLI")


def _store(path: str | None = None) -> DuckDBStore:
    return DuckDBStore(path or settings.duckdb_path)


@app.command()
def run(
    *,
    profile: str | None = typer.Option(None, "--profile", help="Profile override"),
    season: int = typer.Option(..., help="Season (e.g. 2025)"),
    week: int = typer.Option(..., help="Week of season"),
    snapshot_from: str | None = typer.Option(
        None, "--snapshot-from", help="Re-use snapshots from run"
    ),
    db_path: str | None = typer.Option(None, "--db-path", help="Override DuckDB path"),
) -> None:
    """Run the pipeline end-to-end."""

    context = RunContext.new(season=season, week=week, profile=profile)
    if snapshot_from:
        context.use_snapshots = True
        context.snapshot_source_run_id = snapshot_from
        context.params["snapshot_source_run_id"] = snapshot_from
        context.params["use_snapshots"] = True

    store = _store(db_path)
    result = run_pipeline(context, store=store)
    typer.echo(
        json.dumps(
            {
                "run_id": result.context.run_id,
                "profile": result.context.profile,
                "season": result.context.season,
                "week": result.context.week,
                "duckdb_path": str(store.path),
                "pick_count": len(result.picks),
                "guardrails": result.guardrails,
            },
            indent=2,
        )
    )


@app.command()
def rerun(
    run_id: str = typer.Argument(..., help="Run ID to replay"),
    profile: str | None = typer.Option(None, "--profile", help="Override profile for replay"),
    db_path: str | None = typer.Option(None, "--db-path", help="Override DuckDB path"),
) -> None:
    """Replay an existing run using stored snapshots."""

    try:
        result = replay_run(run_id, store=_store(db_path), profile=profile)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(
        json.dumps(
            {
                "run_id": result.context.run_id,
                "source_run_id": run_id,
                "pick_count": len(result.picks),
                "guardrails": result.guardrails,
            },
            indent=2,
        )
    )


@app.command()
def status(
    limit: int = typer.Option(5, help="Number of recent runs to show"),
    db_path: str | None = typer.Option(None, "--db-path", help="Override DuckDB path"),
) -> None:
    """Show high-level run status."""

    store = _store(db_path)
    summary = store.status_summary()
    runs = [run.to_dict() for run in store.list_runs(limit=limit)]
    typer.echo(
        json.dumps(
            {
                "profile": settings.profile,
                "duckdb_path": str(store.path),
                "summary": summary,
                "runs": runs,
            },
            indent=2,
        )
    )


@app.command()
def picks(
    run_id: str = typer.Argument(..., help="Run ID"),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Output as JSON"),
    db_path: str | None = typer.Option(None, "--db-path", help="Override DuckDB path"),
) -> None:
    """Display picks for a run."""

    store = _store(db_path)
    picks = store.fetch_picks(run_id)
    if not picks:
        typer.echo(f"No picks found for run {run_id}")
        raise typer.Exit(code=0)

    if json_output:
        typer.echo(json.dumps([pick.model_dump(mode="json") for pick in picks], indent=2))
    else:
        for pick in picks:
            typer.echo(
                f"{pick.run_id} | {pick.market.value} {pick.side} "
                f"{pick.price_american} (EV {pick.ev_percent:.2f}%)"
            )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
