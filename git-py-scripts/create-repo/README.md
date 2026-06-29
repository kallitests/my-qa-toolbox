# 🚀 create-github-repo

> **Push a local folder to a brand-new GitHub repository in one command.**
> Pre-flight checks, repo creation via `gh`, auto-invited collaborator, commit & push with smart retry on permission errors.

[![Status](https://img.shields.io/badge/status-stable-brightgreen?style=flat-square)](https://github.com/kallitests/create-github-repo)
[![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![Git](https://img.shields.io/badge/Git-required-F05032?style=flat-square&logo=git)](https://git-scm.com)
[![GitHub CLI](https://img.shields.io/badge/GitHub_CLI-gh-181717?style=flat-square&logo=github)](https://cli.github.com)

---

## 🗺️ Table of Contents

- [Why this script?](#-why-this-script)
- [What it does](#%EF%B8%8F-what-it-does)
- [Workflow](#-workflow)
- [Requirements](#-requirements)
- [Usage](#-usage)
- [CLI options](#-cli-options)
- [Built-in safety defaults](#-built-in-safety-defaults)
- [Notes](#-notes)
- [Roadmap](#-roadmap)
- [Author](#-author)

---

## 💡 Why this script?

Pushing a new local project to GitHub usually means several manual, error-prone steps:

> *Create the repo on github.com → copy the remote URL → `git init` → `git remote add` → `git add` → `git commit` → `git push` → remember to add your collaborator before they push and get denied.*

One step forgotten — usually the collaborator one — and the first teammate push fails with a cryptic `Permission ... denied` error.

**`create-github-repo` automates this entire flow in a single command — collaborator access included.**

```
Local folder ──▶ Pre-flight checks ──▶ Repo created (gh) ──▶ Collaborator invited ──▶ Commit & push
```

---

## ⚙️ What It Does

| Step | Description |
|------|-------------|
| 🔍 **Pre-flight checks** | Verifies `git`/`gh` are installed, `gh` is authenticated, the repo name is valid, no remote name collision |
| 📂 **File discovery** | Lists every file/folder in the current directory, minus safe defaults (`.git`, `venv`, `__pycache__`, `.env`…) |
| 🆕 **Repo creation** | Creates the GitHub repository via `gh repo create` (public or private) |
| 🤝 **Auto-invite collaborator** | Invites a second known account right after creation — no more surprise "permission denied" on a teammate's first push |
| 📦 **Commit & push** | Initializes git in place, stages the discovered files, commits, and pushes with `-u` |
| 🔁 **Smart retry** | If the push is denied for a known collaborator, retries the invite once before failing |

---

## 🏗️ Workflow

```
┌────────────────────────────────────────────────────────────────────┐
│                      create_github_repo.py                          │
│                                                                      │
│  ┌──────────────┐    ┌────────────────┐    ┌─────────────────────┐ │
│  │ Pre-flight   │───▶│ Discover files │───▶│  gh repo create     │ │
│  │ checks       │    │ (current dir)  │    │  (public/private)   │ │
│  └──────────────┘    └────────────────┘    └──────────┬──────────┘ │
│                                                         │            │
│  ┌──────────────┐    ┌────────────────┐    ┌──────────▼──────────┐ │
│  │  Push retry  │◀───│  git push -u   │◀───│ Invite collaborator │ │
│  │  on "denied" │    │  origin main   │    │ (gh api, push perm) │ │
│  └──────────────┘    └────────────────┘    └──────────────────────┘│
└────────────────────────────────────────────────────────────────────┘
```

---

## 🧰 Requirements

| Tool | Notes |
|---|---|
| [Git](https://git-scm.com) | Required, must be in `PATH` |
| [GitHub CLI (`gh`)](https://cli.github.com) | Required, authenticated via `gh auth login` |
| Python | 3.10+ |

---

## 🚀 Usage

Run it **from the folder you want to push** — everything in that folder gets pushed, minus the exclusions.

### Basic — public repo from the current folder

```bash
python create_github_repo.py optimus-prompt
```

### Custom description + private repo

```bash
python create_github_repo.py my-project --description "My cool project" --private
```

### Exclude extra files/folders + custom commit message

```bash
python create_github_repo.py my-project --exclude notes.txt drafts --message "chore: initial commit"
```

### Full example

```bash
cd ~/projects/playwright-pr-smoke-gate
python create_github_repo.py playwright-pr-smoke-gate \
  --description "Playwright TypeScript smoke suite running under 5 minutes on every PR" \
  --exclude .vscode draft-notes.md
```

### Example session

```
══════════════════════════════════════════════════════════
  🚀  create_github_repo.py
  Repo  : playwright-pr-smoke-gate
  Desc  : Playwright TypeScript smoke suite running under 5 min
  Vis.  : public
  Dir   : /home/user/projects/playwright-pr-smoke-gate
══════════════════════════════════════════════════════════

[INFO]  Step 1/6 — Running pre-flight checks...
[OK]    git found at /usr/bin/git
[OK]    gh found at /usr/bin/gh
[OK]    GitHub CLI is authenticated.
[OK]    Repo name 'playwright-pr-smoke-gate' is valid.
[OK]    No existing remote repo named 'playwright-pr-smoke-gate' found. Safe to create.

[INFO]  Step 2/6 — Discovering files in the current folder...
[OK]    Will push: tests
[OK]    Will push: README.md
[OK]    Will push: playwright.config.ts

[INFO]  Step 3/6 — Creating remote GitHub repository...
[OK]    Remote repo 'playwright-pr-smoke-gate' created as public on GitHub.
[INFO]  Inviting 'khafidmedheb' as a collaborator on kallitests/playwright-pr-smoke-gate...
[OK]    'khafidmedheb' added/confirmed as a collaborator (push).

[INFO]  Step 5/6 — Setting remote and pushing...
[OK]    Remote 'origin' set to https://github.com/kallitests/playwright-pr-smoke-gate.git
[OK]    Initial commit pushed to GitHub successfully.

[INFO]  Step 6/6 — Done.

──────────────────────────────────────────────────────────
  ✅  Repository 'playwright-pr-smoke-gate' is live!
  🔗  https://github.com/kallitests/playwright-pr-smoke-gate
──────────────────────────────────────────────────────────
```

---

## 🛠️ CLI Options

| Flag | Description | Default |
|---|---|---|
| `repo_name` | Name of the GitHub repository (positional, required) | — |
| `--description` | Short description shown on the GitHub repo page | empty |
| `--private` | Create a private repo instead of public | public |
| `--exclude` | Extra files/folders to skip, on top of the built-in defaults | none |
| `--message` | Initial commit message | `feat: initial commit` |

---

## 🛡️ Built-in Safety Defaults

Always excluded, even without `--exclude`:

`.git` · `.gitignore` · `__pycache__` · `.venv` · `venv` · `env` · `node_modules` · `.env` · `.env.local` · the script itself

If the current folder is already a git repo **with an `origin` remote**, the script refuses to run — avoids pushing to the wrong place. A `.git` folder with no remote yet is safely reused.

---

## 📝 Notes

- Collaborator auto-invite assumes the `gh`-authenticated account has admin rights on the new repo (true by default — the creator is always admin).
- A freshly invited account still needs to **accept the invitation** once before its first push goes through (`https://github.com/<owner>/<repo>/invitations`).
- The smart retry handles the case where the invite hasn't propagated yet at push time — it re-sends the invite and retries the push once before failing with a clear diagnostic.

---

## 📌 Roadmap

- [x] Pre-flight checks (git/gh installed, authenticated, valid name)
- [x] File discovery with safe default exclusions
- [x] Repo creation via `gh repo create`
- [x] Auto-invite known collaborator at creation time
- [x] Push retry with re-invite on "permission denied"
- [ ] `--org` flag to create under a GitHub organization
- [ ] `.gitignore` template selection (Python, Node, etc.)
- [ ] Dry-run mode (`--dry-run`) to preview actions without executing them

---

## 👤 Author

**Khalid Hafid-Medheb**
Senior SDET & AI Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-khalid--hafid--medheb-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/khalid-hafid-medheb-40451aa8/)
[![GitHub](https://img.shields.io/badge/GitHub-kallitests-181717?style=flat-square&logo=github)](https://github.com/kallitests)

---

*Built with 🐍 Python · 🐙 GitHub CLI*
