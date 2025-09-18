PY?=python
SEASON?=2025
WEEK?=1
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
harvest:
	. .venv/bin/activate && python scripts/schedules/harvest_schedule.py --season $(SEASON) --week auto --outdir out/schedules
preslate:
	. .venv/bin/activate && python scripts/analytics/preslate.py --season $(SEASON) --week $(WEEK) --outdir out/picks
size:
	. .venv/bin/activate && python scripts/analytics/size_portfolio.py
