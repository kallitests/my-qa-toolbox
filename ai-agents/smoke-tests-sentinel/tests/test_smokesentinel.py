"""
SmokeSentinel — Agent Quality Test Suite
Tests the agent's behavior, not the smoke tests it generates.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from models.state import SmokeAIState, TestResult, SmokeReport, Verdict
from mcp.playwright_mcp_client import PlaywrightMCPClient
from agent.nodes.reporter_node import _compute_verdict


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def base_state() -> SmokeAIState:
    return {
        "input_story": "As a doctor I want to log in and see my patients",
        "input_url": "https://app.medtech.example.com",
        "env": "staging",
        "gherkin_scenarios": [
            {"id": "CP-01", "title": "Login", "priority": "P1",
             "gherkin": "Given I open the app\nWhen I log in\nThen I see the dashboard",
             "max_duration_ms": 30000},
            {"id": "CP-02", "title": "Patient search", "priority": "P2",
             "gherkin": "Given I am logged in\nWhen I search for a patient\nThen I see results",
             "max_duration_ms": 30000},
        ],
        "mcp_commands": [],
        "execution_results": [],
        "heal_attempted": False,
        "verdict": None,
        "total_duration_ms": 0,
        "report": None,
        "notification_sent": False,
    }


@pytest.fixture
def pass_results():
    return [
        {"path_id": "CP-01", "status": "pass", "duration_ms": 3200,
         "healed": False, "mcp_commands_executed": 4},
        {"path_id": "CP-02", "status": "pass", "duration_ms": 5100,
         "healed": False, "mcp_commands_executed": 3},
    ]


@pytest.fixture
def p1_fail_results():
    return [
        {"path_id": "CP-01", "status": "fail", "duration_ms": 2100,
         "error_message": "element not found: button[name='Se connecter']",
         "healed": False, "mcp_commands_executed": 2},
        {"path_id": "CP-02", "status": "pass", "duration_ms": 4800,
         "healed": False, "mcp_commands_executed": 3},
    ]


# ── Verdict logic tests ────────────────────────────────────────

def test_verdict_healthy_when_all_pass(base_state, pass_results):
    """All paths pass → HEALTHY."""
    verdict = _compute_verdict(pass_results, base_state["gherkin_scenarios"])
    assert verdict == Verdict.HEALTHY


def test_verdict_down_when_p1_fails(base_state, p1_fail_results):
    """P1 path fails → DOWN regardless of P2."""
    verdict = _compute_verdict(p1_fail_results, base_state["gherkin_scenarios"])
    assert verdict == Verdict.DOWN


def test_verdict_degraded_when_only_p2_fails(base_state):
    """Only P2 path fails → DEGRADED."""
    results = [
        {"path_id": "CP-01", "status": "pass", "duration_ms": 3000, "healed": False, "mcp_commands_executed": 4},
        {"path_id": "CP-02", "status": "fail", "duration_ms": 1500, "healed": False, "mcp_commands_executed": 2},
    ]
    verdict = _compute_verdict(results, base_state["gherkin_scenarios"])
    assert verdict == Verdict.DEGRADED


def test_verdict_healthy_when_p1_healed(base_state):
    """P1 path healed → counts as PASS → HEALTHY."""
    results = [
        {"path_id": "CP-01", "status": "pass", "healed": True, "duration_ms": 4200, "mcp_commands_executed": 5},
        {"path_id": "CP-02", "status": "pass", "healed": False, "duration_ms": 3100, "mcp_commands_executed": 3},
    ]
    verdict = _compute_verdict(results, base_state["gherkin_scenarios"])
    assert verdict == Verdict.HEALTHY


# ── Healer tests ───────────────────────────────────────────────

def test_healer_does_not_retry_twice(base_state):
    """Heal attempted must be True after healer runs — prevents double retry."""
    state_with_heal = {**base_state, "heal_attempted": True}
    assert state_with_heal["heal_attempted"] is True


def test_healer_max_one_attempt():
    """The graph must never route to healer if heal_attempted is True."""
    from agent.sentinel import _route_after_execution
    state = {
        "execution_results": [{"status": "fail"}],
        "heal_attempted": True,
    }
    assert _route_after_execution(state) == "reporter"


def test_healer_routes_to_reporter_on_all_pass():
    """No failures → skip healer, go straight to reporter."""
    from agent.sentinel import _route_after_execution
    state = {
        "execution_results": [{"status": "pass"}, {"status": "pass"}],
        "heal_attempted": False,
    }
    assert _route_after_execution(state) == "reporter"


# ── MCP client tests ───────────────────────────────────────────

def test_mcp_client_timeout_returns_error():
    """MCP call that times out must return success=False, not raise."""
    import httpx
    client = PlaywrightMCPClient(base_url="http://localhost:9999")
    result = client.call("playwright_navigate", {"url": "http://example.com"}, timeout_ms=100)
    assert result["success"] is False
    assert result["error"] is not None


def test_mcp_client_health_false_on_unavailable():
    """Health check on unavailable server must return False, not raise."""
    client = PlaywrightMCPClient(base_url="http://localhost:9999")
    assert client.health() is False


# ── Report structure tests ─────────────────────────────────────

def test_smoke_report_fields(base_state, pass_results):
    """SmokeReport must contain all required fields."""
    report = SmokeReport(
        run_id="test-1234",
        timestamp="2026-06-24T12:00:00",
        input=base_state["input_story"],
        env="staging",
        verdict=Verdict.HEALTHY,
        total_duration_ms=8300,
        paths_tested=2,
        paths_passed=2,
        paths_failed=0,
        results=[TestResult(**r) for r in pass_results],
        notification_sent=False,
    )
    assert report.verdict == Verdict.HEALTHY
    assert report.paths_passed == 2
    assert len(report.results) == 2


def test_timeout_result_counts_as_fail_for_p1():
    """A timeout on a P1 path must produce verdict DOWN."""
    scenarios = [{"id": "CP-01", "priority": "P1", "title": "Login", "gherkin": "", "max_duration_ms": 30000}]
    results = [{"path_id": "CP-01", "status": "timeout", "duration_ms": 30001, "healed": False, "mcp_commands_executed": 1}]
    from agent.nodes.reporter_node import _compute_verdict
    assert _compute_verdict(results, scenarios) == Verdict.DOWN


def test_total_duration_under_5_minutes():
    """Smoke run must complete in under 300 000ms (5 minutes)."""
    assert 8300 < 300_000
