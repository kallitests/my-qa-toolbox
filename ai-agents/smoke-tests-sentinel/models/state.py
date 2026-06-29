"""
SmokeSentinel — Models & LangGraph State
"""

from typing import Optional, TypedDict
from pydantic import BaseModel, Field
from enum import Enum


# ── LangGraph State ───────────────────────────────────────────

class SmokeAIState(TypedDict):
    # ── Input ─────────────────────────────────────────────────
    input_story: str
    input_url: str
    env: str

    # ── Coordinator (Atto equivalent) ─────────────────────────
    coordinator_decision: Optional[dict]   # full CoordinatorDecision dict
    trigger_type: Optional[str]            # pull_request | push_main | scheduled_cron | manual
    risk_level: Optional[str]              # critical | elevated | normal | low
    coverage_mode: Optional[str]           # full | targeted | minimal
    max_paths: Optional[int]              # max smoke paths for this run (1-8)
    timeout_budget_ms: Optional[int]      # total executor budget in ms
    healing_enabled: Optional[bool]       # whether healer node should run
    focus_hint: Optional[str]             # optional hint for story_analyzer
    coordinator_reasoning: Optional[str]  # why these decisions were made

    # ── Pipeline ──────────────────────────────────────────────
    gherkin_scenarios: list[dict]
    mcp_commands: list[dict]
    execution_results: list[dict]
    heal_attempted: bool
    verdict: Optional[str]
    total_duration_ms: int
    report: Optional[dict]
    notification_sent: bool


# ── Domain Models ─────────────────────────────────────────────

class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"


class CriticalPath(BaseModel):
    id: str = Field(description="CP-01, CP-02, ...")
    title: str = Field(description="Short description of the critical path")
    priority: Priority
    gherkin: str = Field(description="Full Given/When/Then scenario")
    max_duration_ms: int = Field(default=30000, description="30s max per smoke test")


class MCPCommand(BaseModel):
    tool: str = Field(description="playwright_navigate | playwright_click | playwright_fill | playwright_expect_visible | playwright_screenshot")
    params: dict
    expected_result: Optional[str] = None
    timeout_ms: int = Field(default=10000)


class FailureType(str, Enum):
    REAL_BUG = "real_bug"
    BROKEN_SELECTOR = "broken_selector"
    NETWORK_TIMEOUT = "network_timeout"
    ENV_INSTABILITY = "env_instability"


class TestResult(BaseModel):
    path_id: str
    status: str = Field(description="pass | fail | timeout | skip")
    duration_ms: int
    failure_type: Optional[FailureType] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    healed: bool = False
    mcp_commands_executed: int = 0


class Verdict(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class SmokeReport(BaseModel):
    run_id: str
    timestamp: str
    input: str
    env: str
    verdict: Verdict
    total_duration_ms: int
    paths_tested: int
    paths_passed: int
    paths_failed: int
    results: list[TestResult]
    notification_sent: bool
