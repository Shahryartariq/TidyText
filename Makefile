# TidyText shortcuts. Run `make` to see them all.
# On Windows, this needs Git for Windows (for its bash) or WSL.

SHELL := /bin/bash
.DEFAULT_GOAL := help

VENV   ?= .venv

# Windows venvs keep executables in Scripts/, and `python3` is usually just
# the Microsoft Store stub, so pick the first real interpreter on PATH.
ifeq ($(OS),Windows_NT)
  # From PowerShell or cmd there is no /bin/bash, so borrow Git's.
  GIT_BASH ?= C:/Program Files/Git/bin/bash.exe
  ifneq ($(wildcard $(subst $() ,\ ,$(GIT_BASH))),)
    SHELL := $(GIT_BASH)
  endif
  ifeq ($(shell echo "x"),"x")
    $(error The recipes need bash. Install Git for Windows, or set GIT_BASH to its bash.exe)
  endif
  BIN    := $(VENV)/Scripts
  EXE    := .exe
  PYTHON ?= $(firstword $(foreach p,py python3.14 python3.13 python3.12,$(if $(shell command -v $(p) 2>/dev/null),$(p))) python)
else
  BIN    := $(VENV)/bin
  PYTHON ?= python3
endif
PY     := $(BIN)/python$(EXE)
PORT   ?= 8000
IMAGE  ?= tidytext
TAG    ?= latest
GIT_SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo local)

# Settings used by tests and checks (production-like, throwaway key).
TEST_ENV := DJANGO_SECRET_KEY=test-only-key DJANGO_DEBUG=0

.PHONY: help
help: ## Show this list
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\n"} \
	/^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2} \
	/^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5)}' $(MAKEFILE_LIST)

##@ Setup

$(PY):
	$(PYTHON) -m venv $(VENV)

.PHONY: install
install: $(PY) ## Create the virtualenv and install dev dependencies
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-dev.txt

.PHONY: env
env: ## Create a .env file from .env.example with a fresh secret key
	@test -f .env && echo ".env already exists" || \
	  (sed "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$$($(PY) -c 'import secrets; print(secrets.token_urlsafe(50))')|" .env.example > .env && echo "Created .env")

.PHONY: secret
secret: ## Print a new random DJANGO_SECRET_KEY
	@$(PY) -c "import secrets; print(secrets.token_urlsafe(50))"

##@ Develop

.PHONY: dev
dev: ## Run the development server with auto-reload (http://localhost:8000)
	DJANGO_DEBUG=1 $(PY) manage.py runserver $(PORT)

.PHONY: serve
serve: ## Run like production locally, with Gunicorn
	$(PY) manage.py collectstatic --noinput >/dev/null
	DJANGO_DEBUG=0 $(BIN)/gunicorn tidytext.wsgi:application --config gunicorn.conf.py

.PHONY: cases
cases: ## Regenerate the shared test cases from scripts/case_inputs.json
	$(PY) scripts/build_cases.py

.PHONY: assets
assets: ## Redraw icons and the social sharing card
	$(PY) scripts/generate_assets.py

##@ Quality

.PHONY: test
test: test-py test-js ## Run all tests

.PHONY: test-py
test-py: ## Run the Python tests
	$(TEST_ENV) $(PY) manage.py test

.PHONY: test-js
test-js: ## Run the JavaScript tests (Node 20+)
	node --test tests/js/transforms.test.mjs

.PHONY: lint
lint: ## Check code style and common bugs
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

.PHONY: format
format: ## Auto-format and auto-fix code
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

.PHONY: check
check: ## Run Django's production deployment checks
	DJANGO_DEBUG=0 DJANGO_SECURE_SSL_REDIRECT=1 DJANGO_SECRET_KEY=$$($(PY) -c 'import secrets; print(secrets.token_urlsafe(50))') \
	  $(PY) manage.py check --deploy --fail-level WARNING

.PHONY: ci
ci: lint test check ## Everything CI runs: lint, tests, deploy checks

##@ Docker

.PHONY: docker-build
docker-build: ## Build the production image
	docker build --build-arg GIT_SHA=$(GIT_SHA) -t $(IMAGE):$(TAG) .

.PHONY: docker-run
docker-run: docker-build ## Build and run the image on http://localhost:8000
	docker run --rm -p $(PORT):8000 --read-only --tmpfs /tmp --cap-drop ALL \
	  -e DJANGO_SECRET_KEY=$$($(PY) -c 'import secrets; print(secrets.token_urlsafe(50))') $(IMAGE):$(TAG)

.PHONY: up
up: ## Start with docker compose in the background (needs .env, see `make env`)
	GIT_SHA=$(GIT_SHA) docker compose up -d --build

.PHONY: down
down: ## Stop docker compose
	docker compose down

.PHONY: logs
logs: ## Follow docker compose logs
	docker compose logs -f

##@ Release

.PHONY: release
release: ci ## Tag a release: make release VERSION=1.0.1
	@test -n "$(VERSION)" || (echo "Usage: make release VERSION=x.y.z" && exit 1)
	@git diff --quiet || (echo "Commit your changes first." && exit 1)
	git tag -a v$(VERSION) -m "TidyText v$(VERSION)"
	git push origin v$(VERSION)

##@ Cleanup

.PHONY: clean
clean: ## Remove caches and collected static files
	rm -rf staticfiles .ruff_cache
	find . -name __pycache__ -type d -prune -not -path "./$(VENV)/*" -exec rm -rf {} +
