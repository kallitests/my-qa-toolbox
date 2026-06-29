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

`git-commit-push-safe` adds the checks a senior developer would mentally run through anyway — but makes them automatic, interactive, and impossible to skip by accident.

**The result:** the same three Git commands, wrapped in a ~10-second structured pre-flight that has already caught real mistakes in production workflows.

### Key value-add at a glance

| Without the script | With `git-commit-push-safe` |
|---|---|
| `.env` silently committed | Secret file scanner blocks it and asks for confirmation |
| Direct push to `main` with no warning | Explicit confirmation required for protected branches |
| Empty or `"fix"` commit messages | Minimum-length validation + Conventional Commits guidance |
| Cryptic SSH / permission errors | Named error patterns with plain-English diagnosis and auto-retry |
| No idea what just got staged | Full colour-coded file list shown before anything is staged |
| No confirmation before push | One final `[Y/n]` prompt showing the exact commands that will run |

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

---

## Setting up the `gcp` alias

Instead of typing `python /full/path/to/git_commit_push.py` every time, create a short `gcp` alias that launches the script from any directory.

### macOS / Linux — bash

```bash
# Append the alias to your bash config (replace the path with your actual location)
echo 'alias gcp="python /path/to/git_commit_push.py"' >> ~/.bashrc

# Reload the config so the alias is immediately available in the current shell
source ~/.bashrc
```

### macOS / Linux — zsh

```bash
echo 'alias gcp="python /path/to/git_commit_push.py"' >> ~/.zshrc
source ~/.zshrc
```

### Windows — Git Bash

```bash
# Git Bash uses Unix-style paths; /c/ maps to C:\
echo 'alias gcp="python /c/path/to/git_commit_push.py"' >> ~/.bashrc
source ~/.bashrc
```

### Windows — PowerShell

```powershell
# Open (or create) your PowerShell profile file
notepad $PROFILE

# Add this function, then save and close
function gcp { python "C:\path\to\git_commit_push.py" @args }

# Reload the profile in the current session
. $PROFILE
```

Once set up, use the alias from any directory:

```bash
# Run in the current Git repo
gcp

# Or target a specific repo
gcp --path /path/to/your/repo
```

---

## Verifying the alias

After setup, confirm the alias is correctly wired before relying on it.

```bash
# bash / zsh / Git Bash — print the alias definition
alias gcp
# Expected output: alias gcp='python /path/to/git_commit_push.py'

# bash / zsh — check which file declared it (useful for debugging)
type gcp

# PowerShell — inspect the command definition
Get-Command gcp
Get-Command gcp | Select-Object -ExpandProperty Definition
```

To do a live end-to-end check, navigate to any Git repository and run `gcp`. The script's pre-flight banner should appear immediately. If it does not:

- **"command not found"** → the alias was not written to the right config file, or the file was not sourced.
- **"python: can't open file"** → the path inside the alias is wrong; verify with `ls /path/to/git_commit_push.py`.
- **"python: command not found"** → try `python3` instead of `python` in the alias.

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

## Linting

The project uses [flake8](https://flake8.pycqa.org/) with a line-length limit of 100 characters, configured in `.flake8`.

```bash
pip install flake8
flake8 git_commit_push.py
# No output = clean
```

---

## Notes

- `ALLOWED_GITHUB_USERS` is a set of GitHub usernames trusted as legitimate collaborators on this repo (`khafid1506` and `khafidmedheb` by default). Edit it to match your own team before using this on a different project.
- Persistent SSH (`ControlMaster`/`ControlPersist`) is **disabled by default** — it produced noisy warnings on Git Bash / Windows with no real benefit in practice. The underlying functions (`ensure_persistent_ssh_config`, `check_github_ssh_identity`) are kept in the source, commented out. Re-enable them if you need shared SSH sessions on macOS/Linux.
- Zero external dependencies: the script uses only Python's standard library (`os`, `re`, `sys`, `argparse`, `subprocess`, `pathlib`).
