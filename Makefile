
PY?=python
PROFILE?=local
SEASON?=2025
WEEK?=1

.PHONY: run lint test format smoke ci

run:
IRONCLAD_PROFILE=$(PROFILE) $(PY) scripts/ic.py run --season $(SEASON) --week $(WEEK)

smoke:
IRONCLAD_PROFILE=$(PROFILE) IRONCLAD_DEMO=1 $(PY) scripts/smoke/post_promo_smoke.py --season $(SEASON) --week $(WEEK)

lint:
ruff check src scripts
black --check src scripts tests
mypy src

test:
pytest -q

format:
black src scripts tests

ci: format lint test
