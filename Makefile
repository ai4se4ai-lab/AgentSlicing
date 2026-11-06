PY ?= .venv/bin/python

all:
	$(PY) experiments/run_all.py

quick:
	$(PY) experiments/run_all.py --quick

test:
	$(PY) -m pytest -q tests

paper:
	cd docs/TSE && latexmk -pdf -interaction=nonstopmode main.tex

.PHONY: all quick test paper
