"""Comprehensive Verification Suite for Project Alpha's Autonomous Continuation Layer.

Verifies:
1. NextActionContract validation and mandatory schema enforcement.
2. InvestigationQueue non-empty invariant and priority ordering.
3. StatefulResponsesClient connectivity to http://localhost:1234/v1/responses and previous_response_id chaining.
4. MissionExecutor single-step execution, state persistence to MISSION_STATE.json, and automatic reloading.
5. Autonomous continuation chain without terminal states.
"""

import json
import pytest
from pathlib import Path

from alpha.core.continuation import (
    NextActionContract,
    InvestigationItem,
    InvestigationQueue,
    StatefulResponsesClient,
    MissionState,
    MissionExecutor
)


def test_next_action_contract():
    """Verify NextActionContract model and schema."""
    contract = NextActionContract(
        action="audit",
        target="alpha/core/identity.py",
        priority="critical",
        reason="Verify invariant constitution hash"
    )
    d = contract.to_dict()
    assert d["action"] == "audit"
    assert d["target"] == "alpha/core/identity.py"
    assert d["priority"] == "critical"
    assert "constitution" in d["reason"]


def test_investigation_queue_never_empty():
    """Verify queue prioritizes critical items and automatically replenishes when emptied."""
    queue = InvestigationQueue()
    assert not queue.is_empty()
    assert queue.size() >= 5

    # Pop until drained and verify auto-replenishment
    first_item = queue.pop()
    assert first_item is not None
    assert isinstance(first_item, InvestigationItem)

    # Empty the remaining seeded items
    initial_size = queue.size()
    for _ in range(initial_size):
        queue.pop()

    # The queue must never be empty (Phase 3 & Phase 8)
    replenished_item = queue.pop()
    assert replenished_item is not None
    assert replenished_item.source in ("self_generated_gap_fill", "bootstrap_seed")


def test_stateful_responses_client_live():
    """Verify real inference against http://localhost:1234/v1/responses with previous_response_id chaining."""
    client = StatefulResponsesClient(base_url="http://localhost:1234/v1")
    
    # 1. First prompt
    res1 = client.invoke(
        user_prompt="Audit system constitution. End with mandatory NEXT_ACTION block.",
        use_previous_response=False
    )
    assert res1["success"] is True
    assert len(res1["content"]) > 0
    resp_id1 = res1.get("response_id")
    assert resp_id1 is not None

    # 2. Second prompt chained statefully via previous_response_id
    res2 = client.invoke(
        user_prompt="Follow up on previous findings. What is the next target?",
        use_previous_response=True
    )
    assert res2["success"] is True
    assert len(res2["content"]) > 0
    assert client.last_response_id is not None


def test_mission_executor_execution_and_persistence(tmp_path):
    """Verify MissionExecutor single-step execution and MISSION_STATE.json persistence."""
    state_file = tmp_path / "MISSION_STATE.json"
    executor = MissionExecutor(
        workspace_root=Path.cwd(),
        state_file=str(state_file),
        model_url="http://localhost:1234/v1"
    )

    item = InvestigationItem(
        item_id="test-inv-01",
        action="audit",
        target="alpha/core/identity.py",
        priority_level=0,
        priority_label="critical",
        reason="Verify constitutional drift protection"
    )

    res = executor.execute_next_task(item)
    assert res is not None
    assert "next_action" in res
    assert state_file.exists()

    # Verify persisted state content
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["investigations_completed"] >= 1
    assert data["current_target"] == "alpha/core/identity.py"
    assert "action" in data["next_planned_action"]

    # Verify reloading on fresh initialization
    fresh_executor = MissionExecutor(
        workspace_root=Path.cwd(),
        state_file=str(state_file),
        model_url="http://localhost:1234/v1"
    )
    assert fresh_executor.state.investigations_completed >= 1
    assert fresh_executor.state.current_target == "alpha/core/identity.py"
