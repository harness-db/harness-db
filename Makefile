.PHONY: schema validate test figures all

all: schema validate test

schema:
	python scripts/build_schema.py

validate:
	python scripts/validate.py

test:
	pytest -q

# Filled in by the analysis phase (S4): every figure regenerates from data/.
figures:
	python scripts/analysis/figures.py
