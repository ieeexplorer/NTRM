PYTHON ?= python3

.PHONY: setup test demo demo-live sensitivity lint format typecheck clean

setup:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest cascade_ml/tests agent_control/tests data_pipeline/tests -v

test-cov:
	$(PYTHON) -m pytest cascade_ml/tests agent_control/tests data_pipeline/tests -v --cov=cascade_ml --cov=agent_control --cov=data_pipeline --cov-report=term-missing

demo:
	$(PYTHON) run_demo.py

demo-live:
	$(PYTHON) run_demo.py --live

sensitivity:
	$(PYTHON) agent_control/scripts/run_sensitivity.py --scenario-limit 10

lint:
	$(PYTHON) -m ruff check cascade_ml agent_control data_pipeline run_demo.py

format:
	$(PYTHON) -m ruff format cascade_ml agent_control data_pipeline run_demo.py

typecheck:
	$(PYTHON) -m mypy cascade_ml agent_control data_pipeline --ignore-missing-imports

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf cascade_ml/data/*.csv agent_control/results/*.csv data_pipeline/results/*.csv