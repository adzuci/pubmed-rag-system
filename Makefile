# Variables
PYTHON ?= python
NOTEBOOK_DIR ?= notebooks
RUN_DIR ?= notebooks/_runs
TF_DIR ?= terraform
AWS_REGION ?= us-east-1
ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
REPO_NAME ?= pubmed-rag-ui-repo
VERSION ?= $(shell cat VERSION 2>/dev/null)
IMAGE_TAG ?= v$(VERSION)

.PHONY: precommit-install precommit-run clean-notebooks test coverage setup run-ui run-fetch run-process terraform-init terraform-validate terraform-plan terraform-apply build-ui build-push-ui bump-patch bump-minor bump-major tag-release

# Development Tools
# Require Python 3.12+ and Docker; setup reports clearly if either is missing
setup:
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "Python is required (e.g. 3.12.x). Install from https://www.python.org/"; exit 1; }
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null || { echo "Python 3.12 or newer is required. Current: $$($(PYTHON) --version 2>/dev/null || echo 'unknown')"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required for building/pushing the UI image. Install from https://www.docker.com/"; exit 1; }
	@test -d .venv || $(PYTHON) -m venv .venv
	@. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt -r requirements-dev.txt -r ui/requirements.txt
	@echo "Setup complete. Run: make run-ui"

precommit-install:
	$(PYTHON) -m pre_commit install

precommit-run:
	$(PYTHON) -m pre_commit run --all-files

clean-notebooks:
	$(PYTHON) -m nbstripout $(NOTEBOOK_DIR)/*.ipynb

test:
	set -a; [ -f .env ] && . .env; set +a; PYTHONPATH=. $(RUN_PYTHON) -m pytest -q

coverage:
	set -a; [ -f .env ] && . .env; set +a; PYTHONPATH=. $(RUN_PYTHON) -m pytest -q --cov=. --cov-report=term-missing

# Local Development (prefer .venv if present so "make setup && make run-ui" works)
RUN_PYTHON := $(if $(wildcard .venv/bin/python),.venv/bin/python,$(PYTHON))
run-ui:
	@$(RUN_PYTHON) -c "import streamlit" 2>/dev/null || { \
		echo "Streamlit not found. Run: make setup"; \
		exit 1; \
	}
	set -a; [ -f .env ] && . .env; set +a; $(RUN_PYTHON) -m streamlit run ui/app.py

run-fetch:
	mkdir -p $(RUN_DIR)
	jupyter nbconvert --to notebook --execute \
		--output-dir $(RUN_DIR) \
		--output pubmed_search_and_fetch_run.ipynb \
		$(NOTEBOOK_DIR)/pubmed_search_and_fetch.ipynb

run-process:
	mkdir -p $(RUN_DIR)
	jupyter nbconvert --to notebook --execute \
		--output-dir $(RUN_DIR) \
		--output pubmed_processing_analysis_run.ipynb \
		$(NOTEBOOK_DIR)/pubmed_processing_analysis.ipynb

# Terraform
terraform-init:
	cd $(TF_DIR) && terraform init

terraform-validate:
	cd $(TF_DIR) && terraform validate

terraform-plan:
	@# Load .env and export Terraform variables
	set -a; [ -f .env ] && . .env; set +a; \
	if [ -n "$$S3_BUCKET" ]; then \
	  export TF_VAR_bucket_name="$$S3_BUCKET"; \
	fi; \
	if [ -n "$$NCBI_EMAIL" ]; then \
	  export TF_VAR_ncbi_email="$$NCBI_EMAIL"; \
	fi; \
	if [ -n "$$NCBI_API_KEY" ]; then \
	  export TF_VAR_ncbi_api_key="$$NCBI_API_KEY"; \
	fi; \
	if [ -n "$$OPENSEARCH_ADMIN_PRINCIPAL" ]; then \
	  export TF_VAR_opensearch_admin_principals='["'$$OPENSEARCH_ADMIN_PRINCIPAL'"]'; \
	fi; \
	cd $(TF_DIR) && terraform plan

terraform-apply:
	@# Load .env and export Terraform variables
	set -a; [ -f .env ] && . .env; set +a; \
	if [ -n "$$S3_BUCKET" ]; then \
	  export TF_VAR_bucket_name="$$S3_BUCKET"; \
	fi; \
	if [ -n "$$NCBI_EMAIL" ]; then \
	  export TF_VAR_ncbi_email="$$NCBI_EMAIL"; \
	fi; \
	if [ -n "$$NCBI_API_KEY" ]; then \
	  export TF_VAR_ncbi_api_key="$$NCBI_API_KEY"; \
	fi; \
	if [ -n "$$OPENSEARCH_ADMIN_PRINCIPAL" ]; then \
	  export TF_VAR_opensearch_admin_principals='["'$$OPENSEARCH_ADMIN_PRINCIPAL'"]'; \
	fi; \
	cd $(TF_DIR) && terraform apply -auto-approve

# Docker & Deployment
# build-ui: build image only (no AWS creds required). build-push-ui: build + push to ECR.
build-ui:
	@if [ -z "$(VERSION)" ]; then \
	  echo "VERSION file missing. Create VERSION (e.g. 0.0.4)."; \
	  exit 1; \
	fi
	docker build --build-arg VERSION=$(VERSION) -t "$(REPO_NAME):$(IMAGE_TAG)" ui/
	@echo "UI image built locally. To push to ECR (requires AWS creds): make build-push-ui"

build-push-ui: build-ui
	@if [ -z "$(ACCOUNT_ID)" ]; then \
	  echo "ACCOUNT_ID is not set and could not be derived from aws sts. Set ACCOUNT_ID env var."; \
	  exit 1; \
	fi
	aws ecr get-login-password --region "$(AWS_REGION)" | docker login --username AWS --password-stdin "$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com"
	docker tag "$(REPO_NAME):$(IMAGE_TAG)" "$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(REPO_NAME):$(IMAGE_TAG)"
	docker push "$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(REPO_NAME):$(IMAGE_TAG)"
	@echo "UI image built and pushed. Run 'make terraform-apply' to update infrastructure."

# Versioning
bump-patch:
	bump2version patch

bump-minor:
	bump2version minor

bump-major:
	bump2version major

tag-release:
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
