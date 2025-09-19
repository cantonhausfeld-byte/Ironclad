from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_demo_run_cli(tmp_path):
    env = os.environ.copy()
    env["IRONCLAD_DEMO"] = "1"
    env["DUCKDB_PATH"] = str(tmp_path / "ironclad.duckdb")
    src = Path(__file__).resolve().parents[2] / "src"
    env["PYTHONPATH"] = f"{src}:{env.get('PYTHONPATH', '')}" if env.get("PYTHONPATH") else str(src)
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ic.py",
            "run",
            "--season",
            "2025",
            "--week",
            "1",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert "run_id" in r.stdout
