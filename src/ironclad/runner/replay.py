from __future__ import annotations

from ..persist.duckdb_store import DuckDBStore
from ..runner.context import RunContext
from ..runner.pipeline import PipelineResult, run_pipeline
from ..settings import settings


def replay_run(
    run_id: str,
    *,
    store: DuckDBStore | None = None,
    profile: str | None = None,
) -> PipelineResult:
    """Replay a previously-executed run using stored snapshots."""

    store = store or DuckDBStore(settings.duckdb_path)
    manifest = store.get_run_manifest(run_id)
    if manifest is None:
        raise ValueError(f"Run {run_id} not found")

    context = RunContext.for_replay(manifest, profile=profile, snapshot_source_run_id=run_id)
    return run_pipeline(context, store=store)


__all__ = ["replay_run"]
