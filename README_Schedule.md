# Ironclad — Schedule-Aware Scans (No Unzip Build)

## Quickstart
```bash
make init
export TZ="America/New_York"
make schedule
make preslate
```

Artifacts:
	•	out/schedules/recommended_runs.json — next pre-slate run (UTC & local)
	•	out/schedules/cron_line_utc.txt — single cron line to run preslate
	•	out/picks/*_picks.csv — picks from the baseline model
	•	DuckDB: out/ironclad.duckdb → tables runs, picks

One-shot scheduling

```bash
python scripts/schedules/schedule_one_shot.py
```

Recurring cron (UTC)

```bash
( echo "# ==== IRONCLAD (auto-generated) ===="; cat out/schedules/crontab_block.txt ) | crontab -
crontab -l | tail -n +20
```

CI (GitHub Actions)
	•	ci.yml runs smoke (config, schedule harvest, preslate, tests)
	•	pregame.yml runs hourly; self-gates within ±20m of recommended_run_utc
