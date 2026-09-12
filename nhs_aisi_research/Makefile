PYTHON ?= python3
LATEXMK ?= latexmk

.PHONY: all primary exploratory verify figures paper workbook download data
all: primary exploratory figures verify paper
primary:
	$(PYTHON) experiments/synthetic.py --reps 2000
	$(PYTHON) experiments/replay.py --reps 1000
	$(PYTHON) experiments/nhs_scenarios.py
exploratory:
	$(PYTHON) experiments/replay_budget_extension.py
verify:
	$(PYTHON) experiments/verify_theory.py
	$(PYTHON) experiments/verify_allocation.py
	$(PYTHON) experiments/verify_implementation.py
	$(PYTHON) experiments/verify_budget_extension.py
figures:
	$(PYTHON) experiments/report.py
paper:
	cd paper && $(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error full.tex
	cd paper && $(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error anonymous.tex
	cd paper && $(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error supplement.tex
workbook:
	$(PYTHON) artifact_tools/build_results.py
download:
	$(PYTHON) data_tools/fetch_brfss.py
data: download
	$(PYTHON) data_tools/parse_brfss.py
	$(PYTHON) data_tools/validate_brfss.py
