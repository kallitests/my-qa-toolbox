"""SmokeSentinel — Slack notifier."""

import os
import httpx


def send_slack_notification(report: dict) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return False

    verdict = report.get("verdict", "UNKNOWN")
    icons = {"HEALTHY": "✅", "DEGRADED": "⚠️", "DOWN": "❌"}
    icon = icons.get(verdict, "❓")
    passed = report.get("paths_passed", 0)
    total = report.get("paths_tested", 0)
    duration = report.get("total_duration_ms", 0) / 1000
    env = report.get("env", "").upper()
    run_id = report.get("run_id", "")

    message = {
        "text": f"{icon} *SmokeSentinel — {verdict}* [{env}]",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{icon} *SmokeSentinel — {verdict}* `{env}`\n"
                        f"*{passed}/{total}* critical paths · *{duration:.1f}s* · run `{run_id}`"
                    ),
                },
            },
        ],
    }

    # Add failure details if DOWN or DEGRADED
    if verdict in ("DOWN", "DEGRADED"):
        failed = [r for r in report.get("results", []) if r["status"] not in ("pass",)]
        details = "\n".join(
            f"• {r['path_id']} — {r.get('error_message', 'Unknown error')[:80]}"
            for r in failed[:5]
        )
        message["blocks"].append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Failures:*\n{details}"},
        })

    try:
        r = httpx.post(webhook_url, json=message, timeout=5)
        return r.status_code == 200
    except Exception:
        return False
