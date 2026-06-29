# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Dockerfile — dev-setup-kit                                              ║
# ║  Multi-stage build: builder → runtime                                    ║
# ║  Automatically uses the latest stable Python from python:slim            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── ARG: change Python version here or override at build time ────────────────
#   docker build --build-arg PYTHON_VERSION=3.14 .
ARG PYTHON_VERSION=3.14

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  STAGE 1 — builder                                                       ║
# ║  Installs all dependencies in an isolated layer                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
FROM python:${PYTHON_VERSION}-slim AS builder

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency spec first (layer cache optimisation)
COPY pyproject.toml ./

# Install production + dev dependencies into a prefix
RUN pip install --upgrade pip setuptools wheel \
 && pip install --prefix=/install ".[dev]"


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  STAGE 2 — runtime                                                       ║
# ║  Lean image: only what is needed to run the scripts                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Ollama — override at runtime with -e or docker-compose env
    OLLAMA_BASE_URL=http://ollama:11434 \
    OLLAMA_MODEL=mistral \
    # Locale
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Minimal runtime system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy project source
COPY scripts/ ./scripts/
COPY tests/   ./tests/
COPY pyproject.toml ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

# Health check: verify Python version and key imports
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import langchain, requests, rich; print('ok')" || exit 1

# Default: run the installer in dry-run mode
# Override CMD in docker-compose or at runtime
CMD ["python", "-m", "scripts.setup_dev_env", "--dry-run"]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  STAGE 3 — ci  (linting + testing, used in GitHub Actions)              ║
# ╚══════════════════════════════════════════════════════════════════════════╝
FROM runtime AS ci

USER root
# Install dev tools that aren't in runtime
RUN pip install --no-cache-dir ruff black isort mypy bandit pytest pytest-cov pytest-mock
USER appuser
