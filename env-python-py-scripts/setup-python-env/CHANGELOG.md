# Changelog

All notable changes to **dev-setup-kit** are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/).

---

## [1.0.0] — 2026-06-26

### Added
- `scripts/setup_dev_env.py` — AI-powered installer for Python + PyCharm + plugins
- Ollama backend (local LLM, zero API key) via `langchain-ollama` + `ChatOllama`
- Auto model selection: picks best available Ollama model, falls back gracefully
- 9 system checks: OS, admin rights, PS ExecutionPolicy, winget, disk space, internet, pip, Ollama
- Automatic venv creation test (catches the `venvlauncher.exe` Windows bug)
- 25 PyCharm plugins across 6 categories: VCS, AI, Python, LangChain/Jupyter, Docker, Quality
- `--dry-run`, `--force`, `--model`, `--ollama-url`, `--skip-*` CLI flags
- Multi-stage Dockerfile (builder → runtime → ci) with `PYTHON_VERSION` ARG
- `docker-compose.yml` with 6 services: ollama, ollama-pull, app, lint, format, test, security
- GitHub Actions CI pipeline: lint → test (matrix 3.11/3.12/3.13) → security → build → dry-run → gate
- `pyproject.toml` as single source of truth (ruff, black, isort, mypy, pytest, coverage, bandit)
- `.pre-commit-config.yaml` with 7 hook groups
- `Makefile` with 20 convenience targets
- `.gitignore`, `.dockerignore`, `.env.example`
- Unit test suite (20+ tests, Ollama fully mocked)
