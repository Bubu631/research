PYTHON ?= python

.PHONY: test reproduce-core reproduce-public reproduce-full digits-balanced papers clean

test:
	$(PYTHON) -m unittest discover -s tests -v

reproduce-core:
	$(PYTHON) experiments/edit_localization.py
	$(PYTHON) experiments/base_upgrade.py
	$(PYTHON) experiments/digits_upgrade.py
	$(PYTHON) experiments/plot_digits.py
	$(PYTHON) experiments/digits_balanced.py
	$(PYTHON) experiments/summarize_digits_paths.py

digits-balanced:
	$(PYTHON) experiments/digits_balanced.py
	$(PYTHON) experiments/summarize_digits_paths.py

reproduce-public:
	$(PYTHON) experiments/public_postedit.py
	$(PYTHON) experiments/public_postedit.py --pair en-zh
	$(PYTHON) experiments/public_postedit_report.py

reproduce-full:
	$(PYTHON) experiments/full_parameter_postedit.py
	$(PYTHON) experiments/full_parameter_report.py
	$(PYTHON) experiments/verify_native_geometry.py

papers:
	cd papers/edit_localization && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
	cd papers/base_upgrade && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	cd papers/edit_localization && latexmk -c
	cd papers/base_upgrade && latexmk -c
