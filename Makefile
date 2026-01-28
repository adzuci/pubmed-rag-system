PYTHON ?= python
NOTEBOOK_DIR ?= notebooks
RUN_DIR ?= notebooks/_runs

.PHONY: precommit-install precommit-run clean-notebooks fetch process test

precommit-install:
	$(PYTHON) -m pre_commit install

precommit-run:
	$(PYTHON) -m pre_commit run --all-files

clean-notebooks:
	$(PYTHON) -m nbstripout $(NOTEBOOK_DIR)/*.ipynb

fetch:
	mkdir -p $(RUN_DIR)
	jupyter nbconvert --to notebook --execute \
		--output-dir $(RUN_DIR) \
		--output pubmed_search_and_fetch_run.ipynb \
		$(NOTEBOOK_DIR)/pubmed_search_and_fetch.ipynb

process:
	mkdir -p $(RUN_DIR)
	jupyter nbconvert --to notebook --execute \
		--output-dir $(RUN_DIR) \
		--output pubmed_processing_analysis_run.ipynb \
		$(NOTEBOOK_DIR)/pubmed_processing_analysis.ipynb

test:
	# Export variables from .env (if present) into the test environment.
	set -a; [ -f .env ] && . .env; set +a; PYTHONPATH=. $(PYTHON) -m pytest -q
