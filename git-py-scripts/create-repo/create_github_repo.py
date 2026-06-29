#!/usr/bin/env python3
"""
create_github_repo.py
─────────────────────
Creates a public GitHub repository from the CURRENT directory:
takes every file already present in the folder where the script is run,
initializes git in place, makes an initial commit, and pushes to GitHub.

Usage:
    python create_github_repo.py <repo-name> [--description "..."] [--private]
    python create_github_repo.py <repo-name> [--exclude file1 dir2 ...]
    python create_github_repo.py <repo-name> [--message "..."]

Requirements:
    - Git installed and available in PATH
    - GitHub CLI (gh) installed and authenticated  → https://cli.github.com
    - Run this script FROM the root folder you want to push
      (everything in that folder, minus the exclusions below, gets pushed)

Author : Khalid HAFID-MEDHEB
"""

# ── Standard library imports ─────────────────────────────────────────────────

import argparse          # Parse command-line arguments cleanly
import os                # File-system operations (path checks, directory listing)
import shutil            # Used to locate git/gh binaries in PATH
import subprocess        # Run shell commands (git, gh) from Python
import sys               # Access sys.exit() to stop the script on fatal errors

# ── ANSI colour codes for terminal output ────────────────────────────────────
# These make success / warning / error messages easy to spot at a glance.

GREEN = "\033[92m"    # ✅ Success messages
YELLOW = "\033[93m"   # ⚠️  Warning messages
RED = "\033[91m"      # ❌  Error / fatal messages
CYAN = "\033[96m"     # ℹ️   Info / step messages
RESET = "\033[0m"     # Resets colour back to terminal default

# Files/folders that are NEVER sent to the remote repo, even without --exclude.
# This is a safety net against junk and secrets accidentally living in root.
DEFAULT_EXCLUDES = {
    ".git", ".gitignore",
    "__pycache__", ".venv", "venv", "env",
    "node_modules",
    ".env", ".env.local",
    os.path.basename(__file__),   # never push the script that pushes things
}

# GitHub accounts considered legitimate on every repo this script creates.
# Whichever of these two is NOT the account `gh` is currently authenticated
# as gets auto-invited as a collaborator right after repo creation — this is
# what avoids the "denied to khafidmedheb" surprise later, the first time
# someone pushes from a machine authenticated under the other account.
ALLOWED_GITHUB_USERS = {"khafid1506", "khafidmedheb"}

# If a push is denied for one of ALLOWED_GITHUB_USERS, the script also
# retries the auto-invite at push time as a safety net (e.g. if the initial
# invite at creation time failed for some reason).
AUTO_INVITE_COLLABORATOR = True
DEFAULT_COLLABORATOR_PERMISSION = "push"  # "pull" | "push" | "admin" | "maintain" | "triage"


# ── Helper print functions ────────────────────────────────────────────────────

def info(msg: str) -> None:
    """Print a blue informational message (non-blocking)."""
    print(f"{CYAN}[INFO]  {msg}{RESET}")


def success(msg: str) -> None:
    """Print a green success message (non-blocking)."""
    print(f"{GREEN}[OK]    {msg}{RESET}")


def warn(msg: str) -> None:
    """Print a yellow warning message (non-blocking — script continues)."""
    print(f"{YELLOW}[WARN]  {msg}{RESET}")


def fatal(msg: str) -> None:
    """Print a red error message and immediately stop the script."""
    print(f"{RED}[ERROR] {msg}{RESET}")
    sys.exit(1)          # Exit code 1 = failure (used by CI/CD to detect errors)


# ── Shell command runner ──────────────────────────────────────────────────────

def run(
    cmd: list[str],
    cwd: str | None = None,
    capture: bool = False
) -> subprocess.CompletedProcess:
    """
    Run a shell command and return its result.

    Args:
        cmd     : Command as a list of tokens, e.g. ["git", "init"]
        cwd     : Working directory for the command (None = current directory)
        capture : If True, capture stdout/stderr instead of printing them live

    Returns:
        CompletedProcess with .returncode, .stdout, .stderr

    Raises:
        Calls fatal() and exits if the command returns a non-zero exit code.
    """
    info(f"Running: {' '.join(cmd)}")   # Log every command before executing

    result = subprocess.run(
        cmd,
        cwd=cwd,                        # Set working directory for git commands
        capture_output=capture,         # Capture output for programmatic checks
        text=True                       # Decode stdout/stderr as UTF-8 strings
    )

    # A non-zero return code means the command failed
    if result.returncode != 0:
        # Print captured stderr if available, otherwise fall back to a generic message
        error_detail = result.stderr.strip() if result.stderr else "no details captured"
        fatal(f"Command failed (exit {result.returncode}): {' '.join(cmd)}\n  → {error_detail}")

    return result


# ── Pre-flight checks ─────────────────────────────────────────────────────────

def check_git_installed() -> None:
    """Verify that git is installed and reachable in PATH."""
    result = shutil.which("git")       # Returns the full path to git, or None
    if result is None:
        fatal("git is not installed or not in PATH. Install it from https://git-scm.com")
    success(f"git found at {result}")


def check_gh_installed() -> None:
    """Verify that the GitHub CLI (gh) is installed and reachable in PATH."""
    result = shutil.which("gh")        # Same check for the gh binary
    if result is None:
        fatal("GitHub CLI (gh) is not installed. Install it from https://cli.github.com")
    success(f"gh found at {result}")


def check_gh_authenticated() -> None:
    """
    Verify that the user is logged in to GitHub CLI.
    'gh auth status' returns exit code 0 if authenticated, 1 if not.
    """
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        fatal(
            "You are not authenticated with GitHub CLI.\n"
            "  Run:  gh auth login\n"
            "  Then re-run this script."
        )
    success("GitHub CLI is authenticated.")


def check_repo_name(name: str) -> None:
    """
    Validate the repository name against GitHub's naming rules:
    - Only letters, digits, hyphens, underscores, and dots are allowed
    - Must not start or end with a dot
    """
    import re                          # Import here — only needed for this check

    # GitHub repo name pattern: alphanumeric + hyphen + underscore + dot
    pattern = r'^[a-zA-Z0-9_.-]+$'

    if not re.match(pattern, name):
        fatal(
            f"Invalid repo name '{name}'.\n"
            "  Allowed characters: letters, digits, hyphens (-), underscores (_), dots (.)\n"
            "  Must not contain spaces or special characters."
        )

    if name.startswith(".") or name.endswith("."):
        fatal(f"Repo name '{name}' must not start or end with a dot.")

    success(f"Repo name '{name}' is valid.")


def check_repo_not_exists_remotely(repo_name: str) -> None:
    """
    Check whether a repo with this name already exists on the authenticated
    GitHub account. Prevents accidental overwrites.
    'gh repo view <name>' returns exit code 0 if the repo exists.
    """
    result = subprocess.run(
        ["gh", "repo", "view", repo_name],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        # Exit code 0 means the repo was found — that is a problem here
        fatal(
            f"A GitHub repo named '{repo_name}' already exists on your account.\n"
            "  Choose a different name, or delete the existing repo first."
        )
    success(f"No existing remote repo named '{repo_name}' found. Safe to create.")


def check_not_already_a_git_repo() -> bool:
    """
    Check the current directory's git state.

    - No .git at all              → safe to 'git init' normally.
    - .git exists, no 'origin'    → harmless leftover (e.g. an interrupted
                                     previous run). Ask the user whether to
                                     reuse it instead of hard-blocking.
    - .git exists WITH an origin  → real conflict, abort. Overwriting an
                                     already-wired remote risks pushing to
                                     the wrong repo or losing history.

    Returns:
        True if a fresh 'git init' should run, False if an existing repo
        should be reused as-is (already initialised, no remote yet).
    """
    if not os.path.isdir(".git"):
        success("Current directory is not already a git repository. Safe to init.")
        return True

    existing_remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True
    )

    if existing_remote.returncode == 0:
        fatal(
            f"This directory is already a git repository with an 'origin' remote:\n"
            f"  {existing_remote.stdout.strip()}\n"
            "  Pushing here could overwrite history on the wrong repo.\n"
            "  Remove .git first if you really want to start fresh, or run\n"
            "  this script from a clean folder."
        )

    warn(
        "This directory already has a .git folder, but no 'origin' remote\n"
        "  is configured — likely a leftover from an interrupted previous run."
    )
    prompt = f"{YELLOW}  Reuse this existing local repo instead of starting fresh? [y/N]: {RESET}"
    if input(prompt).strip().lower() not in ("y", "yes", "o", "oui"):
        fatal(
            "Aborted. Remove .git manually if you want a completely fresh start:\n"
            "  rmdir /s /q .git   (Windows)   or   rm -rf .git   (Linux/Mac)"
        )

    success("Reusing existing local git repository (no origin configured yet).")
    return False


def discover_source_files(exclude: set[str]) -> list[str]:
    """
    List every file and top-level folder in the current directory,
    minus DEFAULT_EXCLUDES and anything passed via --exclude.

    Returns:
        Sorted list of relative paths (files and/or folders) to be pushed.
    """
    all_excludes = DEFAULT_EXCLUDES | exclude   # Merge built-in + user excludes

    entries = sorted(os.listdir("."))           # Everything at root level
    kept = [e for e in entries if e not in all_excludes]

    if not kept:
        fatal(
            "No files found to push (current folder is empty, or everything "
            "is excluded). Check your --exclude list."
        )

    for e in kept:
        success(f"Will push: {e}")

    for e in entries:
        if e in all_excludes:
            warn(f"Excluded: {e}")

    return kept


# ── Collaborator auto-invite ────────────────────────────────────────────────

def get_authenticated_username() -> str:
    """
    Return the GitHub username `gh` is currently authenticated as.
    Used to figure out which of the ALLOWED_GITHUB_USERS still needs
    to be invited as a collaborator (the creator already has access).
    """
    result = run(["gh", "api", "user", "--jq", ".login"], capture=True)
    username = result.stdout.strip()
    if not username:
        fatal("Could not determine your GitHub username. Check 'gh auth status'.")
    return username


def add_collaborator_via_gh(
    repo_slug: str,
    username: str,
    permission: str = DEFAULT_COLLABORATOR_PERMISSION,
) -> bool:
    """
    Invite `username` as a collaborator on `repo_slug` via the GitHub API
    (through `gh api`). The currently gh-authenticated account must have
    admin rights on the repo — true by default right after `gh repo create`,
    since the creator is always an admin.

    Returns True on success, False otherwise (never raises/fatals — a failed
    invite here should not block the rest of the workflow).
    """
    info(f"Inviting '{username}' as a collaborator on {repo_slug} (permission: {permission})...")

    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{repo_slug}/collaborators/{username}",
            "-X", "PUT",
            "-f", f"permission={permission}",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        success(f"'{username}' added/confirmed as a collaborator ({permission}).")
        return True

    detail = (result.stderr or result.stdout or "").strip()
    warn(f"Could not add '{username}' as a collaborator automatically.\n  → {detail[:200]}")
    return False


def invite_known_collaborators(repo_slug: str) -> None:
    """
    Right after repo creation: invite every account in ALLOWED_GITHUB_USERS
    that is NOT the currently authenticated `gh` user. This is what prevents
    the classic "Permission ... denied to <other-account>" surprise the first
    time someone pushes from a machine logged in as the other allowed account.
    """
    if not AUTO_INVITE_COLLABORATOR:
        return

    creator = get_authenticated_username()
    others = ALLOWED_GITHUB_USERS - {creator}

    for username in others:
        add_collaborator_via_gh(repo_slug, username)


# ── Core workflow ─────────────────────────────────────────────────────────────

def create_remote_repo(repo_name: str, description: str, private: bool) -> None:
    """
    Create the GitHub repository via the GitHub CLI.
    Sets visibility to public or private based on the --private flag.
    """
    visibility_flag = "--private" if private else "--public"   # Toggle visibility

    run([
        "gh", "repo", "create", repo_name,
        visibility_flag,
        "--description", description
    ])

    visibility_label = "private" if private else "public"
    success(f"Remote repo '{repo_name}' created as {visibility_label} on GitHub.")

    # Auto-invite the other known account as collaborator right away —
    # avoids a denied push later from a machine authenticated as that account.
    creator = get_authenticated_username()
    repo_slug = f"{creator}/{repo_name}"
    invite_known_collaborators(repo_slug)


def init_local_repo(fresh_init: bool) -> str:
    """
    Initialise a git repo IN PLACE (current directory), and set the
    default branch to 'main' (GitHub's current default).

    If fresh_init is False, an existing .git (with no origin) is reused
    as-is instead of running 'git init' again — avoids clobbering whatever
    local state already exists (e.g. a previous interrupted attempt).

    Returns:
        The absolute path to the current directory (now a git repo).
    """
    repo_path = os.path.abspath(".")                 # Current dir, resolved to absolute path

    if fresh_init:
        run(["git", "init"], cwd=repo_path)           # Initialise empty git repo
        success(f"Git repository initialised in {repo_path}.")

    # Make sure we're on 'main' regardless of fresh init or reuse.
    # '-B' creates the branch if missing, or just switches to it if it
    # already exists — safe in both cases.
    run(["git", "checkout", "-B", "main"], cwd=repo_path)

    success(f"On branch 'main' in {repo_path}.")
    return repo_path


def set_remote_origin(repo_name: str, repo_path: str) -> None:
    """
    Get the authenticated GitHub username via gh CLI and add the remote
    'origin' URL so git push knows where to send the commits.
    """
    # Fetch the authenticated GitHub username programmatically
    result = run(["gh", "api", "user", "--jq", ".login"], capture=True)
    github_username = result.stdout.strip()   # Remove trailing newline

    if not github_username:
        fatal("Could not determine your GitHub username. Check 'gh auth status'.")

    # Build the HTTPS remote URL
    remote_url = f"https://github.com/{github_username}/{repo_name}.git"
    run(["git", "remote", "add", "origin", remote_url], cwd=repo_path)
    success(f"Remote 'origin' set to {remote_url}")


def stage_commit_push(
    repo_path: str, files: list[str], commit_message: str, repo_slug: str
) -> None:
    """
    Stage exactly the discovered files/folders, create the initial commit,
    and push to GitHub.
    Uses 'git push -u origin main' to set the upstream tracking branch
    so subsequent 'git push' calls work without arguments.

    The push step is handled separately from add/commit (instead of going
    through the generic run() helper) because it needs custom recovery:
    if GitHub denies the push for one of ALLOWED_GITHUB_USERS, that almost
    always means the auto-invite at creation time didn't take effect yet
    (or failed) — so we retry it here before giving up.
    """
    run(["git", "add", *files], cwd=repo_path)                    # Stage only the kept entries
    run(["git", "commit", "-m", commit_message], cwd=repo_path)   # Create initial commit

    info("Running: git push -u origin main")
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        success("Initial commit pushed to GitHub successfully.")
        return

    combined = (result.stdout or "") + "\n" + (result.stderr or "")

    if "denied" in combined or "Permission" in combined:
        import re
        denied_match = re.search(r"denied to (\S+?)\.", combined)
        denied_user = denied_match.group(1) if denied_match else None

        if denied_user and denied_user in ALLOWED_GITHUB_USERS and AUTO_INVITE_COLLABORATOR:
            warn(
                f"Push denied for '{denied_user}', a known account for this repo.\n"
                "  Retrying the collaborator invite before giving up..."
            )
            add_collaborator_via_gh(repo_slug, denied_user)

            retry = subprocess.run(
                ["git", "push", "-u", "origin", "main"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if retry.returncode == 0:
                success(f"Initial commit pushed successfully on retry (account: {denied_user}).")
                return

            fatal(
                f"Push still denied for '{denied_user}' after re-inviting.\n"
                f"  → {retry.stderr.strip()}\n"
                f"  Check https://github.com/{repo_slug}/invitations — '{denied_user}'\n"
                "  may need to manually accept the invitation before pushing again."
            )

    fatal(
        f"Command failed (exit {result.returncode}): git push -u origin main"
        f"\n  → {result.stderr.strip()}"
    )


def print_summary(repo_name: str) -> None:
    """
    Print a final summary with the GitHub URL of the new repo.
    Fetch the real URL from gh to account for username differences.
    """
    result = subprocess.run(
        ["gh", "repo", "view", repo_name, "--json", "url", "--jq", ".url"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and result.stdout.strip():
        repo_url = result.stdout.strip()
    else:
        repo_url = f"https://github.com/<your-username>/{repo_name}"

    print()
    print(f"{GREEN}{'─' * 60}")
    print(f"  ✅  Repository '{repo_name}' is live!")
    print(f"  🔗  {repo_url}")
    print(f"{'─' * 60}{RESET}")


# ── Argument parser ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """
    Define and parse command-line arguments.

    Positional:
        repo_name       Name of the GitHub repository to create (required)

    Optional:
        --description   Short description shown on the GitHub repo page
        --private       If set, creates a private repo (default: public)
        --exclude       Extra files/folders (on top of DEFAULT_EXCLUDES) to skip
        --message       Custom initial commit message
    """
    parser = argparse.ArgumentParser(
        description="Push every file in the current folder to a new GitHub repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from the folder you want to push — pushes everything in it
  python create_github_repo.py optimus-prompt

  # Custom description and private repo
  python create_github_repo.py my-project --description "My cool project" --private

  # Skip extra files/folders on top of the built-in defaults (.git, venv, __pycache__...)
  python create_github_repo.py my-project --exclude notes.txt drafts \
    --message "chore: initial commit"
        """
    )

    # Positional argument: repo name is always required
    parser.add_argument(
        "repo_name",
        type=str,
        help="Name of the GitHub repository to create (e.g. optimus-prompt)"
    )

    # Optional: human-readable description shown on GitHub
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Short description for the GitHub repo page (default: empty)"
    )

    # Optional flag: make the repo private instead of public
    parser.add_argument(
        "--private",
        action="store_true",           # store_true means the flag is False unless present
        default=False,
        help="Create a private repository (default: public)"
    )

    # Optional: extra files/folders to exclude on top of DEFAULT_EXCLUDES
    parser.add_argument(
        "--exclude",
        nargs="+",                     # Accept one or more space-separated names
        default=[],
        metavar="NAME",
        help="Extra files/folders (relative to current dir) to exclude from the push"
    )

    # Optional: override the initial commit message
    parser.add_argument(
        "--message",
        type=str,
        default="feat: initial commit",
        help="Initial commit message (default: 'feat: initial commit')"
    )

    return parser.parse_args()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Orchestrates the full workflow:
    1. Parse CLI arguments
    2. Run all pre-flight checks
    3. Discover files present in the current (root) folder
    4. Create remote repo on GitHub
    5. Initialise local repo in place
    6. Commit and push
    7. Print summary
    """
    args = parse_args()
    exclude_set = set(args.exclude)

    # ── Banner ────────────────────────────────────────────────────────────────
    print()
    print(f"{CYAN}{'═' * 60}")
    print("  🚀  create_github_repo.py")
    print(f"  Repo  : {args.repo_name}")
    print(f"  Desc  : {args.description or '(none)'}")
    print(f"  Vis.  : {'private' if args.private else 'public'}")
    print(f"  Dir   : {os.path.abspath('.')}")
    print(f"{'═' * 60}{RESET}")
    print()

    # ── Step 1: Pre-flight checks ─────────────────────────────────────────────
    info("Step 1/6 — Running pre-flight checks...")
    check_git_installed()                           # git must be in PATH
    check_gh_installed()                            # gh must be in PATH
    check_gh_authenticated()                        # gh must be logged in
    check_repo_name(args.repo_name)                 # Name must be GitHub-compatible
    check_repo_not_exists_remotely(args.repo_name)   # No remote collision
    # True = git init needed, False = reuse existing
    fresh_init = check_not_already_a_git_repo()

    # ── Step 2: Discover files to push ───────────────────────────────────────
    info("Step 2/6 — Discovering files in the current folder...")
    files = discover_source_files(exclude_set)

    # ── Step 3: Create remote repo on GitHub ─────────────────────────────────
    info("Step 3/6 — Creating remote GitHub repository...")
    create_remote_repo(args.repo_name, args.description, args.private)

    # ── Step 4: Initialise local repo in place ───────────────────────────────
    info("Step 4/6 — Initialising local repository (in current folder)...")
    repo_path = init_local_repo(fresh_init)

    # ── Step 5: Wire remote + commit + push ──────────────────────────────────
    info("Step 5/6 — Setting remote and pushing...")
    set_remote_origin(args.repo_name, repo_path)
    repo_slug = f"{get_authenticated_username()}/{args.repo_name}"
    stage_commit_push(repo_path, files, args.message, repo_slug)

    # ── Step 6: Done ─────────────────────────────────────────────────────────
    info("Step 6/6 — Done.")
    print_summary(args.repo_name)


# Standard Python entry-point guard:
# This block runs only when the script is executed directly (not impo
ted as a module).
if __name__ == "__main__":
    main()
rted as a module).
if __name__ == "__main__":
    main()

