<div align="center">

# 🛡️ qa-toolbox-precommit

### Production-grade pre-commit stack for Python QA teams

*Security · Formatting · Type safety · Dead code · Secret scanning · Coverage · Conventional Commits*

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![ruff](https://img.shields.io/badge/linter-ruff-orange)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/types-mypy%20strict-informational)](https://mypy-lang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Khalid%20HAFID--MEDHEB-black)](https://www.linkedin.com/in/khalid-hafidmedheb-40451aa8)

</div>

---

## 📌 What is this?

A plug-and-play pre-commit configuration for **Python-only QA automation repositories**.

Drop the four files into any Python repo, run `make install`, and every `git commit` will automatically enforce 10 quality gates — before the code ever reaches CI.

**Problems it solves:**

| Without this | With this |
|---|---|
| Style inconsistencies slow down code reviews | `black` + `ruff` auto-fix formatting on every commit |
| Type bugs discovered at runtime | `mypy --strict` catches them at commit time |
| Secrets accidentally pushed to GitHub | `detect-secrets` blocks credentials in diffs |
| CVEs in dependencies go unnoticed | `pip-audit` scans on every commit |
| Insecure patterns slip through review | `bandit` flags shell injection, hardcoded passwords |
| Dead code accumulates silently | `vulture` detects unused functions and imports |
| Vague commit messages ("fix stuff") | `gitlint` enforces Conventional Commits format |
| Coverage regressions in PRs | `pytest-cov` fails the commit if coverage drops below 80% |

---

## 🗂 Repository structure

```
qa-toolbox-precommit/
├── .pre-commit-config.yaml   # hook definitions (copy this into your repo)
├── pyproject.toml            # tool configuration: black, ruff, mypy, bandit, pytest-cov
├── .gitlint                  # commit message rules (Conventional Commits)
├── Makefile                  # shortcuts: make install / lint / test / audit
├── .gitignore                # standard Python ignores
└── README.md                 # this file
```

---

## ⚡ Quick start (3 commands)

```bash
# 1. Clone this repo or copy the four config files into your project root
git clone https://github.com/kallitests/qa-toolbox-precommit.git

# 2. Install everything (venv + tools + hooks)
make install

# 3. Verify the full stack runs clean
make lint
```

> **Windows users:** replace `make install` with the PowerShell commands in the Installation section below.

---

## 🏗 Hook architecture

The `.pre-commit-config.yaml` groups hooks into **8 categories**, executed in this order on every `git commit`:

```
git commit
    │
    ├── 1. FILE HYGIENE        trailing whitespace · line endings · large files · merge conflicts
    ├── 2. FORMATTING          black (auto-fix)
    ├── 3. LINTING             ruff (auto-fix) · complexity check · import order
    ├── 4. TYPE CHECKING       mypy --strict
    ├── 5. DEAD CODE           vulture (80% confidence threshold)
    ├── 6. SECRETS             detect-secrets (baseline diff)
    ├── 7. SAST                bandit (insecure patterns)
    ├── 8. DEPENDENCIES        pip-audit (CVE scan)
    └── 9. COMMIT MESSAGE      gitlint (Conventional Commits) ← runs at commit-msg stage
```

If any hook fails, the commit is **blocked** and the error is displayed with the fix to apply.

---

## 🔧 Hook reference

### File hygiene — `pre-commit-hooks v4.6.0`

| Hook | What it catches |
|---|---|
| `trailing-whitespace` | Trailing spaces that pollute diffs |
| `end-of-file-fixer` | Missing newline at end of file |
| `mixed-line-ending` | CRLF line endings (normalises to LF) |
| `check-added-large-files` | Files over 500 KB (accidental binaries, datasets) |
| `check-merge-conflict` | Leftover `<<<<<<<` / `>>>>>>>` markers |
| `check-yaml` / `check-toml` / `check-json` | Syntax errors in config files |
| `detect-private-key` | RSA/PEM private keys accidentally staged |

### Formatting — `black 24.4.2`

Auto-formats all Python files to a consistent style. Line length: **88**. No configuration needed — black is intentionally opinionated.

### Linting & complexity — `ruff v0.4.9`

Replaces `flake8` + `isort` + `pyupgrade` + parts of `pylint` in a single tool that runs **10–100x faster**. Enabled rule sets: `E W F I C90 UP B S`. Auto-fixes safe violations on every commit.

### Type checking — `mypy v1.10.0`

Runs in `--strict` mode: no untyped function definitions, no implicit `Optional`, full type inference. Scoped to changed files only by pre-commit — stays under 5 seconds.

### Dead code — `vulture v2.11`

Detects unused functions, classes, variables, and imports at **80% confidence** to avoid false positives on dynamically called code.

### Secret scanning — `detect-secrets v1.5.0`

Diffs every staged file against the `.secrets.baseline`. Blocks commits that introduce new credentials (API keys, tokens, passwords, connection strings). The baseline file must be committed to the repo.

### SAST — `bandit 1.7.9`

Static Application Security Testing: flags shell injection (`subprocess` with `shell=True`), hardcoded passwords, use of `eval()`, weak cryptography, and 30+ other insecure patterns. Configured via `pyproject.toml` — `assert` statements are excluded (B101) since they are valid in pytest.

### Dependency scan — `pip-audit` (local hook)

Scans the active Python environment against the OSV and PyPI Advisory databases for known CVEs. Runs on every commit regardless of which files changed.

### Commit message — `gitlint v0.19.1`

Enforces **Conventional Commits** format at the `commit-msg` stage:

```
type(scope): description
│     │       └─ what changed, in plain English, under 72 chars
│     └─ optional: affected module/component
└─ feat | fix | chore | docs | test | refactor | perf | ci | build
```

**Valid examples:**
```
feat(parser): add Playwright JSON report ingestion
fix(ci): correct pip-audit path on Windows
test(fixtures): add edge-case data for empty report files
chore: bump black to 24.4.2
```

**Rejected examples:**
```
fix                      ← too short, no description
added stuff              ← no type prefix
WIP: cleaning up         ← not a valid type
```

---

## 📦 Tool versions (pinned)

| Tool | Version | Replaces |
|---|---|---|
| pre-commit-hooks | v4.6.0 | — |
| black | 24.4.2 | autopep8 |
| ruff | v0.4.9 | flake8 + isort + pyupgrade + pylint |
| mypy | v1.10.0 | — |
| vulture | v2.11 | — |
| detect-secrets | v1.5.0 | trufflehog (Python-only alternative) |
| bandit | 1.7.9 | — |
| pip-audit | latest installed | safety (free, no API key) |
| gitlint | v0.19.1 | commitlint (Python-native alternative) |

> All hooks use **pinned exact versions** — never `latest` or branch names — to guarantee identical behaviour across all developer machines and CI environments.

---

## 🔐 Secret scanning setup

`detect-secrets` requires a one-time baseline initialisation per repo:

```bash
# Generate the baseline (scans all existing files and records known findings)
detect-secrets scan > .secrets.baseline

# Commit the baseline — it must be tracked in git
git add .secrets.baseline
git commit -m "chore: initialise detect-secrets baseline"
```

From that point on, `detect-secrets` only flags **new** secrets introduced in each commit diff.

If a finding is a false positive (e.g. a test fixture that looks like a key):

```bash
# Audit and mark the false positive as reviewed
detect-secrets audit .secrets.baseline

# Commit the updated baseline
git add .secrets.baseline && git commit -m "chore: update secrets baseline"
```

---

## 🖥 Installation

### macOS / Linux

```bash
git clone https://github.com/kallitests/qa-toolbox-precommit.git
cd qa-toolbox-precommit
make install
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
git clone https://github.com/kallitests/qa-toolbox-precommit.git
cd qa-toolbox-precommit

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install pre-commit pip-audit detect-secrets gitlint black ruff mypy bandit vulture pytest pytest-cov

detect-secrets scan > .secrets.baseline

pre-commit install
pre-commit install --hook-type commit-msg

pre-commit run --all-files
```

---

## 🛠 Makefile reference

```
make help       list all available targets
make install    create venv · install tools · activate hooks · init secrets baseline
make lint       run all hooks on all files (without committing)
make test       run pytest with coverage (fails if coverage < 80%)
make audit      scan dependencies for CVEs via pip-audit
make clean      remove .venv and all cache directories
```

---

## ⚙️ Configuration reference

All tool settings live in `pyproject.toml` — no separate `.flake8`, `.mypy.ini`, or `setup.cfg`.

| Section | Key setting |
|---|---|
| `[tool.black]` | `line-length = 88`, `target-version = py311` |
| `[tool.ruff.lint]` | rules: E W F I C90 UP B S · `max-complexity = 10` |
| `[tool.mypy]` | `strict = true` · `ignore_missing_imports = true` |
| `[tool.bandit]` | excludes `tests/` · skips B101 (assert) |
| `[tool.pytest.ini_options]` | `--cov-fail-under=80` · `testpaths = ["tests"]` |

To adjust coverage threshold: change `--cov-fail-under=80` in `pyproject.toml`.
To adjust complexity limit: change `max-complexity = 10` under `[tool.ruff.lint.mccabe]`.

---

## 🔁 Using this in your own repo

Copy these four files into your Python project root:

```
.pre-commit-config.yaml
pyproject.toml
.gitlint
Makefile
```

Then run `make install`. That is all.

If you already have a `pyproject.toml`, merge only the relevant `[tool.*]` sections.

---

## 🚀 Real-world example — `SmokeSentinel`

This section shows exactly how to apply `qa-toolbox-precommit` to an existing Python repo: **[khafid1506/SmokeSentinel](https://github.com/khafid1506/SmokeSentinel)**.

### Context

SmokeSentinel is a Python-based smoke test monitoring tool. Its scripts are the exact target audience for this pre-commit stack: automation code that runs in CI, touches external APIs, and is maintained by a QA team.

### Step-by-step integration

```bash
# 1. Clone SmokeSentinel
git clone https://github.com/khafid1506/SmokeSentinel.git
cd SmokeSentinel

# 2. Copy the four config files from qa-toolbox-precommit into the repo root
curl -O https://raw.githubusercontent.com/kallitests/qa-toolbox-precommit/main/.pre-commit-config.yaml
curl -O https://raw.githubusercontent.com/kallitests/qa-toolbox-precommit/main/pyproject.toml
curl -O https://raw.githubusercontent.com/kallitests/qa-toolbox-precommit/main/.gitlint
curl -O https://raw.githubusercontent.com/kallitests/qa-toolbox-precommit/main/Makefile

# 3. Create a virtual environment and install all tools
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install pre-commit pip-audit detect-secrets gitlint black ruff mypy bandit vulture pytest pytest-cov

# 4. Initialise the secrets baseline (scans existing SmokeSentinel files)
detect-secrets scan > .secrets.baseline

# 5. Activate the pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg

# 6. Run the full stack on all existing SmokeSentinel Python files
pre-commit run --all-files
```

### What happens on the first run

```
Trim Trailing Whitespace.................................................Passed
Fix End of Line..........................................................Passed
Mixed line endings.......................................................Passed
Check for added large files..............................................Passed
Check for merge conflicts................................................Passed
black....................................................................Failed  ← auto-fixed, re-add and commit
ruff.....................................................................Failed  ← unused imports auto-removed
mypy.....................................................................Failed  ← untyped functions flagged
vulture..................................................................Passed
detect-secrets...........................................................Passed
bandit...................................................................Warning ← subprocess shell=True flagged
pip-audit................................................................Passed
```

> `black` and `ruff` **auto-fix** their findings — just `git add .` and retry the commit.
> `mypy` and `bandit` require a manual fix in the source file.

### Example: fixing a mypy error in SmokeSentinel

```python
# Before — mypy error: Function is missing a return type annotation
def run_check(url, timeout):
    response = requests.get(url, timeout=timeout)
    return response.status_code == 200

# After — mypy passes
def run_check(url: str, timeout: int) -> bool:
    response = requests.get(url, timeout=timeout)
    return response.status_code == 200
```

### Example: a valid commit on SmokeSentinel after fixes

```bash
git add smoke_runner.py pyproject.toml .pre-commit-config.yaml .gitlint .secrets.baseline
git commit -m "feat(smoke): add type annotations and pre-commit stack"
```

```
black....................................................................Passed
ruff.....................................................................Passed
mypy.....................................................................Passed
vulture..................................................................Passed
detect-secrets...........................................................Passed
bandit...................................................................Passed
pip-audit................................................................Passed
gitlint..................................................................Passed
[main a3f19c2] feat(smoke): add type annotations and pre-commit stack
```

### Adjusting `pyproject.toml` for SmokeSentinel

Open `pyproject.toml` and update two lines to match the SmokeSentinel package structure:

```toml
[tool.ruff.lint.isort]
known-first-party = ["smoke_sentinel"]  # replace "qa_toolbox" with your actual package name

[tool.pytest.ini_options]
testpaths = ["tests"]                   # adjust if SmokeSentinel tests live in a different folder
```

---

## 📬 Connect

| | |
|---|---|
| 💼 LinkedIn | [khalid-hafidmedheb](https://www.linkedin.com/in/khalid-hafidmedheb-40451aa8) |
| 🐙 GitHub | [kallitests](https://github.com/kallitests) |
| 🌍 Location | Montgeron — Full Remote FR/EU |

---

> *"Quality is not an act, it is a habit — automated at every commit."*
> — Khalid HAFID-MEDHEB
