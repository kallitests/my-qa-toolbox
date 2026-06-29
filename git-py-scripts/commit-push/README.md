# git-commit-push-safe

> **A safety layer around `git add . → commit → push` — because raw Git has no guardrails.**

Every developer has done it: committed a `.env` file, pushed straight to `main` by accident, or written a commit message they regretted six months later. This script puts a structured, opinionated workflow in front of those three Git commands so that mistakes get caught *before* they reach the remote.

[![Status](https://img.shields.io/badge/status-stable-brightgreen?style=flat-square)](https://github.com/kallitests/git-commit-push-safe)
[![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![Git](https://img.shields.io/badge/Git-required-F05032?style=flat-square&logo=git)](https://git-scm.com)

---

## Why this script?

The plain one-liner `git add . && git commit -m "fix" && git push` has no safety net whatsoever. It will happily:

- Commit your `.env` file with real credentials to a public repo
- Push directly to `main` without a second thought
- Create an empty or meaningless commit that pollutes the log forever
- Fail with a cryptic SSH or permission error and leave you guessing why

`git-commit-push-safe` adds the checks a senior developer would mentally run through anyway — but makes them automatic, interactive, and impossible to skip by accident. You still confirm every action; the script just makes sure you have all the information you need before you do.

**The result:** the same three Git commands, with a structured pre-flight that takes ~10 seconds and has already caught real mistakes.

---

## What it checks

| Phase | What happens |
|---|---|
| **Pre-flight** | Verifies Git is installed, the directory is a repo, `origin` is configured, and the branch is not detached |
| **Branch safety** | Warns and asks for explicit confirmation before pushing to `main`, `master`, `production`, `prod`, or `release` |
| **File review** | Lists all modified, added, deleted, and untracked files with colour-coded status before anything is staged |
| **Empty commit guard** | Aborts cleanly if the working tree is clean — no pointless empty commits |
| **Merge conflict guard** | Detects unresolved conflicts (`UU`, `AA`…) and blocks the commit before Git markers end up in your history |
| **Secret detection** | Scans filenames against patterns for `.env`, `.pem`, `.key`, `secrets.*`, `credentials.*`, SSH private keys, and keystores — and flags them before they are staged |
| **Commit message validation** | Rejects empty or too-short messages; warns on generic ones (`fix`, `wip`, `update`, `misc`…) and suggests Conventional Commits format |
| **Full summary** | Shows exactly what will run — remote URL, branch, commit message, file list, and the three Git commands — before touching anything |
| **Final confirmation** | One explicit `y/N` prompt. No surprises. |
| **Push error diagnosis** | Identifies and explains: missing upstream branch, rejected push (remote ahead), auth denied, known-collaborator transient denial (auto-retried once), and network timeout |
| **Post-push report** | Prints the short commit hash and direct GitHub links to the commit and the branch |

---

## Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│                       git_commit_push.py                             │
│                                                                      │
│  ┌──────────────┐    ┌────────────────┐    ┌──────────────────────┐ │
│  │ Pre-flight   │───▶│ Modified files │───▶│  Secret file scan    │ │
│  │ checks       │    │ + conflict scan│    │  (.env, .pem, .key…) │ │
│  └──────────────┘    └────────────────┘    └──────────┬───────────┘ │
│                                                        │             │
│  ┌──────────────┐    ┌────────────────┐    ┌──────────▼───────────┐ │
│  │  Post-push   │◀───│  git push      │◀───│  Commit message      │ │
│  │  summary     │    │  + diagnosis   │    │  + final confirm     │ │
│  └──────────────┘    └────────────────┘    └──────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Requirements

| Tool | Notes |
|---|---|
| [Git](https://git-scm.com) | Must be installed and in `PATH` |
| Python 3.10+ | Standard library only — **zero external dependencies** |

---

## Usage

```bash
# From the repo root
python git_commit_push.py

# Target a different repo
python git_commit_push.py --path /path/to/your/repo
```

No config file, no environment variables, no flags to memorise. Just run it.

### Setting up the `gcp` alias

Instead of typing `python git_commit_push.py` every time, create a `gcp` alias that runs the script from anywhere.

**macOS / Linux (bash or zsh)**

```bash
# Add the alias to your shell config — adjust the path to match your actual location
echo 'alias gcp="python /path/to/git_commit_push.py"' >> ~/.bashrc   # bash
echo 'alias gcp="python /path/to/git_commit_push.py"' >> ~/.zshrc    # zsh

# Reload the config so the alias is available immediately
source ~/.bashrc   # or source ~/.zshrc
```

**Windows — Git Bash**

```bash
# Add the alias to your Git Bash profile
echo 'alias gcp="python /c/path/to/git_commit_push.py"' >> ~/.bashrc
source ~/.bashrc
```

**Windows — PowerShell**

```powershell
# Open your PowerShell profile (creates it if it doesn't exist)
notepad $PROFILE

# Add this line, then save and close
function gcp { python "C:\path\to\git_commit_push.py" @args }
```

Once set up, just run:

```bash
gcp
# or target a specific repo
gcp --path /path/to/your/repo
```

### Verifying the alias

```bash
# Check that the alias is defined and see what it points to
alias gcp          # bash / zsh / Git Bash

# In PowerShell
Get-Command gcp

# Do a dry run from any Git repo to confirm it works
cd /any/git/repo
gcp
```

---

## Example session

```
════════════════════════════════════════════════════════════
   GIT COMMIT & PUSH — Safe administration script
════════════════════════════════════════════════════════════
  Repository: /home/user/my-project

────────────────────────────────────────────────────────────
  Pre-flight checks
────────────────────────────────────────────────────────────
  ✔  Git detected: git version 2.43.0
  ✔  Valid Git repository: /home/user/my-project
  ✔  Remote 'origin': git@github.com:khafid1506/my-project.git
  ⚠  You are on the protected branch 'main'. Continue anyway? [y/N]: y

────────────────────────────────────────────────────────────
  Modified files
────────────────────────────────────────────────────────────
  3 file(s) detected:
    modified  tests/login.spec.ts
    added     pages/LoginPage.ts
    new       .env.local
  ⚠  Potentially sensitive files detected: .env.local
     Include these files anyway? [y/N]: n

────────────────────────────────────────────────────────────
  Commit message
────────────────────────────────────────────────────────────
  Commit message: feat: add Sauce Demo login page object

────────────────────────────────────────────────────────────
  Summary — what will be executed
────────────────────────────────────────────────────────────
  Remote : git@github.com:khafid1506/my-project.git
  Branch : main
  Commit : "feat: add Sauce Demo login page object"
  Files included (2): ...

  Everything looks good. Run add → commit → push? [Y/n]: Y

  ✔  All files have been staged.
  ✔  Commit created successfully.
  ✔  Push successful!

────────────────────────────────────────────────────────────
  Post-push summary
────────────────────────────────────────────────────────────
  ✔  Last pushed commit: a3f2c91
  ℹ  Branch: main
  ℹ  View commit : https://github.com/khafid1506/my-project/commit/a3f2c91
  ℹ  View branch : https://github.com/khafid1506/my-project/tree/main

  ✔  All done!
```

---

## Error handling

The script recognises and explains the most common push failures rather than dumping raw Git output:

```
# Branch not yet on remote
hint: set-upstream …
→ Script offers to run git push --set-upstream automatically

# Remote has commits you don't have locally
! [rejected] main -> main (non-fast-forward)
→ Script explains the situation and tells you to git pull first

# Auth denied for a known collaborator (transient)
ERROR: Permission to owner/repo.git denied to khafidmedheb.
→ Script detects the account is in ALLOWED_GITHUB_USERS, retries once automatically

# Network issue
fatal: Could not resolve host: github.com
→ Script tells you it's a connectivity problem, not a Git misconfiguration
```

---

## Notes

- `ALLOWED_GITHUB_USERS` is a set of GitHub usernames trusted as legitimate collaborators on this repo (`khafid1506` and `khafidmedheb` by default). Edit it to match your own team before using this on a different project.
- Persistent SSH (`ControlMaster`/`ControlPersist`) is **disabled by default** — it produced noisy warnings on Git Bash 