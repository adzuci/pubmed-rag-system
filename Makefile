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

.PHONY: precommit-install precommit-run clean-notebooks test run-ui run-fetch run-process terraform-init terraform-validate terraform-plan terraform-apply build-push-ui bump-patch bump-minor bump-major tag-release

# Development Tools
precommit-install:
	$(PYTHON) -m pre_commit install

precommit-run:
	$(PYTHON) -m pre_commit run --all-files

clean-notebooks:
	$(PYTHON) -m nbstripout $(NOTEBOOK_DIR)/*.ipynb

test:
	set -a; [ -f .env ] && . .env; set +a; PYTHONPATH=. $(PYTHON) -m pytest -q

# Local Development
run-ui:
	set -a; [ -f .env ] && . .env; set +a; streamlit run ui/app.py

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
build-push-ui:
	@if [ -z "$(VERSION)" ]; then \
	  echo "VERSION file missing. Create VERSION (e.g. 0.0.4)."; \
	  exit 1; \
	fi
	@if [ -z "$(ACCOUNT_ID)" ]; then \
	  echo "ACCOUNT_ID is not set and could not be derived from aws sts. Set ACCOUNT_ID env var."; \
	  exit 1; \
	fi
	aws ecr get-login-password --region "$(AWS_REGION)" | docker login --username AWS --password-stdin "$(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com"
	docker build --build-arg VERSION=$(VERSION) -t "$(REPO_NAME):$(IMAGE_TAG)" ui/
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
