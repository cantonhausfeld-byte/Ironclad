from datetime import UTC, datetime

from ironclad.persist.duckdb_store import DuckDBStore
from ironclad.runner.context import RunContext
from ironclad.schemas.pick import Grade, Market, Pick


def test_duckdb_store_roundtrip(tmp_path):
    db_path = tmp_path / "ironclad.duckdb"
    store = DuckDBStore(str(db_path))

    context = RunContext.new(season=2025, week=1, profile="local")
    store.write_run(context.to_manifest(), started_at=context.started_at)

    pick = Pick(
        run_id=context.run_id,
        game_id="game-1",
        season=2025,
        week=1,
        market=Market.ML,
        side="WAS",
        line=None,
        price_american=-110,
        model_prob=0.55,
        fair_price_american=-120,
        ev_percent=3.2,
        z_score=0.0,
        robust_ev_percent=3.2,
        grade=Grade.A,
        kelly_fraction=0.05,
        stake_units=1.0,
        book="DemoBook",
        ts_created=datetime.now(UTC),
    )
    store.write_picks([pick])

    manifest = store.get_run_manifest(context.run_id)
    assert manifest is not None
    assert manifest.run_id == context.run_id

    picks = store.fetch_picks(context.run_id)
    assert len(picks) == 1
    assert picks[0].price_american == -110

    store.save_snapshot(context.run_id, "harvest", {"board": []})
    assert store.get_snapshot(context.run_id, "harvest") == {"board": []}
    assert "harvest" in store.list_snapshots(context.run_id)

    summary = store.status_summary()
    assert summary["runs"] == 1
    assert summary["picks"] == 1
