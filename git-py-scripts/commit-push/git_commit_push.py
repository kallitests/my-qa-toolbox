#!/usr/bin/env python3
"""
git_commit_push.py

GIT ADMINISTRATION SCRIPT — SAFE COMMIT & PUSH
===============================================

Automates the full cycle:
    git add .  →  git commit -m "<message>"  →  git push

Checks included (in execution order):
    ✔ Verifies that git is installed
    ✔ Verifies the current directory is a Git repository
    ✔ Verifies the 'origin' remote is configured
    ✔ Verifies the current branch is known (detached HEAD protection)
    ✔ Warns if the branch is 'main' or 'master' (requires confirmation)
    ✔ Displays modified / untracked files before staging
    ✔ Warns if no changes are detected (nothing to commit)
    ✔ Warns if sensitive files (.env, secrets, keys) are about to be committed
    ✔ Validates that the commit message is not empty and meets a minimum length
    ✔ Displays a full summary before executing anything
    ✔ Asks for final confirmation before pushing
    ✔ Handles SSH / token / network errors and displays a clear diagnosis

NOTE: The persistent SSH connection (ControlMaster/ControlPersist) is
DISABLED by default — it was generating noisy warnings on
Git Bash / Windows ("mux_client_request_session... Connection reset by
peer") with no real benefit. The code is kept (commented out) in
ensure_persistent_ssh_config() / check_github_ssh_identity() and in
main() if you need to re-enable it on a different environment.

Usage:
    python git_commit_push.py
    python git_commit_push.py --path /path/to/your/repo
"""

import os
import re
import sys
import argparse
import subprocess
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Configuration constants
# ─────────────────────────────────────────────────────────────────────────────

# Branches that require explicit confirmation before any push
PROTECTED_BRANCHES = {"main", "master", "production", "prod", "release"}

# File patterns considered sensitive
SENSITIVE_PATTERNS = [
    r"\.env(\..+)?$",                   # .env, .env.local, .env.production …
    r"\.pem$",                           # private certificates
    r"\.key$",                           # private keys
    r"secrets?\.(json|ya?ml|toml)$",
    r"credentials?\.(json|ya?ml)$",
    r"id_rsa",                           # SSH private keys
    r"id_ed25519$",
    r"\.p12$",                           # keystores
    r"\.pfx$",
    r"config\.ya?ml$",                   # potentially sensitive config files
    r"database\.ya?ml$",
]

# Minimum acceptable length for a commit message
MIN_COMMIT_MSG_LENGTH = 10

# Legitimate GitHub accounts for this repository: khafidmedheb is a collaborator
# on the project hosted under khafid1506. If the push fails but the authenticated
# SSH identity is one of these two accounts, it is not a real access error —
# the script should not abort for that reason.
ALLOWED_GITHUB_USERS = {"khafid1506", "khafidmedheb"}

# SSH target host for the persistent connection (avoids re-authenticating
# on every git command in the script)
SSH_PERSISTENT_HOST = "github.com"


# ANSI colors for terminal output
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    DIM = "\033[2m"


# ─────────────────────────────────────────────────────────────────────────────
# Display utilities
# ─────────────────────────────────────────────────────────────────────────────

def header(title: str) -> None:
    """Print a readable section separator."""
    bar = "─" * 60
    print(f"\n{C.CYAN}{bar}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}  {title}{C.RESET}")
    print(f"{C.CYAN}{bar}{C.RESET}")


def ok(msg: str) -> None:
    print(f"{C.GREEN}  ✔  {msg}{C.RESET}")


def warn(msg: str) -> None:
    print(f"{C.YELLOW}  ⚠  {msg}{C.RESET}")


def error(msg: str) -> None:
    print(f"{C.RED}  ✖  {msg}{C.RESET}")


def info(msg: str) -> None:
    print(f"{C.CYAN}  ℹ  {msg}{C.RESET}")


def abort(msg: str) -> None:
    """Print a fatal error message and exit the script."""
    error(msg)
    print(f"\n{C.RED}{C.BOLD}  Aborting.{C.RESET}\n")
    sys.exit(1)


def confirm(prompt: str, default_yes: bool = False) -> bool:
    """
    Ask the user for a y/n confirmation.
    default_yes=True → pressing Enter alone counts as 'yes'.
    """
    hint = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"\n{C.BOLD}  {prompt} {hint}: {C.RESET}").strip().lower()
    if answer == "":
        return default_yes
    return answer in ("y", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# Shell command execution
# ─────────────────────────────────────────────────────────────────────────────

def run(cmd: list[str], cwd: str = None, capture: bool = True,
        check: bool = False) -> subprocess.CompletedProcess:
    """
    Execute a shell command.

    Parameters:
        cmd     -> list of arguments, e.g. ["git", "status", "--short"]
        cwd     -> working directory (None = current directory)
        capture -> if True, captures stdout/stderr instead of printing them
        check   -> if True, raises an exception if return code != 0

    Returns:
        The CompletedProcess object with .returncode, .stdout, .stderr
    """
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        check=check,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pre-flight checks
# ─────────────────────────────────────────────────────────────────────────────

def check_git_installed() -> None:
    """Verify that the 'git' command is available on the system."""
    result = run(["git", "--version"])
    if result.returncode != 0:
        abort("Git is not installed or is not in PATH.")
    ok(f"Git detected: {result.stdout.strip()}")


def check_is_git_repo(repo_path: str) -> None:
    """
    Verify that repo_path (or the current directory) is inside a Git repository.
    'git rev-parse --git-dir' fails if it is not.
    """
    result = run(["git", "rev-parse", "--git-dir"], cwd=repo_path)
    if result.returncode != 0:
        abort(
            f"'{repo_path}' is not a Git repository.\n"
            "  Run first: git init"
        )
    ok(f"Valid Git repository: {repo_path}")


def check_remote(repo_path: str) -> str:
    """
    Verify that an 'origin' remote is configured and return its URL.
    Without a remote, git push has nowhere to send the commits.
    """
    result = run(["git", "remote", "get-url", "origin"], cwd=repo_path)
    if result.returncode != 0:
        abort(
            "No 'origin' remote configured.\n"
            "  Example: git remote add origin git@github.com:user/repo.git"
        )
    url = result.stdout.strip()
    ok(f"Remote 'origin': {url}")
    return url


def check_branch(repo_path: str) -> str:
    """
    Retrieve the current branch name.
    Warns if in detached HEAD mode (dangerous for pushes).
    """
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if result.returncode != 0:
        abort("Unable to determine the current branch.")

    branch = result.stdout.strip()

    if branch == "HEAD":
        # Detached HEAD mode: commits are not attached to any branch.
        # Pushing in this state is almost always a mistake.
        abort(
            "You are in detached HEAD mode.\n"
            "  Create or switch to a branch before committing:\n"
            "  git checkout -b my-branch"
        )

    ok(f"Current branch: {C.BOLD}{branch}{C.RESET}")
    return branch


def check_protected_branch(branch: str) -> None:
    """
    Display an explicit warning if the branch is protected
    (main, master, production…) and ask for confirmation.
    Pushing directly to main is generally bad practice in a team setting.
    """
    if branch in PROTECTED_BRANCHES:
        warn(
            f"You are on the protected branch '{C.BOLD}{branch}{C.RESET}{C.YELLOW}'.\n"
            f"  Pushing directly to '{branch}' is risky in a team context.\n"
            "  Prefer a feature branch + Pull Request."
        )
        if not confirm(f"Continue anyway on '{branch}'?", default_yes=False):
            abort("Push cancelled by user.")


# ─────────────────────────────────────────────────────────────────────────────
# Persistent SSH connection + GitHub identity
# ─────────────────────────────────────────────────────────────────────────────

def ensure_persistent_ssh_config() -> None:
    """
    Ensure a 'ControlMaster/ControlPersist' entry exists in ~/.ssh/config
    for github.com.

    Without this, each git command (fetch/push/ssh -T) opens a NEW SSH
    session and may re-prompt for authentication or fall back to a different
    key. With ControlPersist, the first connection stays open and all
    subsequent commands reuse it — providing a "connected once" experience
    for the duration of the script (and 10 minutes after, enough to chain
    several operations).

    Idempotent: only adds the block if it is absent.
    """
    ssh_dir = Path.home() / ".ssh"
    config_path = ssh_dir / "config"
    sockets_dir = ssh_dir / "sockets"

    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    sockets_dir.mkdir(mode=0o700, exist_ok=True)

    existing = config_path.read_text() if config_path.exists() else ""

    if f"Host {SSH_PERSISTENT_HOST}" in existing and "ControlPersist" in existing:
        ok("Persistent SSH connection already configured for github.com.")
        return

    block = (
        f"\n# --- Added automatically by git_commit_push.py ---\n"
        f"Host {SSH_PERSISTENT_HOST}\n"
        f"    HostName {SSH_PERSISTENT_HOST}\n"
        f"    User git\n"
        f"    ControlMaster auto\n"
        f"    ControlPath ~/.ssh/sockets/%r@%h-%p\n"
        f"    ControlPersist 600\n"
        f"    IdentitiesOnly no\n"
        f"# --- End of automatically added block ---\n"
    )

    with open(config_path, "a") as f:
        f.write(block)
    config_path.chmod(0o600)

    ok("Persistent SSH connection configured in ~/.ssh/config (ControlPersist 600s).")
    info("Subsequent pushes will reuse the same SSH session for 10 minutes.")


def check_github_ssh_identity() -> str | None:
    """
    Run 'ssh -T git@github.com' to find out WHICH GitHub account is actually
    responding to the active SSH authentication.

    GitHub always returns exit code 1 on this test (that is normal, not an
    error), with a message like:
        "Hi khafidmedheb! You've successfully authenticated, but GitHub
         does not provide shell access."

    Returns the detected username, or None if it cannot be determined.
    """
    result = run(["ssh", "-T", "-o", "BatchMode=yes", f"git@{SSH_PERSISTENT_HOST}"])
    combined = f"{result.stdout}\n{result.stderr}"

    match = re.search(r"Hi (\S+?)!", combined)
    if not match:
        warn("Unable to determine the active SSH identity (ssh -T returned no usable response).")
        return None

    username = match.group(1)

    if username in ALLOWED_GITHUB_USERS:
        ok(f"Active SSH identity: {C.BOLD}{username}{C.RESET} (account authorised on this repo).")
    else:
        warn(
            f"Active SSH identity: {username} — this account is NOT in the\n"
            f"  list of authorised accounts ({', '.join(ALLOWED_GITHUB_USERS)}).\n"
            "  The push may be rejected if this account is not a collaborator."
        )

    return username


# ─────────────────────────────────────────────────────────────────────────────
# Modified file analysis
# ─────────────────────────────────────────────────────────────────────────────

def get_status(repo_path: str) -> list[tuple[str, str]]:
    """
    Return the list of modified files as (status_code, path) tuples.
    'git status --porcelain' produces stable, script-friendly output:
       M  file.py    -> modified
       ??  new.txt   -> untracked
       D  deleted.go -> deleted
       etc.
    """
    result = run(["git", "status", "--porcelain"], cwd=repo_path)
    raw_lines = [line for line in result.stdout.splitlines() if line.strip()]
    parsed = []
    for line in raw_lines:
        # First two characters = status code, the rest = path
        code = line[:2].strip()
        path = line[3:].strip()
        parsed.append((code, path))
    return parsed


def display_status(files: list[tuple[str, str]]) -> None:
    """Display the file list with a colour based on their status."""
    code_labels = {
        "M": (C.YELLOW, "modified"),
        "MM": (C.YELLOW, "modified"),
        "A": (C.GREEN, "added   "),
        "D": (C.RED, "deleted "),
        "R": (C.CYAN, "renamed "),
        "C": (C.CYAN, "copied  "),
        "??": (C.DIM, "new     "),
        "UU": (C.RED, "conflict"),
    }
    for code, path in files:
        color, label = code_labels.get(code, (C.WHITE, code.ljust(8)))
        print(f"    {color}{label}{C.RESET}  {path}")


def check_no_changes(files: list[tuple[str, str]]) -> None:
    """
    Stop the script if no changes are detected.
    Avoids creating an empty commit, which would pollute the history.
    """
    if not files:
        abort(
            "No changes detected.\n"
            "  The working tree is clean — nothing to commit."
        )


def check_merge_conflicts(files: list[tuple[str, str]]) -> None:
    """
    Detect unresolved merge conflict files (codes 'UU', 'AA'…).
    Committing with conflict markers (<<<<<<<) in the code is always a mistake.
    """
    conflict_codes = {"UU", "AA", "DD", "AU", "UA", "DU", "UD"}
    conflicts = [(c, p) for c, p in files if c in conflict_codes]
    if conflicts:
        error("Unresolved merge conflicts:")
        for code, path in conflicts:
            print(f"    {C.RED}{code}  {path}{C.RESET}")
        abort(
            "Resolve conflicts before committing.\n"
            "  Use: git mergetool  or edit the files manually,\n"
            "  then: git add <file>"
        )


def check_sensitive_files(files: list[tuple[str, str]]) -> None:
    """
    Detect potentially sensitive files about to be committed
    (.env, SSH keys, secrets…). Offers to abort or continue.
    Does not hard-block — the user may choose to continue
    if they know what they are doing (e.g. .env.example with no real values).
    """
    flagged = []
    for _, path in files:
        filename = Path(path).name
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                flagged.append(path)
                break  # one match per file is enough

    if flagged:
        warn("Potentially sensitive files detected:")
        for path in flagged:
            print(f"    {C.YELLOW}⚠  {path}{C.RESET}")
        print(
            f"\n  {C.DIM}These files may contain passwords,\n"
            f"  API keys, or secrets. Verify they belong in this\n"
            f"  commit and are not supposed to be in .gitignore.{C.RESET}"
        )
        if not confirm("Include these files anyway?", default_yes=False):
            abort(
                "Push cancelled.\n"
                "  Add the sensitive files to .gitignore, then run again."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Commit message
# ─────────────────────────────────────────────────────────────────────────────

def ask_commit_message() -> str:
    """
    Prompt the user for a commit message.
    Validates:
        - non-empty message
        - minimum length (MIN_COMMIT_MSG_LENGTH characters)
        - not just spaces / special characters

    Displays Conventional Commits style tips if the user
    seems to be writing a generic message.
    """
    header("Commit message")

    print(
        f"  {C.DIM}Tips — Conventional Commits:\n"
        f"    feat:     add a new feature\n"
        f"    fix:      fix a bug\n"
        f"    docs:     update documentation\n"
        f"    refactor: restructure without behaviour change\n"
        f"    chore:    maintenance task (deps, CI…){C.RESET}\n"
    )

    generic_messages = {
        "update", "fix", "commit", "changes", "wip",
        "test", "modif", "modifs", "maj", "misc",
    }

    while True:
        msg = input(f"  {C.BOLD}Commit message: {C.RESET}").strip()

        if not msg:
            warn("The commit message cannot be empty.")
            continue

        if len(msg) < MIN_COMMIT_MSG_LENGTH:
            warn(
                f"Message too short ({len(msg)} characters).\n"
                f"  Minimum required: {MIN_COMMIT_MSG_LENGTH} characters.\n"
                f"  Be descriptive — this message will live in the Git history."
            )
            continue

        # Warn on overly generic messages
        first_word = msg.split()[0].rstrip(":").lower()
        if first_word in generic_messages and len(msg.split()) <= 2:
            warn(
                f"The message '{msg}' is very generic.\n"
                "  A good message answers: 'What exactly does this commit do?'\n"
                "  Example: 'fix: resolve startup crash on Windows'"
            )
            if not confirm("Keep this message anyway?", default_yes=False):
                continue

        ok(f"Message validated: \"{msg}\"")
        return msg


# ─────────────────────────────────────────────────────────────────────────────
# Summary and final confirmation
# ─────────────────────────────────────────────────────────────────────────────

def show_summary(branch: str, remote_url: str,
                 files: list[tuple[str, str]], commit_msg: str) -> None:
    """
    Display a complete summary of what is about to be executed.
    The user sees exactly what will happen BEFORE it happens.
    """
    header("Summary — what will be executed")

    print(f"  {C.BOLD}Remote :{C.RESET} {remote_url}")
    print(f"  {C.BOLD}Branch :{C.RESET} {branch}")
    print(f"  {C.BOLD}Commit :{C.RESET} \"{commit_msg}\"")
    print(f"\n  {C.BOLD}Files included ({len(files)}):{C.RESET}")
    display_status(files)

    print(f"\n  {C.BOLD}Commands that will be run:{C.RESET}")
    print(f"  {C.DIM}$ git add .{C.RESET}")
    print(f"  {C.DIM}$ git commit -m \"{commit_msg}\"{C.RESET}")
    print(f"  {C.DIM}$ git push origin {branch}{C.RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# Git execution
# ─────────────────────────────────────────────────────────────────────────────

def git_add(repo_path: str) -> None:
    """
    Run 'git add .' to stage all modified files.
    """
    header("git add .")
    result = run(["git", "add", "."], cwd=repo_path, capture=False)
    if result.returncode != 0:
        abort("'git add .' failed.")
    ok("All files have been staged.")


def git_commit(repo_path: str, commit_msg: str) -> None:
    """
    Run 'git commit -m <message>'.
    Prints the short hash of the created commit for traceability.
    """
    header("git commit")
    result = run(
        ["git", "commit", "-m", commit_msg],
        cwd=repo_path,
        capture=True,
    )
    if result.returncode != 0:
        error("'git commit' failed.")
        print(result.stderr.strip())
        abort("Check your git configuration (user.name, user.email).")

    # Print the git commit output (contains the commit hash)
    print(f"  {result.stdout.strip()}")
    ok("Commit created successfully.")


def git_push(repo_path: str, branch: str) -> None:
    """
    Run 'git push origin <branch>'.

    Handles common errors:
        - Branch does not exist on remote → offers --set-upstream
        - Rejected (remote ahead)         → suggests git pull
        - SSH/HTTPS auth error            → targeted diagnosis
        - Network timeout                 → clear message
    """
    header("git push")
    info(f"Pushing to origin/{branch}…")

    result = run(
        ["git", "push", "origin", branch],
        cwd=repo_path,
        capture=True,
    )

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    combined = stdout + "\n" + stderr

    if result.returncode == 0:
        if stdout:
            print(f"  {stdout}")
        if stderr:
            print(f"  {C.DIM}{stderr}{C.RESET}")
        ok("Push successful!")
        return

    # ── Known error diagnosis ────────────────────────────────────────── #

    error("Push failed. Analysing the error…\n")

    if "set-upstream" in combined or "no upstream branch" in combined:
        warn(
            "The branch does not exist on the remote yet.\n"
            f"  Run: git push --set-upstream origin {branch}"
        )
        if confirm("Run git push --set-upstream now?", default_yes=True):
            r2 = run(
                ["git", "push", "--set-upstream", "origin", branch],
                cwd=repo_path,
                capture=False,
            )
            if r2.returncode == 0:
                ok("Push with upstream successful!")
                return
            else:
                abort("--set-upstream push failed.")
        else:
            abort("Push cancelled.")

    elif "rejected" in combined or "non-fast-forward" in combined:
        warn(
            "The remote contains commits you do not have locally.\n"
            "  The push was rejected to avoid overwriting others' work.\n"
            "  Solution: pull the remote changes first:\n"
            f"    git pull origin {branch}\n"
            "  Then run this script again."
        )
        abort("Push rejected — run git pull first.")

    elif "denied" in combined or "Permission" in combined:
        # GitHub formats this refusal as:
        # "ERROR: Permission to user/repo.git denied to wronguser."
        denied_match = re.search(r"denied to (\S+?)\.", combined)
        denied_user = denied_match.group(1) if denied_match else None

        if denied_user and denied_user in ALLOWED_GITHUB_USERS:
            # This account IS legitimate on this repo (known collaborator).
            # The denial is likely transient — agent just switched key, etc.
            # Retry once before giving up.
            warn(
                f"Push denied for '{denied_user}', but this account is a\n"
                f"  known collaborator on this repo ({', '.join(ALLOWED_GITHUB_USERS)}).\n"
                "  Retrying…"
            )
            # ensure_persistent_ssh_config()  # DISABLED — see note at top of file
            r2 = run(["git", "push", "origin", branch], cwd=repo_path, capture=True)
            if r2.returncode == 0:
                ok(f"Push succeeded on second attempt (account: {denied_user}).")
                return
            error(f"Still denied after retry.\n  {r2.stderr.strip()}")
            abort(
                f"'{denied_user}' should be a collaborator but the push still fails.\n"
                "  Check their access rights directly on GitHub\n"
                "  (Settings → Collaborators) or run github_auth_setup.py again."
            )
        else:
            warn(
                "Authentication error / permissions denied.\n"
                "  Possible causes:\n"
                "    1. Wrong active SSH account → run github_auth_setup.py option 3\n"
                "    2. Expired PAT token        → generate a new one on GitHub\n"
                "    3. You are not a collaborator on this repository\n"
                f"  Git output: {stderr}"
            )
            abort("Access denied.")

    elif "Could not resolve host" in combined or "timeout" in combined.lower():
        warn(
            "Network issue — unable to reach GitHub.\n"
            "  Check your internet connection and try again."
        )
        abort("Network error.")

    else:
        # Unknown error: print raw output for diagnosis
        error("Unrecognised error:")
        print(f"  {C.RED}{stderr or stdout}{C.RESET}")
        abort("Push failed.")


# ─────────────────────────────────────────────────────────────────────────────
# Post-push information
# ─────────────────────────────────────────────────────────────────────────────

def post_push_info(repo_path: str, branch: str, remote_url: str) -> None:
    """
    Display useful information after a successful push:
        - Hash of the last commit
        - Direct link to the commit on GitHub (if a GitHub remote is detected)
    """
    header("Post-push summary")

    # Retrieve the short hash of the commit that was just pushed
    result = run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_path,
        capture=True,
    )
    commit_hash = result.stdout.strip() if result.returncode == 0 else "???"

    ok(f"Last pushed commit: {C.BOLD}{commit_hash}{C.RESET}")
    info(f"Branch: {branch}")

    # Build the GitHub link if the remote URL is recognised
    github_match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote_url)
    if github_match:
        repo_slug = github_match.group(1)
        commit_url = f"https://github.com/{repo_slug}/commit/{commit_hash}"
        branch_url = f"https://github.com/{repo_slug}/tree/{branch}"
        info(f"View commit : {commit_url}")
        info(f"View branch : {branch_url}")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    --path allows targeting a repository other than the current directory.
    """
    parser = argparse.ArgumentParser(
        description="Safe Git commit & push with pre-flight checks and alerts."
    )
    parser.add_argument(
        "--path",
        default=os.getcwd(),
        help="Path to the Git repository (default: current directory)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_path = str(Path(args.path).resolve())

    print(f"\n{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}   GIT COMMIT & PUSH — Safe administration script{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}")
    print(f"  Repository: {repo_path}\n")

    # ── Phase 1: Pre-flight checks ───────────────────────────────────── #
    header("Pre-flight checks")

    check_git_installed()
    check_is_git_repo(repo_path)
    remote_url = check_remote(repo_path)
    branch = check_branch(repo_path)
    check_protected_branch(branch)

    # Persistent SSH connection + active GitHub identity check
    # (only relevant for SSH remotes, not HTTPS)
    # DISABLED: ControlMaster/ControlPersist generates noisy warnings
    # ("mux_client_request_session... Connection reset by peer")
    # on Git Bash / Windows with no real benefit here. Functions are kept
    # below in case you want to re-enable on a different environment.
    # if remote_url.startswith("git@") or "ssh://" in remote_url:
    #     ensure_persistent_ssh_config()
    #     check_github_ssh_identity()

    # ── Phase 2: Change analysis ─────────────────────────────────────── #
    header("Modified files")

    files = get_status(repo_path)
    check_no_changes(files)
    check_merge_conflicts(files)

    print(f"  {len(files)} file(s) detected:\n")
    display_status(files)

    check_sensitive_files(files)

    # ── Phase 3: Commit message ──────────────────────────────────────── #
    commit_msg = ask_commit_message()

    # ── Phase 4: Summary and confirmation ───────────────────────────── #
    show_summary(branch, remote_url, files, commit_msg)

    if not confirm(
        "Everything looks good. Run add → commit → push?",
        default_yes=True
    ):
        abort("Operation cancelled by user.")

    # ── Phase 5: Execution ───────────────────────────────────────────── #
    git_add(repo_path)
    git_commit(repo_path, commit_msg)
    git_push(repo_path, branch)

    # ── Phase 6: Final summary ───────────────────────────────────────── #
    post_push_info(repo_path, branch, remote_url)

    print(f"{C.GREEN}{C.BOLD}  ✔  All done!{C.RESET}\n")


if __name__ == "__main__":
    main()
