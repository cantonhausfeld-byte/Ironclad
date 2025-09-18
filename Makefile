
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

guardrails-validate:
	. .venv/bin/activate && python scripts/guardrails/validate_challenger.py --a $${RUN_A} --b $${RUN_B} --duck $${DUCK:-out/ironclad.duckdb} --policy $${POLICY:-config/guardrails.yaml}

promote:
	. .venv/bin/activate && python scripts/ops/promote_challenger.py --baseline $${RUN_A} --challenger $${RUN_B} --duck $${DUCK:-out/ironclad.duckdb} --policy $${POLICY:-config/guardrails.yaml} --profile $${PROFILE:-prod} $${FORCE:+--force} $${MODEL_ID:+--model_id $${MODEL_ID}} $${MODEL_VERSION:+--model_version $${MODEL_VERSION}}
