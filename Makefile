
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

exposure-delta:
	. .venv/bin/activate && python scripts/analytics/exposure_delta.py --a $${RUN_A} --b $${RUN_B} --duck $${DUCK:-out/ironclad.duckdb} --top $${TOP:-20}
