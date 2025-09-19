#!/usr/bin/env python3
"""
Lightweight end-to-end smoke for Ironclad.

Flow (non-blocking mocks allowed):
  1) harvest      → snapshot odds/injuries/weather (or demo snapshot)
  2) preslate     → build candidate board
  3) size         → apply sizing (kelly/limits)
  4) guardrails   → validate caps, sanity, data quality
  5) ui_checks    → ensure UI-ready artifacts exist

Outputs:
  - out/reports/smoke_<ts>.json
  - out/reports/smoke_<ts>.md
Exit code non-zero on any failure.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any

# ---------- Config / Env ----------
PROFILE = os.getenv("PROFILE", "prod")
SEASON = os.getenv("SEASON") or ""  # optional override
WEEK = os.getenv("WEEK") or ""  # optional override
RUN_ID = os.getenv("RUN_ID") or ""
RUN_A = os.getenv("RUN_A") or ""  # baseline (for promote flows)
RUN_B = os.getenv("RUN_B") or ""  # challenger (for promote flows)

OUTDIR = Path("out")
REPORTS = OUTDIR / "reports"
LOGDIR = OUTDIR / "logs"
DUCK = os.getenv("DUCK", "out/ironclad.duckdb")  # not used by skeleton, just recorded

REPORTS.mkdir(parents=True, exist_ok=True)
LOGDIR.mkdir(parents=True, exist_ok=True)

TS = time.strftime("%Y%m%d_%H%M%S")
STAMP = f"{TS}_{PROFILE}"


# ---------- Result model ----------
@dataclass
class StepResult:
    name: str
    ok: bool
    details: str = ""
    metrics: dict[str, Any] | None = None


@dataclass
class SmokeResult:
    profile: str
    season: str
    week: str
    run_id: str
    run_a: str
    run_b: str
    duck_path: str
    started_at: str
    finished_at: str
    steps: list[StepResult]
    overall_ok: bool


# ---------- Helpers ----------
def log(msg: str) -> None:
    print(msg, flush=True)


def safe_step(
    name: str,
    fn: Callable[..., tuple[bool, str, dict[str, Any] | None]],
    *args: Any,
    **kwargs: Any,
) -> StepResult:
    t0 = time.time()
    try:
        ok, details, metrics = fn(*args, **kwargs)
        dt = time.time() - t0
        metrics = metrics or {}
        metrics["wall_sec"] = round(dt, 3)
        return StepResult(name=name, ok=bool(ok), details=details, metrics=metrics)
    except Exception as exc:  # noqa: BLE001 - surface stack traces for debugging
        tb = traceback.format_exc(limit=6)
        return StepResult(
            name=name,
            ok=False,
            details=f"{exc}\n{tb}",
            metrics={"wall_sec": round(time.time() - t0, 3)},
        )


def write_reports(sr: SmokeResult) -> tuple[Path, Path]:
    json_path = REPORTS / f"smoke_{STAMP}.json"
    md_path = REPORTS / f"smoke_{STAMP}.md"
    with json_path.open("w") as handle:
        json.dump({**asdict(sr), "steps": [asdict(step) for step in sr.steps]}, handle, indent=2)
    with md_path.open("w") as handle:
        handle.write(render_markdown(sr))
    return json_path, md_path


def render_markdown(sr: SmokeResult) -> str:
    rows = []
    for step in sr.steps:
        emoji = "✅" if step.ok else "❌"
        details = step.details.replace("|", "\\|")
        metrics = json.dumps(step.metrics or {})
        rows.append(f"| {emoji} | **{step.name}** | {details} | {metrics} |")
    header = textwrap.dedent(
        f"""
        # Ironclad Smoke — {sr.profile} — {sr.finished_at}

        **Season/Week:** {sr.season or '(auto)'} / {sr.week or '(auto)'}  
        **RUN_ID:** {sr.run_id or '(new)'}  
        **Promote baseline/challenger:** {sr.run_a or '-'} → {sr.run_b or '-'}  
        **DuckDB:** `{sr.duck_path}`

        **Overall:** {"✅ PASS" if sr.overall_ok else "❌ FAIL"}

        | OK | Step | Details | Metrics |
        |---:|------|---------|---------|
        """
    ).strip()
    return f"{header}\n" + "\n".join(rows) + "\n"


# ---------- Stub stage implementations ----------
# Replace these stubs with your real module calls. Keep return signature: (ok, details, metrics)

def stage_harvest(*, profile: str, season: str, week: str) -> tuple[bool, str, dict[str, Any]]:
    """Materialize snapshots (odds/injuries/weather) and record a run context."""
    log(f"[harvest] profile={profile} season={season} week={week}")
    metrics = {"games": 16, "snapshots": {"odds": 16, "injuries": 16, "weather": 14}}
    return True, "Harvest completed (stub)", metrics


def stage_preslate(*, profile: str) -> tuple[bool, str, dict[str, Any]]:
    """Build candidate board from snapshots/features/model."""
    log(f"[preslate] profile={profile}")
    metrics = {"candidates": 120, "markets": {"ML": 25, "ATS": 40, "OU": 30, "PROP": 25}}
    return True, "Preslate completed (stub)", metrics


def stage_size(*, profile: str) -> tuple[bool, str, dict[str, Any]]:
    """Size positions (kelly/limits/correlation)."""
    log(f"[size] profile={profile}")
    metrics = {"picks_sized": 28, "total_units": 19.4, "kelly_cap": 0.2}
    return True, "Sizing completed (stub)", metrics


def stage_guardrails(*, profile: str) -> tuple[bool, str, dict[str, Any]]:
    """Validate data quality & limits. Fail if violations found."""
    log(f"[guardrails] profile={profile}")
    violations: list[str] = []
    ok = len(violations) == 0
    details = "No guardrail violations" if ok else f"Violations: {', '.join(violations)}"
    metrics = {"violations": len(violations)}
    return ok, details, metrics


def stage_ui_checks(*, profile: str) -> tuple[bool, str, dict[str, Any]]:
    """Ensure UI artifacts exist (tables, CSV/Parquet, Streamlit endpoints respond)."""
    log(f"[ui] profile={profile}")
    ui_dir = Path("out/ui")
    ok = ui_dir.exists()
    details = "UI artifacts present" if ok else "UI artifacts missing (create out/ui/*)"
    metrics = {"path": str(ui_dir)}
    return ok, details, metrics


# ---------- Main ----------
def main() -> int:
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.gmtime())
    steps: list[StepResult] = []

    steps.append(safe_step("harvest", stage_harvest, profile=PROFILE, season=SEASON, week=WEEK))
    steps.append(safe_step("preslate", stage_preslate, profile=PROFILE))
    steps.append(safe_step("size", stage_size, profile=PROFILE))
    steps.append(safe_step("guardrails", stage_guardrails, profile=PROFILE))
    steps.append(safe_step("ui_checks", stage_ui_checks, profile=PROFILE))

    overall_ok = all(step.ok for step in steps)
    finished = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.gmtime())
    result = SmokeResult(
        profile=PROFILE,
        season=SEASON,
        week=WEEK,
        run_id=RUN_ID,
        run_a=RUN_A,
        run_b=RUN_B,
        duck_path=DUCK,
        started_at=started,
        finished_at=finished,
        steps=steps,
        overall_ok=overall_ok,
    )
    json_path, md_path = write_reports(result)
    log(f"[smoke] wrote {json_path} and {md_path}")
    return 0 if overall_ok else 2


if __name__ == "__main__":
    sys.exit(main())
