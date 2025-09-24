
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

preslate-size:
	. .venv/bin/activate && PYTHONPATH=src DUCKDB_PATH=out/ironclad.duckdb python -m ironclad.runner.run_board --season $(SEASON) --week $(WEEK)
	. .venv/bin/activate && PYTHONPATH=src python scripts/analytics/size_picks.py --duck out/ironclad.duckdb --season $(SEASON) --week $(WEEK)

exposure-export:
	. .venv/bin/activate && python scripts/analytics/exposure_export.py --season 2025 --week 1 --sized
