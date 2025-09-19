from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_config_doctor_runs():
    env = os.environ.copy()
    src = Path(__file__).resolve().parents[2] / "src"
    env["PYTHONPATH"] = f"{src}:{env.get('PYTHONPATH', '')}" if env.get("PYTHONPATH") else str(src)
    r = subprocess.run(
        [sys.executable, "-m", "ironclad.runner.config_doctor"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0
    assert "{" in r.stdout
