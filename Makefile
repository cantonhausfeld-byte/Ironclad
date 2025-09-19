
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

.PHONY: smoke-prod
smoke-prod:
	@echo "Running post-promo smoke (PROFILE=$(PROFILE))"
	python scripts/smoke/post_promo_smoke.py
