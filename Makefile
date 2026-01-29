PYTHON ?= python
NOTEBOOK_DIR ?= notebooks
RUN_DIR ?= notebooks/_runs

AWS_REGION ?= us-east-1
ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
REPO_NAME ?= pubmed-rag-ui-repo
VERSION ?= $(shell cat VERSION 2>/dev/null)
IMAGE_TAG ?= v$(VERSION)

.PHONY: precommit-install precommit-run clean-notebooks fetch process test build-ui-image run-ui bump-patch bump-minor bump-major tag-release

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

run-ui:
	@# Export variables from .env (if present) into the Streamlit environment.
	set -a; [ -f .env ] && . .env; set +a; streamlit run ui/app.py

build-ui-image:
	@if [ -z "$(VERSION)" ]; then \
	  echo "VERSION file missing. Create VERSION (e.g. 0.0.4)."; \
	  exit 1; \
	fi
	@if [ -z "$(ACCOUNT_ID)" ]; then \
	  echo "ACCOUNT_ID is not set and could not be derived from aws sts. Set ACCOUNT_ID env var."; \
	  exit 1; \
	fi
	aws ecr get-login-password --region "$(AWS_REGION)" | docker login --username AWS --password-stdin "$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com"
	docker build -t "$(REPO_NAME):$(IMAGE_TAG)" ui/
	docker tag "$(REPO_NAME):$(IMAGE_TAG)" "$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(REPO_NAME):$(IMAGE_TAG)"
	docker push "$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(REPO_NAME):$(IMAGE_TAG)"

bump-patch:
	bump2version patch

bump-minor:
	bump2version minor

bump-major:
	bump2version major

tag-release:
	@# Best practice: run this on the merge commit on main.
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then \
	  echo "Refusing to tag: not on main. Checkout main and ensure it's up to date."; \
	  exit 1; \
	fi
	@if [ -n "$$(git status --porcelain)" ]; then \
	  echo "Refusing to tag: working tree not clean."; \
	  exit 1; \
	fi
	@git tag -a "v$$(cat VERSION)" -m "Release v$$(cat VERSION)"
	@git push origin "v$$(cat VERSION)"
