import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

# Ensure baseline output directories exist for scripts/tests
for rel in [
    "out/picks",
    "out/schedules",
    "out/analytics",
    "out/odds_history",
    "out/releases",
    "out/logs",
    "out/backups",
]:
    (ROOT / rel).mkdir(parents=True, exist_ok=True)
