# Makefile — shortcuts for common qa-toolbox-precommit dev tasks
# Usage: make <target>
# Requires: make installed (native on macOS/Linux; use "choco install make" on Windows)

VENV   = .venv
PYTHON = $(VENV)/bin/python   # Windows: change to $(VENV)/Scripts/python
PIP    = $(VENV)/bin/pip      # Windows: change to $(VENV)/Scripts/pip

.PHONY: install lint test audit clean help

help:                          ## show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*##"}; {printf "  %-12s %s\n", $$1, $$2}'

install:                       ## create venv, install all tools, activate pre-commit hooks
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install pre-commit pip-audit detect-secrets gitlint black ruff mypy bandit vulture pytest pytest-cov
	detect-secrets scan > .secrets.baseline
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "Setup complete. Run: source .venv/bin/activate"

lint:                          ## run all pre-commit hooks on all files without committing
	pre-commit run --all-files

test:                          ## run pytest with coverage (fails if coverage < 80%)
	$(PYTHON) -m pytest

audit:                         ## scan dependencies for known CVEs via pip-audit
	$(VENV)/bin/pip-audit

clean:                         ## remove venv and all cache directories
	rm -rf $(VENV) .mypy_cache .ruff_cache .pytest_cache __pycache__ coverage.xml .coverage
