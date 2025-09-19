# Ironclad Bootstrap

Streamlined bootstrap for the Ironclad pipeline: DuckDB persistence, rerunnable pipelines, guardrails, CLI tooling, and a FastAPI status surface ready for Slack slash commands.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -e .[dev]

# run a demo pipeline (uses synthetic board when IRONCLAD_DEMO=1)
IRONCLAD_DEMO=1 python scripts/ic.py run --profile prod --season 2025 --week 3

# replay the last run using stored snapshots
python scripts/ic.py rerun <RUN_ID>

# launch the status API
uvicorn ironclad.app.status_api:app --reload --port 8080

# smoke test (writes out/reports/smoke_*.json|.md)
IRONCLAD_DEMO=1 python scripts/smoke/post_promo_smoke.py
```

DuckDB lives at `out/ironclad.duckdb` by default; override with `DUCKDB_PATH`.

## CLI (scripts/ic.py)

| Command | Description |
| --- | --- |
| `python scripts/ic.py run --season 2025 --week 3` | Run the pipeline end-to-end and persist picks. |
| `python scripts/ic.py rerun <RUN_ID>` | Replay a previous run using stored snapshots. |
| `python scripts/ic.py status` | Show recent runs, pick counts, and guardrail summary. |
| `python scripts/ic.py picks <RUN_ID>` | Dump picks for a run (JSON by default). |

Use `--snapshot-from <RUN_ID>` with `run` to seed a fresh run from existing snapshots.

## Status API

FastAPI app exposes:

- `GET /ironclad/status`
- `GET /ironclad/runs/{run_id}`
- `POST /ironclad/rerun/{run_id}`

Set `IRONCLAD_DEMO=1` to enable synthetic boards. Add `IRONCLAD_API_TOKEN` + `X-API-Token` header later for Slack middleware.

## Smoke + Guardrails

`scripts/smoke/post_promo_smoke.py` runs harvest→preslate→sizing→guardrails→UI, then writes JSON + markdown reports under `out/reports/`.

Guardrails live in `scripts/guardrails/checks.py`—drop in caps, market rules, and price sanity checks. They are wired into the pipeline and the smoke script.

## Repo Layout

```
src/ironclad/        core package
scripts/             CLI, guardrails, smoke
out/                 artifacts (DuckDB + reports)
.github/workflows/   CI + smoke automation
```

## CI

`.github/workflows/smoke.yml` runs the CLI + smoke script and uploads smoke reports as artifacts. Add golden tests, UI checks, and Slack handlers as you build on the bootstrap.
