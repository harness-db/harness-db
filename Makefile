# HARNESS-DB build targets. POSIX make; on this machine it runs under Git Bash
# (make -f Makefile figures), so the recipes are POSIX sh, not cmd.exe or PowerShell.
# PYTHON can be overridden: make PYTHON=C:/Python314/python.exe figures

PYTHON ?= python

.PHONY: schema validate test figures verify all check-analysis-scripts

all: schema validate test

schema:
	$(PYTHON) scripts/build_schema.py

validate:
	$(PYTHON) scripts/validate.py

test:
	$(PYTHON) -m pytest -q

# Every figure in paper/figures/ regenerates from data/ by running these, in order. They are
# depended on by filename rather than by a pattern rule so that a missing one fails here with a
# readable message instead of a "No rule to make target" from make itself.
ANALYSIS_SCRIPTS = \
	scripts/prisma_diagram.py \
	scripts/analyse_descriptives.py \
	scripts/analyse_families.py \
	scripts/analyse_outcomes.py

check-analysis-scripts:
	@missing=""; \
	for s in $(ANALYSIS_SCRIPTS); do \
		[ -f "$$s" ] || missing="$$missing $$s"; \
	done; \
	if [ -n "$$missing" ]; then \
		echo "make figures: cannot regenerate the figures, these analysis scripts are absent:"; \
		for s in $$missing; do echo "  - $$s"; done; \
		echo "Each is written by its own Phase 7 task; add the file (or run 'make figures'"; \
		echo "again once it lands) before regenerating paper/figures/."; \
		exit 1; \
	fi

figures: check-analysis-scripts
	@for s in $(ANALYSIS_SCRIPTS); do \
		echo "==> $$s"; \
		$(PYTHON) "$$s" || exit $$?; \
	done
	@echo "figures: paper/figures/ regenerated from data/"

# Everything a reviewer should be able to run before trusting a number: the data validator,
# then the whole test suite.
verify:
	$(PYTHON) scripts/validate.py
	$(PYTHON) -m pytest -q
