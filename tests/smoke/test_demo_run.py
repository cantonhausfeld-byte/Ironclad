import os
import subprocess
import sys


def test_demo_run_board():
    env = os.environ.copy()
    env["IRONCLAD_DEMO"] = "1"
    r = subprocess.run(
        [sys.executable, "-m", "ironclad.runner.run_board", "--season", "2025", "--week", "1"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0
    assert "wrote" in r.stdout.lower()
