"""
sentinel.py — SmokeSentinel LangGraph orchestrator
Nodes: sentinel_coordinator → story_analyzer → test_generator → executor → healer → reporter

sentinel_coordinator is the Atto equivalent:
the coordinating intelligence that sets strategy before any other agent runs.
"""

from typing import Optional
from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from models.state import SmokeAIState
from agent.nodes.sentinel_coordinator import sentinel_coordinator_node
from agent.nodes.story_analyzer import story_analyzer_node
from agent.nodes.test_generator import test_generator_node
from agent.nodes.executor import executor_node
from agent.nodes.healer import healer_node
from agent.nodes.reporter import reporter_node


def _route_after_execution(state: SmokeAIState) -> str:
    """
    Route to healer if:
      - at least one failure exists
      - healing has not been attempted yet
      - healing is enabled (coordinator decision)

    Otherwise go straight to reporter.
    """
    has_failure = any(
        r.get("status") in ("fail", "timeout")
        for r in state.get("execution_results", [])
    )
    healing_enabled = state.get("healing_enabled", True)

    if has_failure and not state.get("heal_attempted") and healing_enabled:
        return "healer"
    return "reporter"


def build_graph() -> StateGraph:
    """
    SmokeSentinel v2.1 graph — 6 nodes:
      sentinel_coordinator (Atto) → story_analyzer → test_generator
      → executor → [healer?] → reporter
    """
    graph = StateGraph(SmokeAIState)

    # Register all nodes
    graph.add_node("sentinel_coordinator", sentinel_coordinator_node)
    graph.add_node("story_analyzer", story_analyzer_node)
    graph.add_node("test_generator", test_generator_node)
    graph.add_node("executor", executor_node)
    graph.add_node("healer", healer_node)
    graph.add_node("reporter", reporter_node)

    # Wire the pipeline
    # START → Atto (coordinator) first — always
    graph.add_edge(START, "sentinel_coordinator")
    graph.add_edge("sentinel_coordinator", "story_analyzer")
    graph.add_edge("story_analyzer", "test_generator")
    graph.add_edge("test_generator", "executor")

    # After execution: conditional route to healer or reporter
    # healing_enabled from coordinator controls whether healer runs
    graph.add_conditional_edges("executor", _route_after_execution)
    graph.add_edge("healer", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


@traceable(name="smokesentinel_run")
def run(story: str = "", url: str = "", env: str = "staging") -> dict:
    """
    Main entry point for SmokeSentinel.

    Args:
        story: User story in natural language
        url:   Target URL (used if story is empty)
        env:   Target environment (staging or production)

    Returns:
        Final state dict with verdict and report.
    """
    if not story and not url:
        raise ValueError("Provide either story or url.")

    initial_state: SmokeAIState = {
        # Input
        "input_story": story,
        "input_url": url,
        "env": env,

        # Coordinator fields (set by sentinel_coordinator_node)
        "coordinator_decision": None,
        "trigger_type": None,
        "risk_level": None,
        "coverage_mode": None,
        "max_paths": None,
        "timeout_budget_ms": None,
        "healing_enabled": None,
        "focus_hint": None,
        "coordinator_reasoning": None,

        # Pipeline
        "gherkin_scenarios": [],
        "mcp_commands": [],
        "execution_results": [],
        "heal_attempted": False,
        "verdict": None,
        "total_duration_ms": 0,
        "report": None,
        "notification_sent": False,
    }

    agent = build_graph()
    return agent.invoke(initial_state)
