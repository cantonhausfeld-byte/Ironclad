from ironclad.runner.context import RunContext
from ironclad.schemas.run_manifest import RunManifest


def test_run_context_manifest_snapshot():
    ctx = RunContext.new(season=2025, week=3, profile="prod")
    manifest = ctx.to_manifest()
    assert manifest.run_id == ctx.run_id
    assert manifest.settings_json["profile"] == "prod"
    assert manifest.settings_json["use_snapshots"] is False

    replay_ctx = RunContext.for_replay(
        RunManifest(
            run_id="run-abc",
            season=2025,
            week=3,
            profile="qa",
            settings_json={"foo": "bar"},
        )
    )
    assert replay_ctx.use_snapshots is True
    assert replay_ctx.snapshot_source_run_id == "run-abc"
    replay_manifest = replay_ctx.to_manifest()
    assert replay_manifest.settings_json["snapshot_source_run_id"] == "run-abc"
