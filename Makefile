
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

.PHONY: smoke-prod nightly-local

nightly-local:
	# Simulate the nightly job locally (same script)
	. .venv/bin/activate && PROFILE=$${PROFILE:-prod} DUCK=$${DUCK:-out/ironclad.duckdb} python scripts/smoke/post_promo_smoke.py
