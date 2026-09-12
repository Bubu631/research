.DEFAULT_GOAL := help

PYTHON ?= .venv/bin/python
DATA_PYTHON ?= $(PYTHON)
LATEXMK ?= latexmk

.PHONY: help check-env data-fetch data-parse data-docs data-checks vintage-data \
        analysis harmonised vintage simulation simulation-smoke checks report latex all

help:
	@printf '%s\n' \
	  'NHS staff wellbeing research. Default target only displays this help.' \
	  'Install requirements.txt in .venv, or set PYTHON=/path/to/python.' \
	  'check-env        Show required package versions without changing results.' \
	  'data-fetch       Download/verify official public source assets (network).' \
	  'data-parse       Parse the primary five-year workbook already downloaded.' \
	  'data-docs        Extract PDF documentation; set DATA_PYTHON to the data environment.' \
	  'data-checks      Validate the primary panel against original source files.' \
	  'vintage-data     Fetch/parse/validate two historical benchmark vintages (network).' \
	  'analysis         Recompute both empirical backtests from prepared CSV inputs.' \
	  'harmonised       Recompute only the 2025-reweighted-history backtest.' \
	  'vintage          Recompute only the archived-predictor-vintage backtest.' \
	  'simulation       Recompute 600,000 Gaussian panel draws plus four stress cells.' \
	  'simulation-smoke Run 20 repetitions per cell under separate smoke filenames.' \
	  'checks           Execute independent theory and empirical verification.' \
	  'report           Regenerate figures and LaTeX tables from saved full results.' \
	  'latex            Compile the paper using existing generated figures/tables.' \
	  'all              Sequentially run analysis, simulation, checks, report, latex.' \
	  'Analysis/report targets replace their own generated outputs. Data downloads are never automatic in all.'

check-env:
	"$(PYTHON)" -c "import sys,numpy,pandas,scipy,matplotlib,openpyxl; print(sys.version); print({m.__name__:m.__version__ for m in (numpy,pandas,scipy,matplotlib,openpyxl)})"

data-fetch:
	"$(PYTHON)" data_tools/fetch_sources.py

data-parse:
	"$(PYTHON)" data_tools/parse_panel.py

data-docs:
	"$(DATA_PYTHON)" data_tools/extract_documentation.py

data-checks:
	"$(PYTHON)" data_tools/validate_panel.py

vintage-data:
	$(MAKE) data-fetch
	$(MAKE) data-parse
	$(MAKE) data-checks
	cp data/raw/detailed_2021.zip vintage_data/detailed_2021.zip
	cp data/raw/detailed_2022.zip vintage_data/detailed_2022.zip
	cp data/raw/detailed_2023.zip vintage_data/detailed_2023.zip
	cp data/raw/detailed_2024.zip vintage_data/detailed_2024.zip
	"$(PYTHON)" vintage_data/fetch_primary_benchmarks.py
	"$(PYTHON)" vintage_data/parse_vintages.py
	"$(PYTHON)" vintage_data/validate_vintages.py

harmonised: data/processed/nhs_staff_survey_panel_2021_2025.csv
	"$(PYTHON)" experiments/empirical.py

vintage: data/processed/nhs_staff_survey_panel_2021_2025.csv vintage_data/benchmark_vintage_panel.csv
	"$(PYTHON)" experiments/vintage_empirical.py

analysis:
	$(MAKE) harmonised
	$(MAKE) vintage

simulation:
	"$(PYTHON)" experiments/simulate.py --reps 5000 --seed 2026091101 --output simulation

simulation-smoke:
	"$(PYTHON)" experiments/simulate.py --reps 20 --seed 2026091101 --output simulation_smoke

checks:
	"$(PYTHON)" experiments/theory_checks.py
	"$(PYTHON)" experiments/verify_empirical.py

report:
	"$(PYTHON)" experiments/report.py

latex:
	cd paper && "$(LATEXMK)" -pdf -interaction=nonstopmode -halt-on-error main.tex

all:
	$(MAKE) analysis
	$(MAKE) simulation
	$(MAKE) checks
	$(MAKE) report
	$(MAKE) latex
