from __future__ import annotations

import os
import subprocess
import sys

import click
import duckdb

from ironclad.settings import get_settings


@click.command()
@click.option("--run_id", required=True)
@click.option("--season", type=int, required=False)
@click.option("--week", type=int, required=False)
@click.option("--profile", default="replay")
@click.option("--seed", type=int, default=123)
def main(run_id: str, season: int | None, week: int | None, profile: str, seed: int) -> None:
    """
    Re-run the pipeline using snapshots from a prior run_id.
    - Sets SNAPSHOT_RUN_ID so get_vendor() serves ReplayVendor
    - Calls your preslate + size + record_run to produce a new run
    """

    os.environ["SNAPSHOT_RUN_ID"] = run_id
    settings = get_settings()

    # Fill season/week if not provided by reading the prior run
    if season is None or week is None:
        try:
            with duckdb.connect(settings.duckdb_path, read_only=True) as con:
                row = con.execute(
                    "SELECT season, week FROM runs WHERE run_id = ?", [run_id]
                ).fetchone()
        except duckdb.Error:
            row = None
        if not row:
            print("Could not find season/week for run:", run_id)
            sys.exit(2)
        season, week = row

    # 1) Preslate (your pipeline should read via get_vendor())
    print(">>> Replaying preslate from snapshots …")
    preslate_env = os.environ | {"SEASON": str(season), "WEEK": str(week)}
    code = subprocess.call(["make", "preslate"], env=preslate_env)
    if code != 0:
        print("preslate failed (continuing if your flow writes picks elsewhere)")

    # 2) Size (optional)
    print(">>> Sizing …")
    subprocess.call(["make", "size"], env=os.environ)

    # 3) Record a new manifest (fresh run_id) with lineage pointing to snapshots used
    print(">>> Recording replayed run …")
    record_env = os.environ | {
        "PROFILE": profile,
        "SEED": str(seed),
        "SEASON": str(season),
        "WEEK": str(week),
    }
    subprocess.check_call(["make", "record-run"], env=record_env)
    print("Replay complete.")


if __name__ == "__main__":
    main()
