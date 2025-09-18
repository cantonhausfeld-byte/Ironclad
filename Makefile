
PY?=python
run:
        IRONCLAD_PROFILE=$(PROFILE) $(PY) -m ironclad.runner.run_board --season $(SEASON) --week $(WEEK)
record-run:
        IRONCLAD_PROFILE=$(PROFILE) $(PY) scripts/record_run.py --season $(SEASON) --week $(WEEK)
lint:
        ruff check src
        black --check src
        mypy src
test:
        pytest -q
format:
        black src tests
ci: format lint test
data-quality:
	. .venv/bin/activate && python scripts/analytics/data_quality_check.py --season $${SEASON:-2025} --week $${WEEK:-1}
