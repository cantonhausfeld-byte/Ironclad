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
	$(PY) -m ironclad.runner.run_board --season $(SEASON) --week $(WEEK)
	$(PY) scripts/analytics/size_and_mark.py

guardrails-from-config:
	. .venv/bin/activate && python scripts/analytics/guardrail_check.py --season 2025 --week 1 --sized
