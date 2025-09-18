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

# Capture snapshots and record a full run (manifest + snapshots + picks + sized)
record-run:
	. .venv/bin/activate && PYTHONPATH=src python scripts/record_run.py --season $${SEASON:-2025} --week $${WEEK:-1} --profile $${PROFILE:-local} --seed $${SEED:-42}

# Quick peek at latest snapshot folder
snap-ls:
	ls -la out/snapshots | head -n 50 || true
