"""
SmokeSentinel — Agent Nodes (story_analyzer, test_generator, executor, healer, reporter)
Each node maps to one phase of the pipeline:
  Story → Gherkin → MCP Commands → Execute → Heal → Report
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langsmith import traceable

from models.state import SmokeAIState, CriticalPath, TestResult, SmokeReport, Verdict
from mcp.playwright_mcp_client import PlaywrightMCPClient
from notifier.slack_notifier import send_slack_notification
from notifier.github_pr_commenter import post_pr_comment

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)


# ── NODE 1 — STORY ANALYZER ───────────────────────────────────

@traceable(name="story_analyzer")
def story_analyzer_node(state: SmokeAIState) -> SmokeAIState:
    """
    Reads user story or URL and identifies critical paths (max 8).
    Generates Gherkin Given/When/Then scenarios for each.
    """
    from agent.prompts.story_analyzer_prompt import STORY_ANALYZER_PROMPT

    parser = PydanticOutputParser(pydantic_object=CriticalPath)
    prompt = ChatPromptTemplate.from_template(STORY_ANALYZER_PROMPT)

    input_text = state.get("input_story") or f"URL: {state.get('input_url')}"

    chain = prompt | llm
    raw = chain.invoke({
        "input": input_text,
        "env": state.get("env", "staging"),
        "format_instructions": parser.get_format_instructions(),
    }).content

    # Parse JSON array of critical paths
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        paths_raw = json.loads(clean)
        scenarios = paths_raw if isinstance(paths_raw, list) else [paths_raw]
    except Exception:
        # Fallback: minimal smoke scenario
        scenarios = [{
            "id": "CP-01",
            "title": "Page loads",
            "priority": "P1",
            "gherkin": f"Given I open {state.get('input_url', 'the app')}\nThen the page loads successfully",
            "max_duration_ms": 30000,
        }]

    return {**state, "gherkin_scenarios": scenarios[:8]}  # Max 8 smoke scenarios


# ── NODE 2 — TEST GENERATOR ───────────────────────────────────

@traceable(name="test_generator")
def test_generator_node(state: SmokeAIState) -> SmokeAIState:
    """
    Translates each Gherkin scenario into Playwright MCP command sequences.
    No TypeScript files generated — pure MCP command JSON.
    """
    from agent.prompts.test_generator_prompt import TEST_GENERATOR_PROMPT

    prompt = ChatPromptTemplate.from_template(TEST_GENERATOR_PROMPT)
    chain = prompt | llm

    all_commands = []
    for scenario in state["gherkin_scenarios"]:
        raw = chain.invoke({
            "scenario_id": scenario["id"],
            "gherkin": scenario["gherkin"],
            "url": state.get("input_url", ""),
            "env": state.get("env", "staging"),
        }).content

        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            commands = json.loads(clean)
            all_commands.append({
                "path_id": scenario["id"],
                "priority": scenario.get("priority", "P1"),
                "commands": commands if isinstance(commands, list) else [commands],
            })
        except Exception:
            pass

    return {**state, "mcp_commands": all_commands}


# ── NODE 3 — EXECUTOR ─────────────────────────────────────────

@traceable(name="executor")
def executor_node(state: SmokeAIState) -> SmokeAIState:
    """
    Executes MCP command sequences against the Playwright MCP server.
    Enforces 30s per test and 4m30s global stopwatch.
    """
    mcp = PlaywrightMCPClient()
    results = []
    global_start = time.monotonic()
    MAX_GLOBAL_MS = 270_000  # 4m30s — leaves 30s for reporter

    for test in state["mcp_commands"]:
        path_id = test["path_id"]
        commands = test["commands"]

        # Global timeout check
        elapsed_ms = int((time.monotonic() - global_start) * 1000)
        if elapsed_ms > MAX_GLOBAL_MS:
            results.append(TestResult(
                path_id=path_id,
                status="skip",
                duration_ms=0,
                error_message="Global smoke timeout exceeded (4m30s)",
            ).model_dump())
            continue

        test_start = time.monotonic()
        failed = False
        error_msg = None
        screenshot_path = None
        commands_executed = 0

        for cmd in commands:
            tool = cmd.get("tool", "")
            params = cmd.get("params", {})
            timeout_ms = cmd.get("timeout_ms", 10000)

            result = mcp.call(tool, params, timeout_ms)
            commands_executed += 1

            if not result["success"]:
                failed = True
                error_msg = result.get("error", "Unknown error")
                # Screenshot on failure
                sc_path = f"reports/screenshots/{path_id}_{int(time.monotonic())}.png"
                Path(sc_path).parent.mkdir(parents=True, exist_ok=True)
                mcp.screenshot(sc_path)
                screenshot_path = sc_path
                break

        duration_ms = int((time.monotonic() - test_start) * 1000)

        # Enforce 30s per test
        if duration_ms > 30_000:
            results.append(TestResult(
                path_id=path_id,
                status="timeout",
                duration_ms=duration_ms,
                error_message=f"Test exceeded 30s limit ({duration_ms}ms)",
                mcp_commands_executed=commands_executed,
            ).model_dump())
            continue

        results.append(TestResult(
            path_id=path_id,
            status="fail" if failed else "pass",
            duration_ms=duration_ms,
            error_message=error_msg,
            screenshot_path=screenshot_path,
            mcp_commands_executed=commands_executed,
        ).model_dump())

    total_ms = int((time.monotonic() - global_start) * 1000)
    return {**state, "execution_results": results, "total_duration_ms": total_ms}


# ── NODE 4 — HEALER ───────────────────────────────────────────

@traceable(name="healer")
def healer_node(state: SmokeAIState) -> SmokeAIState:
    """
    For failed tests: inspects accessibility tree and proposes a healed command.
    Max 1 healing attempt per run — never loops.
    """
    from agent.prompts.healer_prompt import HEALER_PROMPT

    mcp = PlaywrightMCPClient()
    prompt = ChatPromptTemplate.from_template(HEALER_PROMPT)
    chain = prompt | llm

    updated_results = []
    for result in state["execution_results"]:
        if result["status"] not in ("fail",):
            updated_results.append(result)
            continue

        # Get current accessibility tree
        tree_result = mcp.get_accessibility_tree()
        accessibility_tree = tree_result.get("result", {}) if tree_result["success"] else {}

        # Ask LLM to diagnose and propose a fix
        raw = chain.invoke({
            "path_id": result["path_id"],
            "error_message": result.get("error_message", ""),
            "accessibility_tree": json.dumps(accessibility_tree)[:3000],
        }).content

        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            diagnosis = json.loads(clean)
            failure_type = diagnosis.get("failure_type", "real_bug")
            healed_command = diagnosis.get("healed_command")
        except Exception:
            failure_type = "real_bug"
            healed_command = None

        # Attempt heal if broken_selector and healed command provided
        if failure_type == "broken_selector" and healed_command:
            heal_result = mcp.call(
                healed_command.get("tool", ""),
                healed_command.get("params", {}),
            )
            if heal_result["success"]:
                result["status"] = "pass"
                result["healed"] = True
                result["failure_type"] = failure_type
                result["error_message"] = f"Healed: {result['error_message']}"
            else:
                result["failure_type"] = failure_type
        else:
            result["failure_type"] = failure_type

        updated_results.append(result)

    return {**state, "execution_results": updated_results, "heal_attempted": True}


# ── NODE 5 — REPORTER ─────────────────────────────────────────

@traceable(name="reporter")
def reporter_node(state: SmokeAIState) -> SmokeAIState:
    """
    Computes verdict, builds report (JSON + HTML), sends notifications.
    HEALTHY / DEGRADED / DOWN based on P1/P2 failure rules.
    """
    results = state["execution_results"]
    scenarios = {s["id"]: s for s in state["gherkin_scenarios"]}

    # Compute verdict
    p1_failures = [
        r for r in results
        if r["status"] in ("fail", "timeout")
        and scenarios.get(r["path_id"], {}).get("priority") == "P1"
    ]
    p2_failures = [
        r for r in results
        if r["status"] in ("fail", "timeout")
        and scenarios.get(r["path_id"], {}).get("priority") == "P2"
    ]

    if p1_failures:
        verdict = Verdict.DOWN
    elif p2_failures:
        verdict = Verdict.DEGRADED
    else:
        verdict = Verdict.HEALTHY

    passed = sum(1 for r in results if r["status"] == "pass")

    report = SmokeReport(
        run_id=str(uuid.uuid4())[:8],
        timestamp=datetime.utcnow().isoformat(),
        input=state.get("input_story") or state.get("input_url", ""),
        env=state.get("env", "staging"),
        verdict=verdict,
        total_duration_ms=state.get("total_duration_ms", 0),
        paths_tested=len(results),
        paths_passed=passed,
        paths_failed=len(results) - passed,
        results=[TestResult(**r) for r in results],
        notification_sent=False,
    ).model_dump()

    # Send Slack notification
    notified = send_slack_notification(report)
    report["notification_sent"] = notified

    # Post PR comment if in CI context
    post_pr_comment(report)

    return {**state, "verdict": verdict.value, "report": report}
