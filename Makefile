PYTHON ?= python

.PHONY: setup test demo demo-live sensitivity

setup:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest cascade_ml/tests agent_control/tests data_pipeline/tests

demo:
	$(PYTHON) run_demo.py

demo-live:
	$(PYTHON) run_demo.py --live

sensitivity:
	$(PYTHON) agent_control/scripts/run_sensitivity.py --scenario-limit 10
