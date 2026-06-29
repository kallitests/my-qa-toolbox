"""
SmokeSentinel — Sentinel Coordinator Node
The Atto equivalent: the coordinating intelligence above all other agents.

Responsibilities:
  - Analyze the trigger context (PR, cron, manual, sprint start)
  - Assess risk level of the change
  - Decide coverage depth (full smoke vs targeted vs minimal)
  - Set max paths, timeout budget, and healing policy for this run
  - Enrich the state before any other agent runs

This node does NOT execute tests. It sets the strategy.
Every decision it makes is logged and traceable via LangSmith.
"""

import os
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langsmith import traceable
from pydantic import BaseModel, Field
from typing import Literal, Optional

from models.state import SmokeAIState

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)


# ── Coordinator output model ───────────────────────────────────

class CoordinatorDecision(BaseModel):
    """
    The strategic decision Atto makes before any agent runs.
    Every field influences downstream agent behavior.
    """

    trigger_type: Literal[
        "pull_request",
        "push_main",
        "scheduled_cron",
        "manual",
        "sprint_start",
        "unknown",
    ] = Field(description="What triggered this smoke run")

    risk_level: Literal["critical", "elevated", "normal", "low"] = Field(
        description=(
            "Risk assessment for this run. "
            "critical = P1 paths only, fast. "
            "elevated = all paths, strict timeouts. "
            "normal = standard smoke. "
            "low = reduced set, relaxed timeouts."
        )
    )

    coverage_mode: Literal["full", "targeted", "minimal"] = Field(
        description=(
            "full = all critical paths (max 8). "
            "targeted = P1 only (max 4). "
            "minimal = single happy path check (1-2 paths)."
        )
    )

    max_paths: int = Field(
        default=8,
        ge=1,
        le=8,
        description="Maximum number of smoke paths to generate for this run",
    )

    timeout_budget_ms: int = Field(
        default=270_000,
        description=(
            "Total execution budget in ms for the executor node. "
            "Never exceed 270 000ms (4m30s) to leave room for reporter."
        ),
    )

    healing_enabled: bool = Field(
        default=True,
        description=(
            "Whether the healer node should attempt selector healing. "
            "False on production cron runs where a failure should surface immediately."
        ),
    )

    focus_hint: Optional[str] = Field(
        default=None,
        description=(
            "Optional hint for the story_analyzer about what to focus on. "
            "Example: 'Focus on authentication and patient data access flows.' "
            "Injected from PR title or Jira sprint context."
        ),
    )

    coordinator_reasoning: str = Field(
        description="One-sentence explanation of why these decisions were made"
    )


# ── Prompt ────────────────────────────────────────────────────

COORDINATOR_PROMPT = """
<role>
You are Atto, the coordinating intelligence of SmokeSentinel — a critical
smoke test agent for medtech and healthtech applications.

You are the first agent to run on every smoke test execution.
Your job is NOT to generate tests. Your job is to READ the context,
ASSESS the risk, and SET THE STRATEGY for all downstream agents.

You are the equivalent of a senior QA lead who looks at a PR in the
morning and says: "This touches the authentication service — run P1 paths
only, strict timeouts, surface failures immediately, no healing."
Or: "This is a scheduled cron on Saturday night — run full smoke,
healing enabled, relaxed budget."
</role>

<context>
Trigger context:
  - Input type     : {input_type}
  - Input content  : {input_summary}
  - Environment    : {env}
  - CI context     : {ci_context}
  - PR title       : {pr_title}
  - PR number      : {pr_number}
  - Scheduled run  : {is_scheduled}
  - Manual run     : {is_manual}
</context>

<instructions>
Based on the context above, make a strategic decision for this smoke run.

Risk assessment guide for medtech/healthtech:
  critical  → authentication, patient data access, medication flows, core API
  elevated  → any PR touching auth, data, or core clinical workflows
  normal    → feature PRs, UI changes, non-critical services
  low       → documentation PRs, config changes, scheduled off-peak runs

Coverage mode:
  full      → standard smoke, up to 8 paths
  targeted  → P1 only, max 4 paths, faster verdict
  minimal   → 1-2 paths, emergency check only

Healing policy:
  Enable healing on PR and manual runs (a broken selector should not block a valid merge).
  Disable healing on production cron runs (a failure must surface raw and unmasked).

Output ONLY valid JSON matching the schema — no prose, no markdown fences.
</instructions>

{format_instructions}
"""


# ── Node ──────────────────────────────────────────────────────

@traceable(name="sentinel_coordinator")
def sentinel_coordinator_node(state: SmokeAIState) -> SmokeAIState:
    """
    Atto equivalent — the coordinating intelligence of SmokeSentinel.

    Reads trigger context, assesses risk, sets strategy.
    Enriches state with coordinator_decision before any other agent runs.
    """
    parser = PydanticOutputParser(pydantic_object=CoordinatorDecision)
    prompt = ChatPromptTemplate.from_template(COORDINATOR_PROMPT)
    chain = prompt | llm | parser

    # Build CI context from environment variables
    pr_number = os.getenv("GITHUB_PR_NUMBER", "")
    pr_title = os.getenv("GITHUB_PR_TITLE", "")
    is_scheduled = os.getenv("GITHUB_EVENT_NAME", "") == "schedule"
    is_manual = os.getenv("GITHUB_EVENT_NAME", "") == "workflow_dispatch"
    ci_event = os.getenv("GITHUB_EVENT_NAME", "unknown")

    # Determine input type
    input_type = "user_story" if state.get("input_story") else "url"
    input_summary = (
        state.get("input_story", "")[:200]
        or f"URL: {state.get('input_url', '')}"
    )

    ci_context = (
        f"GitHub event: {ci_event}"
        + (f" | PR #{pr_number}" if pr_number else "")
        + (" | scheduled run" if is_scheduled else "")
        + (" | manual dispatch" if is_manual else "")
    )

    try:
        decision: CoordinatorDecision = chain.invoke({
            "input_type": input_type,
            "input_summary": input_summary,
            "env": state.get("env", "staging"),
            "ci_context": ci_context,
            "pr_title": pr_title or "(not provided)",
            "pr_number": pr_number or "(not a PR run)",
            "is_scheduled": str(is_scheduled),
            "is_manual": str(is_manual),
            "format_instructions": parser.get_format_instructions(),
        })
    except Exception as e:
        # Fallback: safe defaults if coordinator fails
        decision = CoordinatorDecision(
            trigger_type="unknown",
            risk_level="normal",
            coverage_mode="full",
            max_paths=8,
            timeout_budget_ms=270_000,
            healing_enabled=True,
            focus_hint=None,
            coordinator_reasoning=f"Fallback defaults applied — coordinator error: {str(e)[:100]}",
        )

    print(f"\n🧠 Sentinel Coordinator (Atto)")
    print(f"   Trigger      : {decision.trigger_type}")
    print(f"   Risk level   : {decision.risk_level.upper()}")
    print(f"   Coverage     : {decision.coverage_mode} (max {decision.max_paths} paths)")
    print(f"   Healing      : {'enabled' if decision.healing_enabled else 'DISABLED'}")
    print(f"   Budget       : {decision.timeout_budget_ms // 1000}s")
    print(f"   Reasoning    : {decision.coordinator_reasoning}\n")

    return {
        **state,
        "coordinator_decision": decision.model_dump(),
        # Propagate key decisions into top-level state for downstream nodes
        "max_paths": decision.max_paths,
        "timeout_budget_ms": decision.timeout_budget_ms,
        "healing_enabled": decision.healing_enabled,
        "focus_hint": decision.focus_hint,
        "risk_level": decision.risk_level,
        "coverage_mode": decision.coverage_mode,
        "trigger_type": decision.trigger_type,
    }
