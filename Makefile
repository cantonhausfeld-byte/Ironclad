
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

replay-by-run:
	. .venv/bin/activate && \
	  python scripts/replay/run_with_snapshots.py --run_id $${RUN_ID} --season $${SEASON:-} --week $${WEEK:-} --profile $${PROFILE:-replay} --seed $${SEED:-123}
