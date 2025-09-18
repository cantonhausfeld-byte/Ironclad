.PHONY: init deps schedule preslate postslate ci-gate test clean backup logs ui sheets sheets-push

init:
	git init || true
	python -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt
	mkdir -p out/picks out/schedules out/analytics out/odds_history out/releases out/logs

deps:
	. .venv/bin/activate && pip install -r requirements.txt

schedule:
	. .venv/bin/activate && python scripts/schedules/harvest_schedule.py --season 2025 --week auto --outdir out/schedules
	. .venv/bin/activate && python scripts/schedules/orchestrate_schedule_update.py --minute_offset 60 --emit_crontab --outdir out/schedules
	@echo "Cron (UTC) ->"; cat out/schedules/cron_line_utc.txt || true

preslate:
	. .venv/bin/activate && python scripts/ic.py run-preslate

postslate:
	. .venv/bin/activate && python scripts/closing_line_scrapers/true_close.py --out_csv out/odds_history/closing_lines.csv
	. .venv/bin/activate && python scripts/analytics/odds_clv_audit.py --closers out/odds_history/closing_lines.csv
	. .venv/bin/activate && python scripts/analytics/make_release_artifacts.py --week auto

ci-gate:
	. .venv/bin/activate && python - <<'PY'
import json, datetime, subprocess
j=json.load(open('out/schedules/recommended_runs.json'))
iso=j['recommended_run_utc']['iso'].replace('Z','+00:00')
t=datetime.datetime.fromisoformat(iso)
now=datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
if abs((now-t).total_seconds())<=20*60:
    print('Within window → running preslate.')
    subprocess.check_call('python scripts/ic.py run-preslate', shell=True)
else:
    print('Outside window; target:', t, 'now:', now)
PY

backup:
	. .venv/bin/activate && python scripts/ops/backup_duckdb.py

logs:
	@echo "Last 30 log lines (out/logs/app.jsonl):"
	@tail -n 30 out/logs/app.jsonl || true

ui:
	. .venv/bin/activate && streamlit run streamlit_app.py

sheets:
	. .venv/bin/activate && python scripts/export/to_sheets.py --csv_out out/picks/picks_latest.csv

sheets-push:
	. .venv/bin/activate && python scripts/export/to_sheets.py --sheet "Ironclad Picks" --csv_out out/picks/picks_latest.csv

test:
	. .venv/bin/activate && pytest -q || true

clean:
	rm -rf .venv out/ironclad.duckdb out/picks out/schedules out/analytics out/odds_history out/releases out/backups out/logs
	mkdir -p out/picks out/schedules out/analytics out/odds_history out/releases out/backups out/logs
