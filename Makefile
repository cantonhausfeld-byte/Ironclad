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
	. .venv/bin/activate && python scripts/ic.py run-preslate
	. .venv/bin/activate && python scripts/analytics/size_and_mark.py
