import subprocess, sys


def test_config_doctor_runs():
    r = subprocess.run(
        [sys.executable, "-m", "ironclad.runner.config_doctor"], capture_output=True, text=True
    )
    assert r.returncode == 0
    assert "{" in r.stdout
