import glob, os, subprocess, sys, json, csv, time
from pathlib import Path

def _latest_picks_csv():
    files = sorted(Path("out/picks").glob("*_picks.csv"))
    assert files, "No picks CSVs found. Did preslate run?"
    return str(files[-1])

def test_preslate_golden(tmp_path):
    # Ensure schedules exist (deterministic demo)
    subprocess.check_call([sys.executable, "scripts/schedules/harvest_schedule.py", "--season", "2025", "--week", "1", "--outdir", "out/schedules"])
    # Run preslate once
    env = os.environ.copy(); env["SEASON"]="2025"; env["WEEK"]="1"
    subprocess.check_call([sys.executable, "scripts/ic.py", "run-preslate"], env=env)

    csv_path = _latest_picks_csv()
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1, f"Expected 1 demo row, got {len(rows)}"

    r = rows[0]
    # Canonical checks (baseline model emits a home ATS pick at -2.5, -110)
    assert r["season"] == "2025"
    assert r["week"] == "1"
    assert r["game_id"].startswith("W1_DEMO1")
    assert r["market"] == "ATS"
    assert r["side"] == "PHI"
    assert float(r["line"]) == -2.5
    assert int(float(r["price_american"])) == -110
    # Model prob & fair price (from baseline config at 0.52)
    assert abs(float(r["model_prob"]) - 0.52) < 1e-9
    assert int(float(r["fair_price_american"])) == 108
    # Grading (A because EV% is high in the simple baseline)
    assert r["grade"] in ("A", "B", "C", "NO_PICK")
    # Required fields exist
    for k in ["run_id","ts_created","book"]:
        assert r.get(k) not in (None, "", "NaN")
