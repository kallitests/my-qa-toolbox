#!/usr/bin/env python3
"""
git_commit_push_ai.py

GIT ADMINISTRATION SCRIPT — SAFE COMMIT & PUSH WITH AI COMMIT MESSAGE
=======================================================================

AI variant of git_commit_push.py: instead of asking for the commit message
manually, a small Claude model (via LangChain) reads the staged diff and
proposes a Conventional Commits message. You can accept it, edit it, or
ask for a new one.

Automates the complete cycle:
    git add .  →  AI-generated commit message  →  git commit  →  git push

Checks included (in order of execution):
    ✔ Verifies that git is installed
    ✔ Verifies that the current directory is a Git repository
    ✔ Verifies that the 'origin' remote is configured
    ✔ Verifies that the current branch is known (detached HEAD protection)
    ✔ Warns if the branch is 'main' or 'master' (asks for confirmation)
    ✔ Shows modified / untracked files before staging
    ✔ Warns if no changes are detected (nothing to commit)
    ✔ Warns if sensitive files (.env, secrets, keys) are about to be committed
    ✔ Generates a commit message via Claude (LangChain) from the staged diff
    ✔ Lets you accept / edit / regenerate the message before proceeding
    ✔ Displays a full recap before executing anything
    ✔ Asks for final confirmation before pushing
    ✔ Handles SSH / token / network errors with a clear diagnosis
    ✔ Persistent SSH connection + collaborator account awareness

Two AI providers available for commit message generation:

    OLLAMA (default, for TESTING) — 100% local, 0 tokens billed:
        1. Install Ollama      → https://ollama.com
        2. Pull a model        → ollama pull llama3.2
        3. Start the server    → ollama serve
        4. pip install langchain-ollama langchain-core

    ANTHROPIC / CLAUDE (for PRODUCTION) — higher quality, paid:
        export ANTHROPIC_API_KEY="sk-ant-..."
        pip install langchain-anthropic langchain-core

If neither is configured, the script automatically falls back to manual
message input — the workflow is never blocked.

Usage:
    python git_commit_push_ai.py                           # Ollama (default)
    python git_commit_push_ai.py --llm-provider anthropic  # Claude (prod)
    python git_commit_push_ai.py --no-ai                   # forced manual input
    python git_commit_push_ai.py --path /path/to/your/repo
"""

import os
import re
import sys
import argparse
import subprocess
from pathlib import Path

# ── Optional LangChain imports (multi-provider) ───────────────────────────────
# The script must remain usable even if a package is missing or an AI server
# is unreachable: in every case it falls back to manual commit message input
# without blocking the workflow.
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGCHAIN_CORE_AVAILABLE = True
except ImportError:
    LANGCHAIN_CORE_AVAILABLE = False

# ── Available AI providers ────────────────────────────────────────────────────
#
# OLLAMA (default here, for TESTING):
#   - 100% local, 0 tokens billed, no API key required.
#   - Install: https://ollama.com  →  `ollama pull llama3.2`  →  `ollama serve`
#   - The model runs on your machine; the diff never leaves your computer.
#
# ANTHROPIC / CLAUDE (reserved for PRODUCTION):
#   - export ANTHROPIC_API_KEY="sk-ant-..."
#   - Higher message quality, but billed per token.
#
# Other free/local options with zero token cost, if you want to vary testing:
#   - LM Studio        : desktop app, exposes an OpenAI-compatible API
#                        locally → https://lmstudio.ai
#   - llama.cpp server : `llama-server` CLI, OpenAI-compatible, very lightweight
#                        → https://github.com/ggml-org/llama.cpp
#   - GPT4All          : all-in-one desktop app, quantized models, local API
#                        → https://gpt4all.io
#   - Jan              : desktop alternative to ChatGPT, 100% local, local API
#                        → https://jan.ai
#   - text-generation-webui (oobabooga): local web UI, OpenAI-compatible API
#                        → https://github.com/oobabooga/text-generation-webui
#   All these tools expose an OpenAI-compatible API. To wire them in here,
#   just add an `elif provider == "lmstudio"` block using
#   ChatOpenAI(base_url=..., api_key="not-needed") from langchain_openai —
#   same skeleton as for Ollama below.

AI_PROVIDER_DEFAULT = "ollama"   # "ollama" (tests, free) or "anthropic" (prod)

# Claude model used in production. Haiku is intentionally chosen: the task is
# short and unambiguous — no need for a larger model to summarize a diff in
# one line.
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

# Ollama model used locally for testing. Small generalist model, fast even on
# a modest CPU. Change it if you already have something else pulled
# (e.g., "qwen2.5:3b", "phi3", "mistral").
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# Maximum diff size sent to the model (in characters). Beyond this, the diff
# is truncated and the model is notified — the goal is a short prompt, not a
# perfect summary of large refactors. The message remains manually editable
# regardless.
AI_MAX_DIFF_CHARS = 6000


# ─────────────────────────────────────────────────────────────────────────────
# Configuration constants
# ─────────────────────────────────────────────────────────────────────────────

# Branches that require explicit confirmation before any push
PROTECTED_BRANCHES = {"main", "master", "production", "prod", "release"}

# File patterns considered sensitive
SENSITIVE_PATTERNS = [
    r"\.env(\..+)?$",          # .env, .env.local, .env.production …
    r"\.pem$",                 # private certificates
    r"\.key$",                 # private keys
    r"secrets?\.(json|ya?ml|toml)$",
    r"credentials?\.(json|ya?ml)$",
    r"id_rsa",                 # SSH private keys
    r"id_ed25519$",
    r"\.p12$",                 # keystores
    r"\.pfx$",
    r"config\.ya?ml$",         # potentially sensitive config files
    r"database\.ya?ml$",
]

# Minimum acceptable length for a commit message
MIN_COMMIT_MSG_LENGTH = 10

# Legitimate GitHub accounts for this repository: khafidmedheb is a collaborator
# of the project hosted under khafid1506. If a push fails but the authenticated
# SSH identity is one of these two accounts, it is not a real access error —
# the script should not abort on that basis.
ALLOWED_GITHUB_USERS = {"khafid1506", "khafidmedheb"}

# SSH target host for the persistent connection (avoids re-authenticating
# on every git command run by the script)
SSH_PERSISTENT_HOST = "github.com"

# ANSI terminal colors


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
    """Print a fatal error and exit the script."""
    error(msg)
    print(f"\n{C.RED}{C.BOLD}  Aborting.{C.RESET}\n")
    sys.exit(1)


def confirm(prompt: str, default_yes: bool = False) -> bool:
    """
    Ask the user for a y/n confirmation.
    default_yes=True → pressing Enter alone counts as 'yes'.
    """
    hint = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"\n{C.BOLD}  {prompt} {hint} : {C.RESET}").strip().lower()
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
        abort("Git is not installed or not in PATH.")
    ok(f"Git detected: {result.stdout.strip()}")


def check_is_git_repo(repo_path: str) -> None:
    """
    Verify that repo_path (or the current directory) is inside a Git
    repository. 'git rev-parse --git-dir' fails if it is not.
    """
    result = run(["git", "rev-parse", "--git-dir"], cwd=repo_path)
    if result.returncode != 0:
        abort(
            f"'{repo_path}' is not a Git repository.\n"
            "  Run: git init"
        )
    ok(f"Valid Git repository: {repo_path}")


def check_remote(repo_path: str) -> str:
    """
    Verify that an 'origin' remote is configured and return its URL.
    Without a remote, git push has nowhere to send commits.
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
    Get the current branch name.
    Warns if in detached HEAD mode (dangerous for pushes).
    """
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if result.returncode != 0:
        abort("Cannot determine the current branch.")

    branch = result.stdout.strip()

    if branch == "HEAD":
        # Detached HEAD: commits are not attached to any branch.
        # A push in this state is usually a mistake.
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
    Pushing directly to main is often bad practice.
    """
    if branch in PROTECTED_BRANCHES:
        warn(
            f"You are on the protected branch '{C.BOLD}{branch}{C.RESET}{C.YELLOW}'.\n"
            f"  Pushing directly to '{branch}' is risky in a team setting.\n"
            "  Prefer a feature branch + Pull Request."
        )
        if not confirm(f"Continue anyway on '{branch}'?", default_yes=False):
            abort("Push cancelled by user.")


# ─────────────────────────────────────────────────────────────────────────────
# Persistent SSH connection + GitHub identity check
# ─────────────────────────────────────────────────────────────────────────────

def _control_socket_path() -> Path:
    """Return the SSH control socket path used for github.com."""
    return Path.home() / ".ssh" / "sockets" / f"git@{SSH_PERSISTENT_HOST}-22"


def clear_stale_ssh_socket() -> None:
    """
    Remove the SSH control socket if it exists but is no longer responding.

    A 'dead' socket (previous SSH process killed, PC put to sleep, etc.)
    stays on disk and causes exactly the following symptom:
        mux_client_request_session: read from master failed: Connection reset by peer
        ControlSocket ... already exists, disabling multiplexing
    SSH refuses to reuse an existing socket even if it is dead, and the
    push fails because of the connection, not because of permissions.

    'ssh -O check' queries the socket: exit 0 = alive, anything else = dead.
    """
    socket_path = _control_socket_path()
    if not socket_path.exists():
        return

    check = run(
        ["ssh", "-O", "check", "-o", f"ControlPath={socket_path}", f"git@{SSH_PERSISTENT_HOST}"]
    )
    if check.returncode != 0:
        warn(f"Stale SSH socket detected ({socket_path.name}) — cleaning up…")
        try:
            socket_path.unlink()
            ok("Stale socket removed. The next connection will start fresh.")
        except OSError as e:
            warn(f"Could not remove stale socket: {e}")
    else:
        ok("Existing SSH socket is alive — reusing it.")


def ensure_persistent_ssh_config() -> None:
    """
    Ensure a 'ControlMaster/ControlPersist' entry exists in ~/.ssh/config
    for github.com.

    Without this, each git command (fetch/push/ssh -T) opens a NEW SSH
    session and may trigger re-authentication or fall back to a different key.
    With ControlPersist, the first connection stays open and all subsequent
    commands reuse it — giving a "connected once" experience for the duration
    of the script (and 10 minutes after, enough to chain several operations).

    Idempotent: only adds the block if it is absent.
    """
    ssh_dir = Path.home() / ".ssh"
    config_path = ssh_dir / "config"
    sockets_dir = ssh_dir / "sockets"

    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    sockets_dir.mkdir(mode=0o700, exist_ok=True)

    # Always check/clean the existing socket, even if the config block is
    # already present — it is the most common cause of push failure.
    clear_stale_ssh_socket()

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
    Run 'ssh -T git@github.com' to determine WHICH GitHub account is
    actually responding to the active SSH authentication.

    GitHub always responds with exit code 1 on this test (that is normal,
    not an error), with a message like:
        "Hi khafidmedheb! You've successfully authenticated, but GitHub
         does not provide shell access."

    Returns the detected username, or None if it cannot be determined.
    """
    result = run(["ssh", "-T", "-o", "BatchMode=yes", f"git@{SSH_PERSISTENT_HOST}"])
    combined = f"{result.stdout}\n{result.stderr}"

    match = re.search(r"Hi (\S+?)!", combined)
    if not match:
        warn("Cannot determine the active SSH identity (ssh -T returned no usable output).")
        return None

    username = match.group(1)

    if username in ALLOWED_GITHUB_USERS:
        ok(f"Active SSH identity: {C.BOLD}{username}{C.RESET} (authorized account for this repo).")
    else:
        warn(
            f"Active SSH identity: {username} — this account is NOT in the list\n"
            f"  of authorized accounts ({', '.join(ALLOWED_GITHUB_USERS)}).\n"
            "  The push may be rejected if this account is not a collaborator."
        )

    return username


# ─────────────────────────────────────────────────────────────────────────────
# Modified files analysis
# ─────────────────────────────────────────────────────────────────────────────

def get_status(repo_path: str) -> list[tuple[str, str]]:
    """
    Return the list of modified files as (status_code, path) tuples.
    'git status --porcelain' produces stable, scriptable output:
       M  file.py    -> modified
       ?? new.txt    -> untracked
       D  deleted.go -> deleted
       etc.
    """
    result = run(["git", "status", "--porcelain"], cwd=repo_path)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    parsed = []
    for line in lines:
        # First two characters = status code, the rest = path
        code = line[:2].strip()
        path = line[3:].strip()
        parsed.append((code, path))
    return parsed


def display_status(files: list[tuple[str, str]]) -> None:
    """Print the file list with a color based on each file's status."""
    code_labels = {
        "M":  (C.YELLOW, "modified"),
        "MM": (C.YELLOW, "modified"),
        "A":  (C.GREEN,  "added   "),
        "D":  (C.RED,    "deleted "),
        "R":  (C.CYAN,   "renamed "),
        "C":  (C.CYAN,   "copied  "),
        "??": (C.DIM,    "new     "),
        "UU": (C.RED,    "conflict"),
    }
    for code, path in files:
        color, label = code_labels.get(code, (C.WHITE, code.ljust(8)))
        print(f"    {color}{label}{C.RESET}  {path}")


def check_no_changes(files: list[tuple[str, str]]) -> None:
    """
    Stop the script if no changes are detected.
    Avoids creating an empty commit that would pollute the history.
    """
    if not files:
        abort(
            "No changes detected.\n"
            "  The working tree is clean — nothing to commit."
        )


def check_merge_conflicts(files: list[tuple[str, str]]) -> None:
    """
    Detect files with unresolved merge conflicts (code 'UU', 'AA'…).
    Committing with conflict markers (<<<<<<<) is always a mistake.
    """
    conflict_codes = {"UU", "AA", "DD", "AU", "UA", "DU", "UD"}
    conflicts = [(c, p) for c, p in files if c in conflict_codes]
    if conflicts:
        error("Unresolved merge conflicts:")
        for code, path in conflicts:
            print(f"    {C.RED}{code}  {path}{C.RESET}")
        abort(
            "Resolve conflicts before committing.\n"
            "  Use: git mergetool  or edit files manually,\n"
            "  then: git add <file>"
        )


def check_sensitive_files(files: list[tuple[str, str]]) -> None:
    """
    Detect potentially sensitive files about to be committed
    (.env, SSH keys, secrets…). Offers to abort or continue.
    Does not hard-block — the user can choose to continue if they know
    what they are doing (e.g., .env.example with no real values).
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
            f"  API keys, or secrets. Verify that they belong in\n"
            f"  this commit and are not listed in .gitignore.{C.RESET}"
        )
        if not confirm("Include these files anyway?", default_yes=False):
            abort(
                "Push cancelled.\n"
                "  Add sensitive files to .gitignore, then run the script again."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Commit message — AI generation (LangChain + Claude)
# ─────────────────────────────────────────────────────────────────────────────

# System prompt intentionally kept short: one instruction per line, no
# justification, no superfluous examples. Fewer input tokens per call, and a
# message that does not drift into a novel.
AI_SYSTEM_PROMPT = (
    "You write Git commit messages in Conventional Commits format.\n"
    "One line only. Maximum 72 characters. In English.\n"
    "Format: <type>(<optional scope>): <description in present tense>\n"
    "Valid types: feat, fix, docs, refactor, chore, test, style, perf.\n"
    "No trailing period. No em dash. No quotes.\n"
    "Reply with the message only, nothing else."
)


def get_staged_diff(repo_path: str) -> str:
    """
    Retrieve the staged diff (what will actually be committed), truncated to
    AI_MAX_DIFF_CHARS to keep the prompt short. '--stat' provides a per-file
    summary in addition to the full diff, useful to the model even if the raw
    diff is cut mid-way — the message remains manually editable regardless.
    """
    stat = run(["git", "diff", "--staged", "--stat"], cwd=repo_path, capture=True)
    diff = run(["git", "diff", "--staged"], cwd=repo_path, capture=True)

    full_diff = diff.stdout or ""
    truncated = len(full_diff) > AI_MAX_DIFF_CHARS
    if truncated:
        full_diff = full_diff[:AI_MAX_DIFF_CHARS]

    payload = f"Changed files summary:\n{stat.stdout.strip()}\n\nDiff:\n{full_diff}"
    if truncated:
        payload += "\n\n[diff truncated — rely mainly on the file summary above]"

    return payload


def generate_ai_commit_message(repo_path: str, provider: str) -> str | None:
    """
    Ask an LLM (via LangChain) for a commit message based on the staged diff.
    Returns None if the AI is unavailable / misconfigured or if the call fails
    — the script must always be able to continue in manual mode in that case.

    provider: "ollama" (local, free, for testing) or
              "anthropic" (Claude, paid API, for production)
    """
    if not LANGCHAIN_CORE_AVAILABLE:
        warn("langchain-core not installed — AI message unavailable.")
        info("Install it with: pip install langchain-core")
        return None

    diff_payload = get_staged_diff(repo_path)
    if not diff_payload.strip():
        return None

    llm = None

    if provider == "ollama":
        if not OLLAMA_AVAILABLE:
            warn("langchain-ollama not installed — AI message unavailable.")
            info("Install it with: pip install langchain-ollama")
            return None
        try:
            llm = ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=0,
                num_predict=60,   # equivalent of max_tokens on the Ollama side
            )
        except Exception as e:
            warn(f"Cannot initialize Ollama ({OLLAMA_MODEL}): {e}")
            info(
                f"Make sure Ollama is running (`ollama serve`) and the model\n"
                f"  is downloaded (`ollama pull {OLLAMA_MODEL}`)."
            )
            return None

    elif provider == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            warn("langchain-anthropic not installed — AI message unavailable.")
            info("Install it with: pip install langchain-anthropic")
            return None
        if not os.environ.get("ANTHROPIC_API_KEY"):
            warn("ANTHROPIC_API_KEY not set — AI message unavailable.")
            return None
        try:
            llm = ChatAnthropic(model=ANTHROPIC_MODEL, max_tokens=60, temperature=0)
        except Exception as e:
            warn(f"Cannot initialize Claude ({ANTHROPIC_MODEL}): {e}")
            return None

    else:
        warn(f"Unknown AI provider: '{provider}'.")
        return None

    try:
        response = llm.invoke([
            SystemMessage(content=AI_SYSTEM_PROMPT),
            HumanMessage(content=diff_payload),
        ])
        message = response.content.strip().strip('"')
        return message if message else None
    except Exception as e:
        warn(f"AI commit message generation failed ({provider}): {e}")
        if provider == "ollama":
            info("Make sure Ollama is running: `ollama serve` (in a separate terminal).")
        return None


def ask_commit_message_ai(
    repo_path: str,
    use_ai: bool = True,
    provider: str = AI_PROVIDER_DEFAULT,
) -> str:
    """
    Propose an AI-generated commit message based on the staged diff.
    The user can:
        [Enter]  accept the proposed message
        r        regenerate a new message
        anything else → used as-is as the commit message

    If the AI is unavailable or disabled (--no-ai), falls back directly
    to classic manual input (ask_commit_message).
    """
    header("Commit message")

    if not use_ai:
        info("AI mode disabled (--no-ai) — manual input.")
        return ask_commit_message()

    info(f"Generating commit message via AI (provider: {provider})…")
    suggestion = generate_ai_commit_message(repo_path, provider)

    if suggestion is None:
        warn("Falling back to manual input.")
        return ask_commit_message()

    while True:
        print(f"\n  {C.BOLD}Suggested message:{C.RESET} {C.GREEN}{suggestion}{C.RESET}")
        answer = input(
            f"\n  {C.DIM}[Enter] accept · 'r' regenerate · "
            f"or type your own message{C.RESET}\n  > "
        ).strip()

        if answer == "":
            ok(f'Message accepted: "{suggestion}"')
            return suggestion

        if answer.lower() == "r":
            info("Regenerating…")
            new_suggestion = generate_ai_commit_message(repo_path, provider)
            if new_suggestion is None:
                warn("Regeneration failed — falling back to manual input.")
                return ask_commit_message()
            suggestion = new_suggestion
            continue

        if len(answer) < MIN_COMMIT_MSG_LENGTH:
            warn(
                f"Message too short ({len(answer)} characters).\n"
                f"  Minimum required: {MIN_COMMIT_MSG_LENGTH} characters."
            )
            continue

        ok(f'Message accepted: "{answer}"')
        return answer


def ask_commit_message() -> str:
    """
    Prompt the user to type a commit message.
    Validates:
        - non-empty message
        - minimum length (MIN_COMMIT_MSG_LENGTH characters)
        - not only spaces / special characters

    Shows Conventional Commits style tips if the user seems to be writing
    a generic message.
    """
    header("Commit message")

    print(
        f"  {C.DIM}Tips — Conventional Commits:\n"
        f"    feat:     add a new feature\n"
        f"    fix:      fix a bug\n"
        f"    docs:     documentation change\n"
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
            warn("Commit message cannot be empty.")
            continue

        if len(msg) < MIN_COMMIT_MSG_LENGTH:
            warn(
                f"Message too short ({len(msg)} characters).\n"
                f"  Minimum required: {MIN_COMMIT_MSG_LENGTH} characters.\n"
                "  Be descriptive — this message lives in the Git history."
            )
            continue

        # Alert on overly generic messages
        first_word = msg.split()[0].rstrip(":").lower()
        if first_word in generic_messages and len(msg.split()) <= 2:
            warn(
                f"The message '{msg}' is very generic.\n"
                "  A good message answers: 'What exactly does this commit do?'\n"
                "  Example: 'fix: resolve crash on startup on Windows'"
            )
            if not confirm("Keep this message anyway?", default_yes=False):
                continue

        ok(f'Message accepted: "{msg}"')
        return msg


# ─────────────────────────────────────────────────────────────────────────────
# Recap and final confirmation
# ─────────────────────────────────────────────────────────────────────────────

def show_summary(branch: str, remote_url: str,
                 files: list[tuple[str, str]], commit_msg: str) -> None:
    """
    Display a complete recap of what is about to be executed.
    The user sees exactly what will happen BEFORE it happens.
    """
    header("Summary — what will be executed")

    print(f"  {C.BOLD}Remote :{C.RESET} {remote_url}")
    print(f"  {C.BOLD}Branch :{C.RESET} {branch}")
    print(f"  {C.BOLD}Commit :{C.RESET} \"{commit_msg}\"")
    print(f"\n  {C.BOLD}Files included ({len(files)}):{C.RESET}")
    display_status(files)

    print(f"\n  {C.BOLD}Remaining commands:{C.RESET}")
    print(f"  {C.DIM}$ git add .          (already done){C.RESET}")
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
    ok("All files staged.")


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

    # Print git commit output (includes the commit hash)
    print(f"  {result.stdout.strip()}")
    ok("Commit created successfully.")


def git_push(repo_path: str, branch: str) -> None:
    """
    Run 'git push origin <branch>'.

    Handles common errors:
        - Branch not on remote yet  → offers --set-upstream
        - Rejected (remote ahead)   → suggests git pull
        - SSH/HTTPS auth error      → targeted diagnosis
        - Network timeout           → clear error message
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
        ok("Push succeeded!")
        return

    # ── Known error diagnosis ─────────────────────────────────────────── #

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
                ok("Push with upstream succeeded!")
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
        # GitHub formats this refusal as: "ERROR: Permission to user/repo.git denied to wronguser."
        denied_match = re.search(r"denied to (\S+?)\.", combined)
        denied_user = denied_match.group(1) if denied_match else None

        if denied_user and denied_user in ALLOWED_GITHUB_USERS:
            # This account IS legitimate on this repository (known collaborator).
            # The refusal may come from a stale SSH socket (frequent cause,
            # see "Connection reset by peer" / "already exists, disabling
            # multiplexing") rather than a real permission issue.
            # Clean the socket and retry once before aborting.
            warn(
                f"Push denied for '{denied_user}', but this account is a\n"
                f"  known collaborator of this repo ({', '.join(ALLOWED_GITHUB_USERS)}).\n"
                "  Cleaning SSH socket and retrying…"
            )
            clear_stale_ssh_socket()
            ensure_persistent_ssh_config()
            r2 = run(["git", "push", "origin", branch], cwd=repo_path, capture=True)
            if r2.returncode == 0:
                ok(f"Push succeeded on second attempt (account: {denied_user}).")
                return
            error(f"Still denied after retry.\n  {r2.stderr.strip()}")
            abort(
                f"'{denied_user}' should be a collaborator but push keeps failing.\n"
                "  This is no longer an SSH connection issue — check on GitHub:\n"
                "    1. https://github.com/khafid1506/CV-ATS-Optimizer/settings/access\n"
                f"       → '{denied_user}' must appear with Write access (not Pending)\n"
                "    2. https://github.com/khafid1506/CV-ATS-Optimizer/invitations\n"
                f"       → if an invitation is pending, '{denied_user}' must accept it"
            )
        else:
            warn(
                "Authentication / permission error.\n"
                "  Possible causes:\n"
                "    1. Wrong active SSH account → run github_auth_setup.py option 3\n"
                "    2. Expired PAT token        → generate a new one on GitHub\n"
                "    3. You are not a collaborator on this repository\n"
                f"  Git output: {stderr}"
            )
            abort("Access denied.")

    elif "Could not resolve host" in combined or "timeout" in combined.lower():
        warn(
            "Network error — cannot reach GitHub.\n"
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
        - Short hash of the last commit
        - Direct link to the commit on GitHub (if a GitHub remote is detected)
    """
    header("Post-push summary")

    # Get the short hash of the commit just pushed
    result = run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_path,
        capture=True,
    )
    commit_hash = result.stdout.strip() if result.returncode == 0 else "???"

    ok(f"Last commit pushed: {C.BOLD}{commit_hash}{C.RESET}")
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
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    --path lets you target a repository other than the current directory.
    """
    parser = argparse.ArgumentParser(
        description="Safe git commit & push with pre-flight checks and AI commit message."
    )
    parser.add_argument(
        "--path",
        default=os.getcwd(),
        help="Path to the Git repository (default: current directory)",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        default=False,
        help="Disable AI commit message generation (manual input)",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["ollama", "anthropic"],
        default=os.environ.get("LLM_PROVIDER", AI_PROVIDER_DEFAULT),
        help=(
            "AI provider for the commit message: "
            "'ollama' (local, free, default — for testing) or "
            "'anthropic' (Claude, requires ANTHROPIC_API_KEY — for production). "
            "Can also be set via the LLM_PROVIDER environment variable."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_path = str(Path(args.path).resolve())

    print(f"\n{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}   GIT COMMIT & PUSH — AI-assisted{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 60}{C.RESET}")
    print(f"  Repo : {repo_path}")
    if not args.no_ai:
        provider_label = (
            "Ollama (local, free)" if args.llm_provider == "ollama"
            else "Claude / Anthropic (API)"
        )
        print(f"  AI   : {provider_label}\n")
    else:
        print("  AI   : disabled (--no-ai)\n")

    # ── Phase 1: Pre-flight checks ───────────────────────────────────── #
    header("Pre-flight checks")

    check_git_installed()
    check_is_git_repo(repo_path)
    remote_url = check_remote(repo_path)
    branch = check_branch(repo_path)
    check_protected_branch(branch)

    # Persistent SSH connection + GitHub identity check
    # (only relevant for SSH remotes, not HTTPS)
    if remote_url.startswith("git@") or "ssh://" in remote_url:
        ensure_persistent_ssh_config()
        check_github_ssh_identity()

    # ── Phase 2: Change analysis ─────────────────────────────────────── #
    header("Modified files")

    files = get_status(repo_path)
    check_no_changes(files)
    check_merge_conflicts(files)

    print(f"  {len(files)} file(s) detected:\n")
    display_status(files)

    check_sensitive_files(files)

    # ── Phase 3: Staging (required so the AI reads the real diff) ────── #
    git_add(repo_path)

    # ── Phase 4: Commit message (AI, with manual fallback) ───────────── #
    commit_msg = ask_commit_message_ai(
        repo_path, use_ai=not args.no_ai, provider=args.llm_provider
    )

    # ── Phase 5: Recap and confirmation ──────────────────────────────── #
    show_summary(branch, remote_url, files, commit_msg)

    if not confirm("Everything looks good. Run commit → push?", default_yes=True):
        abort("Operation cancelled by user.")

    # ── Phase 6: Execution ───────────────────────────────────────────── #
    git_commit(repo_path, commit_msg)
    git_push(repo_path, branch)

    # ── Phase 7: Final summary ───────────────────────────────────────── #
    post_push_info(repo_path, branch, remote_url)

    print(f"{C.GREEN}{C.BOLD}  ✔  All done!{C.RESET}\n")


if __name__ == "__main__":
    main()
