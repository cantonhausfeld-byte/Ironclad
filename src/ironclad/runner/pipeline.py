from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..persist.duckdb_store import DuckDBStore
from ..schemas.pick import Grade, Market, Pick
from ..services.odds_client import OddsClient
from ..settings import settings
from ..utils.odds import american_to_prob, prob_to_american
from .context import RunContext

try:
    from scripts.guardrails.checks import run_guardrails
except ModuleNotFoundError:  # pragma: no cover - defensive in case scripts missing from path

    def run_guardrails(picks: Sequence[Pick]) -> list[dict[str, Any]]:  # type: ignore[misc]
        return []


@dataclass(slots=True)
class PipelineResult:
    context: RunContext
    picks: list[Pick]
    guardrails: list[dict[str, Any]]
    snapshots: dict[str, Mapping[str, Any]]


def run_pipeline(
    context: RunContext,
    *,
    store: DuckDBStore | None = None,
    odds_client: OddsClient | None = None,
) -> PipelineResult:
    """Run the synthetic bootstrap pipeline end-to-end."""

    store = store or DuckDBStore(settings.duckdb_path)
    client = odds_client or OddsClient()

    store.write_run(context.to_manifest(), started_at=context.started_at)

    snapshots: dict[str, Mapping[str, Any]] = {}

    harvest_snapshot = _harvest_stage(context, store, client)
    snapshots["harvest"] = harvest_snapshot

    preslate_snapshot = _preslate_stage(context, store, harvest_snapshot)
    snapshots["preslate"] = preslate_snapshot

    picks, size_snapshot = _size_stage(context, store, preslate_snapshot)
    snapshots["size"] = size_snapshot

    guardrail_results = _guardrail_stage(context, store, picks)
    snapshots["guardrails"] = {"results": guardrail_results}

    ui_snapshot = _ui_stage(context, store, picks, guardrail_results)
    snapshots["ui"] = ui_snapshot

    store.write_picks(picks)

    return PipelineResult(
        context=context,
        picks=picks,
        guardrails=guardrail_results,
        snapshots=snapshots,
    )


# ---------------------------------------------------------------------------
# pipeline stages
# ---------------------------------------------------------------------------


def _load_snapshot(context: RunContext, store: DuckDBStore, stage: str) -> Mapping[str, Any] | None:
    if context.use_snapshots and context.snapshot_source_run_id:
        snapshot = store.get_snapshot(context.snapshot_source_run_id, stage)
        if snapshot is not None:
            # ensure the replay run re-persists the snapshot for auditability
            store.save_snapshot(context.run_id, stage, snapshot)
            return snapshot
    return None


def _harvest_stage(
    context: RunContext,
    store: DuckDBStore,
    client: OddsClient,
) -> Mapping[str, Any]:
    snapshot = _load_snapshot(context, store, "harvest")
    if snapshot is not None:
        return snapshot

    board = [
        {
            "game_id": line.game_id,
            "book": line.book,
            "market": line.market,
            "side": line.side,
            "line": line.line,
            "price_american": line.price_american,
            "ts": line.ts,
        }
        for line in client.fetch_board(context.season, context.week)
    ]
    snapshot = {"board": board}
    store.save_snapshot(context.run_id, "harvest", snapshot)
    return snapshot


def _preslate_stage(
    context: RunContext,
    store: DuckDBStore,
    harvest_snapshot: Mapping[str, Any],
) -> Mapping[str, Any]:
    snapshot = _load_snapshot(context, store, "preslate")
    if snapshot is not None:
        return snapshot

    board = harvest_snapshot.get("board", [])
    preslate_board = [
        line for line in board if str(line.get("market", "")).upper() in {"ML", "ATS", "OU"}
    ]
    snapshot = {"board": preslate_board}
    store.save_snapshot(context.run_id, "preslate", snapshot)
    return snapshot


def _size_stage(
    context: RunContext,
    store: DuckDBStore,
    preslate_snapshot: Mapping[str, Any],
) -> tuple[list[Pick], Mapping[str, Any]]:
    snapshot = _load_snapshot(context, store, "size")
    if snapshot is not None:
        picks = [Pick.model_validate(p) for p in snapshot.get("picks", [])]
        return picks, snapshot

    board = preslate_snapshot.get("board", [])
    picks = _picks_from_board(context, board)
    snapshot = {"picks": [p.model_dump(mode="json") for p in picks]}
    store.save_snapshot(context.run_id, "size", snapshot)
    return picks, snapshot


def _guardrail_stage(
    context: RunContext,
    store: DuckDBStore,
    picks: Sequence[Pick],
) -> list[dict[str, Any]]:
    snapshot = _load_snapshot(context, store, "guardrails")
    if snapshot is not None:
        return list(snapshot.get("results", []))

    results = run_guardrails(picks)
    store.save_snapshot(context.run_id, "guardrails", {"results": results})
    return results


def _ui_stage(
    context: RunContext,
    store: DuckDBStore,
    picks: Sequence[Pick],
    guardrail_results: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    snapshot = _load_snapshot(context, store, "ui")
    if snapshot is not None:
        return snapshot

    summary = {
        "run_id": context.run_id,
        "season": context.season,
        "week": context.week,
        "profile": context.profile,
        "pick_count": len(picks),
        "guardrails": list(guardrail_results),
    }
    store.save_snapshot(context.run_id, "ui", summary)
    return summary


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _payout(price: int) -> float:
    return (100 / abs(price)) if price < 0 else (price / 100)


def _grade_from_ev(ev: float) -> Grade:
    pct = ev * 100
    if pct >= 2.5:
        return Grade.A
    if pct >= 1.2:
        return Grade.B
    if ev > 0:
        return Grade.C
    return Grade.NO_PICK


def generate_picks_from_board(
    run_id: str,
    *,
    season: int,
    week: int,
    board: Sequence[Mapping[str, Any]],
    profile: str | None = None,
) -> list[Pick]:
    """Utility helper for UI/tests to reuse the sizing logic without persistence."""

    context = RunContext(
        run_id=run_id,
        season=season,
        week=week,
        profile=profile or settings.profile,
    )
    return _picks_from_board(context, board)


def _picks_from_board(
    context: RunContext,
    board: Sequence[Mapping[str, Any]],
    *,
    now: datetime | None = None,
) -> list[Pick]:
    ts = now or datetime.utcnow()
    picks: list[Pick] = []
    for line in board:
        if str(line.get("market", "")).upper() != "ML":
            continue
        price = int(line.get("price_american", -110))
        model_prob = min(max(american_to_prob(price) + 0.02, 0.01), 0.99)
        fair_price = prob_to_american(model_prob)
        ev = model_prob * (_payout(price)) - (1 - model_prob)
        grade = _grade_from_ev(ev)
        picks.append(
            Pick(
                run_id=context.run_id,
                game_id=str(line.get("game_id", "")),
                season=context.season,
                week=context.week,
                market=Market.ML,
                side=str(line.get("side", "")),
                line=line.get("line"),
                price_american=price,
                model_prob=model_prob,
                fair_price_american=fair_price,
                ev_percent=round(ev * 100, 4),
                z_score=0.0,
                robust_ev_percent=round(ev * 100, 4),
                grade=grade,
                kelly_fraction=(
                    0.05 if grade in {Grade.A, Grade.B} else 0.02 if grade == Grade.C else 0.0
                ),
                stake_units=0.0,
                book=str(line.get("book", "")),
                ts_created=ts,
            )
        )
    return picks


__all__ = ["PipelineResult", "generate_picks_from_board", "run_pipeline"]
