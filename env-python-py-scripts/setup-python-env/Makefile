# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Makefile — dev-setup-kit                                                ║
# ║  Shortcuts for common dev tasks                                          ║
# ║  Usage: make <target>                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

.PHONY: help install lint format test security dry-run \
        ollama-start ollama-pull ollama-stop \
        docker-build docker-up docker-down \
        pre-commit-install clean

PYTHON     ?= python
PIP        ?= pip
OLLAMA_URL ?= http://localhost:11434
MODEL      ?= mistral

# ── Default target ────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  dev-setup-kit — available targets"
	@echo ""
	@echo "  Dev setup"
	@echo "    make install            Install all dependencies (incl. dev)"
	@echo "    make pre-commit-install Setup pre-commit hooks"
	@echo ""
	@echo "  Code quality"
	@echo "    make lint               Run ruff + black + isort + mypy"
	@echo "    make format             Auto-fix formatting (ruff + black + isort)"
	@echo "    make test               Run pytest + coverage"
	@echo "    make security           Run bandit + pip-audit"
	@echo ""
	@echo "  Ollama (local LLM)"
	@echo "    make ollama-start       Start Ollama via Docker Compose"
	@echo "    make ollama-pull        Pull default model ($(MODEL))"
	@echo "    make ollama-stop        Stop Ollama"
	@echo ""
	@echo "  Script"
	@echo "    make dry-run            Run installer in dry-run mode"
	@echo "    make run                Run installer (installs Python + PyCharm)"
	@echo ""
	@echo "  Docker"
	@echo "    make docker-build       Build all Docker images"
	@echo "    make docker-lint        Run lint inside Docker"
	@echo "    make docker-test        Run tests inside Docker"
	@echo "    make docker-down        Stop and remove containers"
	@echo ""
	@echo "  Cleanup"
	@echo "    make clean              Remove caches and temp files"
	@echo ""

# ── Dev setup ─────────────────────────────────────────────────────────────────
install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

pre-commit-install:
	pre-commit install
	pre-commit install --hook-type commit-msg

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	@echo "── ruff ──"
	ruff check scripts/ tests/ --output-format=concise
	@echo "── ruff format check ──"
	ruff format --check scripts/ tests/
	@echo "── black check ──"
	black --check scripts/ tests/
	@echo "── isort check ──"
	isort --check-only scripts/ tests/
	@echo "── mypy ──"
	mypy scripts/ || true
	@echo "✅ Lint done"

format:
	@echo "── ruff format (fix) ──"
	ruff format scripts/ tests/
	@echo "── ruff check --fix ──"
	ruff check --fix scripts/ tests/
	@echo "── black ──"
	black scripts/ tests/
	@echo "── isort ──"
	isort scripts/ tests/
	@echo "✅ Formatting applied"

test:
	pytest tests/ -v --tb=short \
		--cov=scripts \
		--cov-report=term-missing \
		--cov-report=html:coverage-reports/htmlcov

security:
	@echo "── bandit ──"
	bandit -r scripts/ -c pyproject.toml -ll || true
	@echo "── pip-audit ──"
	pip-audit --desc || true
	@echo "✅ Security scan done"

# ── Ollama ────────────────────────────────────────────────────────────────────
ollama-start:
	docker compose --profile ollama up -d ollama
	@echo "✅ Ollama started at $(OLLAMA_URL)"

ollama-pull:
	docker compose run --rm ollama-pull
	@echo "✅ Model '$(MODEL)' pulled"

ollama-stop:
	docker compose --profile ollama stop ollama

# ── Script ────────────────────────────────────────────────────────────────────
dry-run:
	$(PYTHON) scripts/setup_dev_env.py \
		--dry-run \
		--model $(MODEL) \
		--ollama-url $(OLLAMA_URL)

run:
	$(PYTHON) scripts/setup_dev_env.py \
		--model $(MODEL) \
		--ollama-url $(OLLAMA_URL)

# ── Docker ────────────────────────────────────────────────────────────────────
docker-build:
	docker compose build

docker-lint:
	docker compose --profile lint run --rm lint

docker-format:
	docker compose --profile format run --rm format

docker-test:
	docker compose --profile test run --rm test

docker-security:
	docker compose --profile security run --rm security

docker-down:
	docker compose --profile full --profile ci --profile ollama down --remove-orphans

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "coverage.xml" -delete 2>/dev/null || true
	rm -rf htmlcov/ coverage-reports/ dist/ build/
	@echo "✅ Clean done"
