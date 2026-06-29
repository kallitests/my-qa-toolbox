"""reporter_node.py — standalone for import by tests."""
from models.state import Verdict


def _compute_verdict(results: list[dict], scenarios: list[dict]) -> Verdict:
    """
    HEALTHY   : all P1 pass
    DEGRADED  : all P1 pass, at least 1 P2 fails
    DOWN      : at least 1 P1 fails or times out
    """
    priority_map = {s["id"]: s.get("priority", "P1") for s in scenarios}

    p1_failures = [
        r for r in results
        if r.get("status") in ("fail", "timeout")
        and priority_map.get(r["path_id"]) == "P1"
    ]
    p2_failures = [
        r for r in results
        if r.get("status") in ("fail", "timeout")
        and priority_map.get(r["path_id"]) == "P2"
    ]

    if p1_failures:
        return Verdict.DOWN
    if p2_failures:
        return Verdict.DEGRADED
    return Verdict.HEALTHY
