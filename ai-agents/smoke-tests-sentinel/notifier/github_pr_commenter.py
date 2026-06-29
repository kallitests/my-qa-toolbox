"""SmokeSentinel — GitHub PR commenter."""

import os


def post_pr_comment(report: dict) -> bool:
    token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv("GITHUB_REPO", "")
    pr_number = os.getenv("GITHUB_PR_NUMBER", "")

    if not all([token, repo, pr_number]):
        return False

    try:
        from github import Github
        g = Github(token)
        gh_repo = g.get_repo(repo)
        pr = gh_repo.get_pull(int(pr_number))

        verdict = report.get("verdict", "UNKNOWN")
        icons = {"HEALTHY": "✅", "DEGRADED": "⚠️", "DOWN": "❌"}
        icon = icons.get(verdict, "❓")
        passed = report.get("paths_passed", 0)
        total = report.get("paths_tested", 0)
        duration = report.get("total_duration_ms", 0) / 1000

        rows = "\n".join(
            f"| {r['path_id']} | {'✅' if r['status'] == 'pass' else '❌'} "
            f"{'(healed)' if r.get('healed') else ''} | {r['duration_ms']}ms |"
            for r in report.get("results", [])
        )

        body = (
            f"## {icon} SmokeSentinel — **{verdict}**\n\n"
            f"**{passed}/{total}** critical paths · **{duration:.1f}s** total\n\n"
            f"| Path | Status | Duration |\n|---|---|---|\n{rows}\n\n"
        )

        if verdict == "DOWN":
            body += "⛔ **Merge blocked** — at least one P1 critical path is failing.\n"
        elif verdict == "DEGRADED":
            body += "⚠️ **Merge with caution** — P2 paths are failing.\n"
        else:
            body += "✅ **Merge cleared** — all critical paths operational.\n"

        pr.create_issue_comment(body)
        return True
    except Exception:
        return False
