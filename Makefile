
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


smoke-prod:
	. .venv/bin/activate && python scripts/smoke/post_promo_smoke.py PROFILE=$${PROFILE:-prod} DUCK=$${DUCK:-out/ironclad.duckdb}

# convenience: validate → promote → smoke (fails fast)
promote-and-smoke:
	. .venv/bin/activate && \
	RUN_A=$${RUN_A} RUN_B=$${RUN_B} make guardrails-validate && \
	RUN_A=$${RUN_A} RUN_B=$${RUN_B} make promote && \
	make smoke-prod PROFILE=$${PROFILE:-prod}
