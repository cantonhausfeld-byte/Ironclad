
PY?=python
run:
        IRONCLAD_PROFILE=$(PROFILE) $(PY) -m ironclad.runner.run_board --season $(SEASON) --week $(WEEK)

preslate-size:
	PYTHONPATH=src $(PY) scripts/analytics/size_and_mark.py
lint:
	ruff check src
	black --check src
	mypy src
test:
	pytest -q
format:
	black src tests
ci: format lint test

sized-count:
	. .venv/bin/activate && python -c "import duckdb; con=duckdb.connect('out/ironclad.duckdb'); print('picks_sized rows =', con.execute('select count(*) from picks_sized').fetchone()[0])"
