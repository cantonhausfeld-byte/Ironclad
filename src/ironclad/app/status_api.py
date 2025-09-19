from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException

from ..persist.duckdb_store import DuckDBStore
from ..runner.replay import replay_run
from ..settings import settings

app = FastAPI(title="Ironclad Status API")


def get_store() -> DuckDBStore:
    return DuckDBStore(settings.duckdb_path)


@app.get("/ironclad/status")
def read_status(store: DuckDBStore = Depends(get_store)) -> dict[str, Any]:
    summary = store.status_summary()
    runs = [run.to_dict() for run in store.list_runs(limit=10)]
    return {
        "status": "ok",
        "profile": settings.profile,
        "duckdb_path": str(store.path),
        "summary": summary,
        "runs": runs,
    }


@app.get("/ironclad/runs/{run_id}")
def read_run(run_id: str, store: DuckDBStore = Depends(get_store)) -> dict[str, Any]:
    manifest = store.get_run_manifest(run_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Run not found")
    picks = [pick.model_dump(mode="json") for pick in store.fetch_picks(run_id)]
    return {
        "run": manifest.model_dump(),
        "picks": picks,
        "snapshots": store.list_snapshots(run_id),
    }


@app.post("/ironclad/rerun/{run_id}")
def rerun(run_id: str, store: DuckDBStore = Depends(get_store)) -> dict[str, Any]:
    try:
        result = replay_run(run_id, store=store)
    except ValueError as exc:  # run not found
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "status": "ok",
        "source_run_id": run_id,
        "run_id": result.context.run_id,
        "pick_count": len(result.picks),
        "guardrails": result.guardrails,
    }
