import duckdb, json, yaml, click, shutil
from pathlib import Path
import sys, datetime as dt

def _load_run(con, run_id):
    row = con.execute("SELECT settings_json FROM runs WHERE run_id = ?", [run_id]).fetchone()
    return json.loads(row[0]) if row and row[0] else {}

@click.command()
@click.option("--duck", default="out/ironclad.duckdb", show_default=True)
@click.option("--baseline", "run_a", required=True, help="Baseline run_id")
@click.option("--challenger", "run_b", required=True, help="Challenger run_id to promote")
@click.option("--policy", default="config/guardrails.yaml", show_default=True, help="Same policy used in validation")
@click.option("--profile", default="prod", show_default=True)
@click.option("--profile_dir", default="config/profiles", show_default=True)
@click.option("--force", is_flag=True, help="Promote even if guardrails failed (danger)")
@click.option("--model_id", default=None, help="Override model id")
@click.option("--model_version", default=None, help="Override model version")
def main(duck, run_a, run_b, policy, profile, profile_dir, force, model_id, model_version):
    # 1) run guardrails validator
    import subprocess, os
    env = os.environ.copy()
    cmd = ["python", "scripts/guardrails/validate_challenger.py", "--duck", duck, "--a", run_a, "--b", run_b, "--policy", policy]
    rc = subprocess.call(cmd, env=env)
    if rc != 0 and not force:
        print("Refusing to promote: guardrails failed (use --force to override)"); sys.exit(2)

    con = duckdb.connect(duck, read_only=True)
    # 2) pull challenger metadata (model id/version if present)
    meta = _load_run(con, run_b)
    model = {
        "id": model_id or meta.get("model_id","Apache"),
        "version": int(model_version or meta.get("model_version", 1))
    }
    thresholds = meta.get("thresholds", {
        "grade_A_ev_pct_min": 3.0,
        "grade_B_ev_pct_min": 1.0
    })

    # 3) write new profile file (with backup)
    prof_dir = Path(profile_dir)
    prof_dir.mkdir(parents=True, exist_ok=True)
    prod_path = prof_dir / f"{profile}.yaml"
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    if prod_path.exists():
        shutil.copyfile(prod_path, prof_dir / f"{profile}.yaml.bak.{ts}")

    new_cfg = {
        "model": model,
        "thresholds": thresholds,
        "last_promoted_run": run_b,
        "notes": f"Promoted from {run_b} (baseline {run_a}) at {ts}Z"
    }
    with open(prod_path, "w") as f:
        yaml.safe_dump(new_cfg, f, sort_keys=False)

    print(f"Promoted challenger to {prod_path}")
    print(json.dumps(new_cfg, indent=2))

if __name__ == "__main__":
    main()
