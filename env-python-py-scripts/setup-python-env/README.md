# 🛠️ dev-setup-kit

> **AI-powered developer environment installer — Python + PyCharm + plugins, fully automated.**
> Powered by **Ollama** (local LLM, zero API key, zero cloud). One command to rule them all.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-1C3557)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-black?logo=ollama)
![Docker](https://img.shields.io/badge/Docker-multi--stage-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/github/actions/workflow/status/your-username/dev-setup-kit/ci.yml?label=CI&logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000)
![Linter: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)

---

## What it does

`dev-setup-kit` is a growing collection of **AI-powered Python automation scripts** for developer tooling.
The first script — `setup_dev_env.py` — installs the latest stable Python and PyCharm Community,
then installs 25 curated PyCharm plugins, runs 9 system health checks, and uses a **local Ollama LLM**
to suggest fixes if anything goes wrong.

```
setup_dev_env.py
      ↓
[System checks]       — OS · Admin · ExecutionPolicy · winget · disk · internet · pip · Ollama
      ↓
[Version fetch]       — python.org API + JetBrains API → latest stable versions
      ↓
[Install Python]      — winget first, direct download fallback (silent, adds to PATH)
      ↓
[Install PyCharm]     — winget first, direct download fallback (silent)
      ↓
[Install 25 plugins]  — VCS · AI · Python · LangChain · Docker · Quality
      ↓
[Post-install checks] — venv creation test · module imports · PATH verification
      ↓
[Report]              — coloured summary + AI fix suggestions for any error
```

**If anything fails**, the local Ollama LLM (Mistral, Llama3, Codellama…) is asked for a
Windows-specific fix in 3 steps. No cloud API key needed — everything runs locally.

---

## Why Ollama instead of a cloud LLM?

| | Cloud LLM (OpenAI / Anthropic) | Ollama (this project) |
|---|---|---|
| API key | Required | ❌ Not needed |
| Data privacy | Sent to cloud | ✅ Stays on your machine |
| Cost | Per token | ✅ Free |
| Works offline | ❌ No | ✅ Yes |
| Setup | `export API_KEY=...` | `ollama serve` |

---

## Repository structure

```
dev-setup-kit/
├── scripts/
│   ├── __init__.py
│   └── setup_dev_env.py          # ★ AI-powered Python + PyCharm installer
│   └── (more scripts coming…)
├── tests/
│   ├── __init__.py
│   └── test_setup_dev_env.py     # Unit tests — Ollama fully mocked
├── .github/
│   └── workflows/
│       └── ci.yml                # CI: lint → test → security → build → dry-run
├── Dockerfile                    # Multi-stage: builder → runtime → ci
├── docker-compose.yml            # 7 services: ollama · app · lint · format · test · security
├── pyproject.toml                # Single source of truth: deps + ruff + black + mypy + pytest
├── .pre-commit-config.yaml       # 7 hook groups: ruff · black · isort · mypy · bandit · hadolint
├── Makefile                      # 20 convenience targets
├── .gitignore
├── .dockerignore
├── .env.example
├── CHANGELOG.md
└── README.md
```

---

## Quick start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Ollama | latest | [ollama.com/download](https://ollama.com/download) |
| Docker | 24+ | [docs.docker.com](https://docs.docker.com/get-docker/) *(optional)* |
| Git | 2.40+ | [git-scm.com](https://git-scm.com/) |

### 1. Clone and install

```bash
git clone https://github.com/your-username/dev-setup-kit.git
cd dev-setup-kit

python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# OR
.venv\Scripts\Activate.ps1      # Windows PowerShell

pip install -e ".[dev]"
```

### 2. Start Ollama

```bash
# Install Ollama if not done: https://ollama.com/download
ollama serve                    # keep running in a separate terminal
ollama pull mistral             # download the default model (~4 GB)
```

### 3. Run the installer

```bash
# Dry-run — see what would happen, install nothing
python scripts/setup_dev_env.py --dry-run

# Full install (Python + PyCharm + 25 plugins)
python scripts/setup_dev_env.py

# Use a different Ollama model
python scripts/setup_dev_env.py --model llama3.2

# Skip PyCharm plugins (faster)
python scripts/setup_dev_env.py --skip-plugins

# Force reinstall even if already present
python scripts/setup_dev_env.py --force
```

---

## CLI reference

```
python scripts/setup_dev_env.py [OPTIONS]

Options:
  --dry-run             Show plan without installing anything
  --force               Reinstall even if already present
  --model MODEL         Ollama model for fix suggestions (default: mistral)
  --ollama-url URL      Ollama server URL (default: http://localhost:11434)
  --skip-python         Skip Python installation
  --skip-pycharm        Skip PyCharm installation
  --skip-plugins        Skip PyCharm plugin installation
```

---

## PyCharm plugins installed (25 total)

| Category | Plugins |
|----------|---------|
| **VCS** | Git, GitHub, .ignore, GitToolBox |
| **AI** | GitHub Copilot, JetBrains AI Assistant |
| **Python** | Python Core, Python Envs, Requirements, TOML |
| **LangChain / Jupyter** | Jupyter, Prettier, Swagger/OpenAPI |
| **Docker / DevOps** | Docker, Kubernetes, CSV Editor |
| **Quality** | SonarLint, CheckStyle, Rainbow Brackets, String Manipulation, Markdown, .env support, ideolog |

---

## Ollama model selection

The script picks the best available model automatically:

```
Requested model available?  → use it
Else: try RECOMMENDED_MODELS in order:
      mistral → llama3.2 → llama3 → codellama → phi3 → gemma2
Else: use any available model
Else: disable AI suggestions (install continues without LLM)
```

Pull your preferred model before running:

```bash
ollama pull mistral      # 4.1 GB — best balance
ollama pull llama3.2     # 2.0 GB — lighter
ollama pull codellama    # 3.8 GB — code-focused
ollama pull phi3         # 2.3 GB — very fast
```

---

## Docker

### Run with Docker Compose

```bash
# Copy env file
cp .env.example .env

# Start Ollama + pull model + run dry-run installer
docker compose --profile full up

# Individual services
docker compose --profile ollama up -d ollama     # start LLM server only
docker compose --profile lint run --rm lint      # lint check
docker compose --profile format run --rm format  # auto-format (writes back)
docker compose --profile test run --rm test      # run tests
docker compose --profile security run --rm security  # security scan
```

### Docker services

| Service | Profile | What it does |
|---------|---------|--------------|
| `ollama` | `ollama`, `full` | Local LLM server (persists models in a named volume) |
| `ollama-pull` | `ollama`, `full` | Pulls `$OLLAMA_MODEL` once on startup |
| `app` | `app`, `full` | Runs `setup_dev_env.py --dry-run` |
| `lint` | `lint`, `ci` | ruff + black + isort + mypy |
| `format` | `format` | Auto-fix formatting (writes back to host) |
| `test` | `test`, `ci` | pytest + coverage |
| `security` | `security`, `ci` | bandit + pip-audit |

### Build the image directly

```bash
# Latest Python (3.14 by default)
docker build -t dev-setup-kit .

# Specific Python version
docker build --build-arg PYTHON_VERSION=3.13 -t dev-setup-kit:py313 .
```

---

## Makefile targets

```bash
make help              # list all targets

# Dev setup
make install           # pip install -e ".[dev]"
make pre-commit-install

# Code quality (local)
make lint              # ruff + black + isort + mypy
make format            # auto-fix all formatting
make test              # pytest + coverage
make security          # bandit + pip-audit

# Ollama
make ollama-start      # docker compose up ollama
make ollama-pull       # pull default model
make ollama-stop

# Script
make dry-run           # setup_dev_env.py --dry-run
make run               # setup_dev_env.py (full install)

# Docker
make docker-build
make docker-lint
make docker-test
make docker-down
make clean
```

---

## CI/CD pipeline

Five jobs run on every push and pull request:

| Job | Trigger | What it does |
|-----|---------|--------------|
| `lint` | Every push + PR | ruff · black · isort · mypy |
| `test` | After lint | pytest matrix (Python 3.11 / 3.12 / 3.13) + Codecov |
| `security` | After lint | bandit (SAST) · pip-audit (CVE scan) |
| `build` | After test + security (main only) | Docker multi-stage build + push to GHCR |
| `dry-run` | After test | Smoke test: run installer in dry-run mode |
| `ci-gate` | After all jobs | Required status check for branch protection |

### GitHub Secrets to configure

```
GITHUB_TOKEN    # auto-injected by GitHub Actions
```

*(No other secrets needed — Ollama runs locally, not in CI. The dry-run job gracefully handles missing Ollama.)*

---

## Code quality

This project uses a strict quality stack:

| Tool | Role | Config |
|------|------|--------|
| **ruff** | Linter + import sorter + formatter | `pyproject.toml` |
| **black** | Code formatter | `pyproject.toml` |
| **isort** | Import ordering | `pyproject.toml` |
| **mypy** | Static type checking | `pyproject.toml` |
| **bandit** | Security SAST | `pyproject.toml` |
| **pip-audit** | CVE dependency scan | — |
| **pre-commit** | Git hook automation | `.pre-commit-config.yaml` |
| **pytest** | Test runner | `pyproject.toml` |
| **pytest-cov** | Coverage (≥ 60% enforced) | `pyproject.toml` |

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `mistral` | Model for fix suggestions |
| `PYTHON_VERSION` | `3.14` | Python version for Docker build |

Copy `.env.example` to `.env` and adjust as needed.

---

## System checks

The installer runs 9 checks before installing anything:

| Check | What it verifies | Fix on failure |
|-------|-----------------|----------------|
| OS | Windows 10/11 detected | Warning only on Linux/macOS |
| Admin rights | Running as Administrator | Right-click → Run as Admin |
| PS ExecutionPolicy | RemoteSigned or higher | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| winget | Available in PATH | Install App Installer from Microsoft Store |
| Python (existing) | Current Python version | — |
| PyCharm (existing) | Existing installation | — |
| Disk space | ≥ 3 GB free on C: | Free disk space |
| Internet | python.org reachable | Check proxy / firewall |
| pip | Available | `python -m ensurepip --upgrade` |
| Ollama | Server reachable + models pulled | `ollama serve` + `ollama pull mistral` |

---

## Adding new scripts

This repo is designed to grow. To add a new automation script:

1. Create `scripts/your_script.py`
2. Add its tests in `tests/test_your_script.py`
3. The CI pipeline picks it up automatically (lint + test cover `scripts/`)
4. Document it in this README under a new section
5. Add an entry to `CHANGELOG.md`

---

## Roadmap

- [ ] `setup_git.py` — configure Git (user, SSH key, GPG signing, .gitconfig)
- [ ] `setup_wsl.py` — install and configure WSL2 + Ubuntu
- [ ] `setup_node.py` — install Node.js LTS + global packages (npm, npx, nvm)
- [ ] `setup_docker.py` — install Docker Desktop + configure daemon
- [ ] `setup_vscode.py` — install VS Code + extensions equivalent to PyCharm plugins
- [ ] `setup_ollama.py` — install Ollama + pull recommended models automatically
- [ ] Web dashboard — React UI to trigger scripts and view reports

---

## Contributing

```bash
# Fork → clone → branch
git checkout -b feat/your-feature

# Install dev deps
make install
make pre-commit-install

# Make changes, then
make format       # auto-fix formatting
make lint         # check
make test         # verify tests pass

# Commit (pre-commit hooks run automatically)
git commit -m "feat: your feature"
git push origin feat/your-feature
# Open a Pull Request
```

---

## License

MIT © 2026 — see [LICENSE](LICENSE)

---

*README last updated: June 2026 · v1.0.0*
