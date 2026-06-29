# 🤖 git-commit-push-ai

> **A safety-checked `git add → commit → push` workflow that writes its own commit message.**
> A local LLM (Ollama, free, zero tokens) reads your staged diff and proposes a Conventional Commits message — accept it, edit it, or regenerate. Claude/Anthropic is wired in as a drop-in upgrade for production.

[![Status](https://img.shields.io/badge/status-stable-brightgreen?style=flat-square)](https://github.com/kallitests/git-commit-push-ai)
[![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-agent-blueviolet?style=flat-square)](https://langchain.com)
[![Ollama](https://img.shields.io/badge/Ollama-local%20%26%20free-1A1A1A?style=flat-square&logo=ollama)](https://ollama.com)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-black?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](#-license)

---

## 🗺️ Table of Contents

- [Why this script?](#-why-this-script)
- [What it does](#%EF%B8%8F-what-it-does)
- [Pipeline](#-pipeline)
- [LLM providers](#-llm-providers)
- [Safety checks](#-safety-checks)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [gcp alias — run it from anywhere](#-gcp-alias--run-it-from-anywhere)
- [Example session](#-example-session)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)
- [Author](#-author)

---

## 💡 Why This Script?

Careless commits are a permanent problem. `fix`, `wip`, and `update stuff` clog Git history because writing a proper message takes a small extra effort that developers skip under pressure.

**This script removes the excuse by automating the two hardest parts of a good commit workflow:**

1. **Commit message quality** — the LLM reads your actual staged diff and proposes a properly formatted [Conventional Commits](https://www.conventionalcommits.org/) message in one shot. You accept it in one keystroke, edit it inline, or ask for a fresh one.

2. **Push safety** — every run enforces a full checklist before anything is executed: protected branch warning, secret-file detection, merge-conflict guard, and a complete recap (remote, branch, files, message) with explicit confirmation before the push fires.

```
git add . ──▶ staged diff ──▶ local LLM ──▶ Conventional Commit message ──▶ commit ──▶ push
```

The default provider is **Ollama — 100% local, zero API cost, zero cloud calls.** The diff never leaves your machine unless you explicitly switch to the Anthropic provider. Claude/Anthropic is available as a one-flag upgrade when message quality matters more than cost.

The script is also resilient: if the LLM is unreachable or not installed, it falls back to manual input without blocking the workflow. No setup is strictly required to use it.

---

## ⚙️ What It Does

| Step | Description |
|------|-------------|
| 🔍 **Pre-flight checks** | Git installed · valid repo · `origin` configured · branch not detached |
| ⚠️ **Branch safety** | Warns and asks for confirmation on `main`, `master`, `production`, `release` |
| 📋 **Change detection** | Lists every modified/added/deleted/untracked file before staging |
| 🚫 **Conflict guard** | Hard-blocks if unresolved merge conflicts are detected |
| 🔐 **Secret detection** | Flags `.env`, `.pem`, `.key`, `secrets.*`, SSH private keys before they get committed |
| 🧠 **AI commit message** | Reads the staged diff, proposes a Conventional Commits message via Ollama (or Claude) |
| ✏️ **Accept / edit / regenerate** | `[Enter]` accepts · `r` regenerates · anything else is used as a custom message |
| 📝 **Full recap** | Shows remote, branch, commit message, and file list before touching anything |
| 🔌 **SSH resilience** | Persistent SSH connection (ControlPersist) + stale-socket cleanup + multi-collaborator awareness |
| 🩺 **Push error diagnosis** | Handles: no upstream branch · rejected push · auth denied · network timeout |
| 🔗 **Post-push summary** | Commit hash + direct GitHub links to the commit and branch |

---

## 🔄 Pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│                      git-commit-push-ai                              │
│                                                                      │
│   ┌──────────────┐     ┌────────────────┐     ┌──────────────────┐  │
│   │  git status  │────▶│  Safety checks  │────▶│   git add .      │  │
│   │  (changes)   │     │  (conflicts,    │     │   (staged diff)  │  │
│   │              │     │   secrets, etc) │     │                  │  │
│   └──────────────┘     └────────────────┘     └────────┬─────────┘  │
│                                                         │            │
│   ┌──────────────┐     ┌────────────────┐     ┌────────▼─────────┐  │
│   │ git push     │◀────│ git commit -m   │◀────│  LLM commit msg  │  │
│   │ (origin/...) │     │ (after recap +  │     │  (Ollama/Claude) │  │
│   │              │     │  confirmation)  │     │                  │  │
│   └──────────────┘     └────────────────┘     └──────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 LLM Providers

| Provider | Cost | Where it runs | When to use |
|----------|------|----------------|-------------|
| 🟢 **Ollama** *(default)* | Free, 0 tokens | 100% local | Testing, dev machines, no API key needed |
| 🔵 **Anthropic (Claude)** | Paid, per token | Cloud API | Production, when message quality matters more than cost |

The system prompt is intentionally minimal — one instruction per line, no filler — to keep every call short and cheap regardless of provider:

```
You write Git commit messages in Conventional Commits format.
One line only. Maximum 72 characters. In English.
Format: <type>(<scope>): <description in present tense>
Valid types: feat, fix, docs, refactor, chore, test, style, perf.
No trailing period. No em dash. No quotes.
Reply with the message only, nothing else.
```

The staged diff sent to the model is capped (`AI_MAX_DIFF_CHARS`, default 6 000 chars) and paired with a `git diff --stat` summary, so large refactors don't blow up the prompt — the message stays editable by hand regardless.

Switching provider is a single flag or env var:

```bash
python git_commit_push_ai.py                           # Ollama (default)
python git_commit_push_ai.py --llm-provider anthropic  # Claude
LLM_PROVIDER=anthropic python git_commit_push_ai.py    # same, via env var
python git_commit_push_ai.py --no-ai                   # manual input, no LLM at all
```

> Other free/local options work the same way and could be wired in later — they all expose an OpenAI-compatible API, same plumbing as Ollama: **LM Studio**, **llama.cpp server**, **GPT4All**, **Jan**, **text-generation-webui**.

---

## 🛡️ Safety Checks

Nothing executes silently. Every run shows the exact files, branch, remote, and commit message **before** asking for final confirmation — and the script never commits an empty diff or pushes with unresolved conflicts.

| Check | Behavior |
|-------|----------|
| Protected branch (`main`, `master`, `production`, `release`) | Requires explicit `y/n` confirmation |
| Sensitive files (`.env`, `.pem`, `.key`, `secrets.*`, SSH keys…) | Warns and asks before including them |
| Merge conflicts | Hard block — no commit until resolved |
| Empty diff | Hard block — nothing to commit |
| Push rejected (remote ahead) | Diagnosis + `git pull` instructions |
| No upstream branch | Offers to run `--set-upstream` automatically |
| Auth/permission denied | Diagnoses SSH identity, retries once via persistent connection if the denied account is a known collaborator |

---

## 🚀 Getting Started

### Option A — Ollama (free, local, default)

```bash
# 1. Install Ollama
# https://ollama.com

# 2. Pull a small model
ollama pull llama3.2

# 3. Start the Ollama server (separate terminal)
ollama serve

# 4. Install Python dependencies
pip install langchain-ollama langchain-core
```

### Option B — Claude / Anthropic (production)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pip install langchain-anthropic langchain-core
```

Both providers are optional — the script **never blocks** if the chosen one is unavailable and falls back to manual commit message input automatically.

---

## 📖 Usage

```bash
# From inside your repo, with Ollama running
python git_commit_push_ai.py

# Force the Claude/Anthropic provider
python git_commit_push_ai.py --llm-provider anthropic

# Skip AI entirely, type the message yourself
python git_commit_push_ai.py --no-ai

# Target a different repo
python git_commit_push_ai.py --path /path/to/your/repo
```

---

## ⚡ gcp alias — run it from anywhere

Instead of typing `python /full/path/to/git_commit_push_ai.py` every time, create a `gcp` shell alias that launches the script from any directory.

### Create the alias

**bash / zsh — temporary (current session only):**
```bash
alias gcp='python /full/path/to/git_commit_push_ai.py'
```

**bash — permanent (add to `~/.bashrc`):**
```bash
echo "alias gcp='python /full/path/to/git_commit_push_ai.py'" >> ~/.bashrc
source ~/.bashrc
```

**zsh — permanent (add to `~/.zshrc`):**
```bash
echo "alias gcp='python /full/path/to/git_commit_push_ai.py'" >> ~/.zshrc
source ~/.zshrc
```

> Replace `/full/path/to/git_commit_push_ai.py` with the actual absolute path to the script, e.g. `~/projects/my-qa-toolbox/git-py-scripts/commit-push-ai/git_commit_push_ai.py`

### Verify the alias was created

```bash
# Check the alias is defined
alias gcp

# Expected output:
# alias gcp='python /full/path/to/git_commit_push_ai.py'

# Make sure it resolves (type is more thorough than alias on some shells)
type gcp

# Run it from any git repo
cd /path/to/any/repo
gcp
```

### Use it with flags

```bash
gcp                            # Ollama (default)
gcp --llm-provider anthropic   # Claude
gcp --no-ai                    # manual message
gcp --path /other/repo         # different repo
```

---

## 🖥️ Example Session

```
════════════════════════════════════════════════════
   GIT COMMIT & PUSH — AI-assisted
════════════════════════════════════════════════════
  Repo : /home/user/my-project
  AI   : Ollama (local, free)

── Pre-flight checks ───────────────────────────────
  ✔  Git detected: git version 2.43.0
  ✔  Valid Git repository
  ✔  Remote 'origin': git@github.com:user/my-project.git
  ✔  Current branch: feature/auth-retry

── Modified files ───────────────────────────────────
  3 file(s) detected:
    modified   auth/session.py
    modified   auth/retry.py
    added      tests/test_retry.py

── git add . ────────────────────────────────────────
  ✔  All files staged.

── Commit message ───────────────────────────────────
  ℹ  Generating commit message via AI (provider: ollama)…

  Suggested message: feat(auth): add retry logic for expired session tokens

  [Enter] accept · 'r' regenerate · or type your own message
  >

  ✔  Message accepted: "feat(auth): add retry logic for expired session tokens"

── Summary ─────────────────────────────────────────
  Remote  : git@github.com:user/my-project.git
  Branch  : feature/auth-retry
  Commit  : "feat(auth): add retry logic for expired session tokens"

  Everything looks good. Run commit → push? [Y/n] :

── git push ─────────────────────────────────────────
  ✔  Push succeeded!
  ✔  Last commit pushed: a3f2c91
```

---

## ⚙️ Configuration

| Variable / Flag | Default | Purpose |
|------------------|---------|---------|
| `--llm-provider` | `ollama` | `ollama` or `anthropic` |
| `LLM_PROVIDER` (env) | `ollama` | Same as above, set globally |
| `OLLAMA_MODEL` (env) | `llama3.2` | Any model you've `ollama pull`-ed |
| `OLLAMA_BASE_URL` (env) | `http://localhost:11434` | Point at a remote Ollama instance if needed |
| `ANTHROPIC_API_KEY` (env) | — | Required only when `--llm-provider anthropic` |
| `--no-ai` | off | Skip the LLM entirely, type the message by hand |
| `--path` | current directory | Target a repo other than the one you're standing in |

---

## 📌 Roadmap

- [x] Core safety-checked commit & push workflow
- [x] AI commit message generation (Ollama, local & free)
- [x] Claude/Anthropic provider for production use
- [x] Persistent SSH connection + stale-socket cleanup
- [x] Multi-collaborator account awareness (`denied to X` handling)
- [ ] OpenAI-compatible provider (LM Studio / llama.cpp server / GPT4All)
- [ ] Commit message history / learning from past commits in the repo
- [ ] Pre-commit hook mode (auto-run on `git commit`)

---

## 👤 Author

**Khalid Hafid-Medheb**
QA Automation Engineer | SDET — Playwright · Cypress · CI/CD

[![LinkedIn](https://img.shields.io/badge/LinkedIn-khalid--hafid--medheb-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/khalid-hafid-medheb-40451aa8/)
[![GitHub](https://img.shields.io/badge/GitHub-kallitests-181717?style=flat-square&logo=github)](https://github.com/kallitests)

---

## 📄 License

MIT — use it, fork it, plug in whatever LLM provider you want.

---

*Built with 🧠 Claude (Anthropic) · 🦙 Ollama · 🦜 LangChain*
