PY?=python

run:
	IRONCLAD_PROFILE=$(PROFILE) $(PY) -m ironclad.runner.run_board --season $(SEASON) --week $(WEEK)

preslate:
	. .venv/bin/activate && python scripts/analytics/preslate.py

lint:
	ruff check src
	black --check src
	mypy src

test:
	pytest -q

format:
	black src tests

ci: format lint test

harvest:
	. .venv/bin/activate && python scripts/schedules/harvest_schedule.py --season 2025 --week auto --outdir out/schedules

size:
	. .venv/bin/activate && python scripts/analytics/size_portfolio.py
