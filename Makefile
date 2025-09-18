
PY?=python
run:
	IRONCLAD_PROFILE=$(PROFILE) $(PY) -m ironclad.runner.run_board --season $(SEASON) --week $(WEEK)
lint:
	ruff check src
	black --check src
	mypy src
test:
	pytest -q
format:
	black src tests
ci: format lint test

record-run:
	. .venv/bin/activate && PYTHONPATH=src python scripts/record_run.py --season $${SEASON:-2025} --week $${WEEK:-1} --profile $${PROFILE:-local} --seed $${SEED:-42}

replay-latest:
	. .venv/bin/activate && PYTHONPATH=src python -c "from ironclad.settings import get_settings; import duckdb; s=get_settings(); path=getattr(s, 'DUCKDB__PATH', getattr(s, 'duckdb_path', 'out/ironclad.duckdb')); con=duckdb.connect(path); sql=\"SELECT p.run_id, p.season, p.week, COUNT(*) AS n, r.started_at, MAX(p.ts_created) AS latest_pick_ts FROM picks p LEFT JOIN runs r ON p.run_id = r.run_id GROUP BY p.run_id, p.season, p.week, r.started_at ORDER BY COALESCE(r.started_at, MAX(p.ts_created)) DESC NULLS LAST LIMIT 5\"; print(con.execute(sql).df())"
