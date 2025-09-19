from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ..schemas.run_manifest import RunManifest
from ..settings import settings


def _now() -> datetime:
    return datetime.now(UTC)


def _generate_run_id(profile: str, season: int, week: int, *, suffix: str | None = None) -> str:
    token = uuid4().hex[:8]
    parts = [profile.lower(), f"{season}w{week}", token]
    if suffix:
        parts.insert(2, suffix.lower())
    return "-".join(parts)


@dataclass(slots=True)
class RunContext:
    run_id: str
    season: int
    week: int
    profile: str
    use_snapshots: bool = False
    snapshot_source_run_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=_now)

    @classmethod
    def new(
        cls,
        *,
        season: int,
        week: int,
        profile: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> RunContext:
        profile_value = profile or settings.profile
        return cls(
            run_id=_generate_run_id(profile_value, season, week),
            season=season,
            week=week,
            profile=profile_value,
            use_snapshots=False,
            snapshot_source_run_id=None,
            params=dict(params or {}),
        )

    @classmethod
    def from_manifest(cls, manifest: RunManifest, *, use_snapshots: bool = False) -> RunContext:
        return cls(
            run_id=manifest.run_id,
            season=manifest.season,
            week=manifest.week,
            profile=manifest.profile,
            use_snapshots=use_snapshots,
            snapshot_source_run_id=None,
            params=dict(manifest.settings_json),
        )

    @classmethod
    def for_replay(
        cls,
        manifest: RunManifest,
        *,
        profile: str | None = None,
        snapshot_source_run_id: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> RunContext:
        profile_value = profile or manifest.profile
        source_run_id = snapshot_source_run_id or manifest.run_id
        merged_params = dict(manifest.settings_json)
        if params:
            merged_params.update(params)
        merged_params["snapshot_source_run_id"] = source_run_id
        return cls(
            run_id=_generate_run_id(profile_value, manifest.season, manifest.week, suffix="replay"),
            season=manifest.season,
            week=manifest.week,
            profile=profile_value,
            use_snapshots=True,
            snapshot_source_run_id=source_run_id,
            params=merged_params,
        )

    def to_manifest(self) -> RunManifest:
        payload = dict(self.params)
        payload.setdefault("profile", self.profile)
        payload.setdefault("use_snapshots", self.use_snapshots)
        if self.snapshot_source_run_id:
            payload["snapshot_source_run_id"] = self.snapshot_source_run_id
        return RunManifest(
            run_id=self.run_id,
            season=self.season,
            week=self.week,
            profile=self.profile,
            settings_json=payload,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "season": self.season,
            "week": self.week,
            "profile": self.profile,
            "use_snapshots": self.use_snapshots,
            "snapshot_source_run_id": self.snapshot_source_run_id,
            "params": dict(self.params),
            "started_at": self.started_at.isoformat(),
        }
