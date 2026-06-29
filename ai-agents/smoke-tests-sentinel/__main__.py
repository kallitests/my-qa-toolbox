"""
SmokeSentinel — CLI Entry Point

Usage:
  python -m smokesentinel --env staging --story "As a doctor I want to log in"
  python -m smokesentinel --env production --url https://app.medtech.com
  python -m smokesentinel --env staging  # uses TARGET_URL from .env
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="smokesentinel",
        description="SmokeSentinel — AI smoke tests < 5 min via Playwright MCP",
    )
    parser.add_argument("--story", type=str, default="", help="User story in natural language")
    parser.add_argument("--url", type=str, default="", help="Target URL to smoke test")
    parser.add_argument("--env", type=str, default="staging", choices=["staging", "production"])
    parser.add_argument("--output", type=str, default="", help="Output JSON report path")
    parser.add_argument("--json", action="store_true", help="Output full JSON to stdout")

    args = parser.parse_args()

    # Resolve input
    story = args.story or os.getenv("SMOKE_STORY", "")
    url = args.url or os.getenv("TARGET_URL", "")

    if not story and not url:
        print("❌ Provide --story or --url (or set TARGET_URL in .env)")
        sys.exit(2)

    print(f"\n🔥 SmokeSentinel v2.0 — {args.env.upper()}\n")
    if story:
        print(f"  Story : {story[:80]}{'...' if len(story) > 80 else ''}")
    if url:
        print(f"  URL   : {url}")
    print(f"  Env   : {args.env}")
    print()

    # Import here to avoid slow startup when just showing help
    from agent.sentinel import run

    try:
        result = run(story=story, url=url, env=args.env)
    except Exception as e:
        print(f"❌ SmokeSentinel failed: {e}")
        sys.exit(2)

    verdict = result.get("verdict", "UNKNOWN")
    report = result.get("report", {})

    # Write report
    output_path = args.output or f"reports/smoke_{args.env}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(report, indent=2, ensure_ascii=False))

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_summary(verdict, report)

    # Exit codes: 0=HEALTHY, 1=DEGRADED, 2=DOWN
    codes = {"HEALTHY": 0, "DEGRADED": 1, "DOWN": 2}
    sys.exit(codes.get(verdict, 2))


def _print_summary(verdict: str, report: dict) -> None:
    icons = {"HEALTHY": "✅", "DEGRADED": "⚠️", "DOWN": "❌"}
    icon = icons.get(verdict, "❓")
    passed = report.get("paths_passed", 0)
    total = report.get("paths_tested", 0)
    duration = report.get("total_duration_ms", 0) / 1000

    print(f"{icon}  Verdict  : {verdict}")
    print(f"   Paths    : {passed}/{total} critical paths")
    print(f"   Duration : {duration:.1f}s")
    print()

    for r in report.get("results", []):
        status_icon = "✅" if r["status"] == "pass" else "❌"
        healed = " (healed)" if r.get("healed") else ""
        print(f"   {status_icon} {r['path_id']} — {r['status'].upper()}{healed} ({r['duration_ms']}ms)")

    print()


if __name__ == "__main__":
    main()
