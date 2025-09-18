from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from ..schemas.run_manifest import RunManifest


@dataclass(slots=True)
class RunContext:
    run_id: str
    season: int
    week: int
    profile: str
    seed: int
    created_at: datetime

    @classmethod
    def new(cls, *, season: int, week: int, profile: str, seed: int) -> RunContext:
        run_id = f"run-{uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc)
        return cls(
            run_id=run_id,
            season=season,
            week=week,
            profile=profile,
            seed=seed,
            created_at=created_at,
        )

    def manifest(self) -> RunManifest:
        return RunManifest(
            run_id=self.run_id,
            season=self.season,
            week=self.week,
            profile=self.profile,
            settings_json={
                "seed": self.seed,
                "created_at": self.created_at.isoformat(),
            },
        )

    def as_dict(self) -> dict[str, str | int]:
        return {
            "run_id": self.run_id,
            "season": self.season,
            "week": self.week,
            "profile": self.profile,
            "seed": self.seed,
            "created_at": self.created_at.isoformat(),
        }
