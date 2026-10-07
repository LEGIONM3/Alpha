"""Unit tests for Component 2: Task Decomposer."""

import pytest
from alpha.core.types import TaskLevel, TaskStatus
from alpha.decomposer.decomposer import TaskDecomposer

@pytest.fixture
def decomposer():
    return TaskDecomposer(max_depth=3, max_retries=3)

def test_heuristic_decomposition_hierarchy(decomposer):
    tree = decomposer.decompose(
        goal_description="Create a secure user authentication system",
        goal_name="User Auth System"
    )

    root = tree.get_root()
    assert root is not None
    assert root.level == TaskLevel.GOAL

    # Check children levels
    subgoals = tree.get_children(root.id)
    assert len(subgoals) >= 3
    for sg in subgoals:
        assert sg.level == TaskLevel.SUB_GOAL

    atomic_actions = tree.get_atomic_actions()
    assert len(atomic_actions) >= 3
    for act in atomic_actions:
        assert act.level == TaskLevel.ATOMIC_ACTION

def test_dag_dependencies_and_topological_sort(decomposer):
    tree = decomposer.decompose("Build pipeline")
    atomic_actions = tree.get_atomic_actions()
    order = tree.topological_order()

    assert len(order) == len(atomic_actions)
    
    # Check that dependencies precede dependents
    executed_ids = set()
    for node in order:
        for dep in node.dependencies:
            assert dep in executed_ids, f"Dependency {dep} was not executed before {node.id}"
        executed_ids.add(node.id)

def test_retry_tracking(decomposer):
    tree = decomposer.decompose("Test retry")
    node = tree.get_atomic_actions()[0]

    assert node.retry_count == 0
    can_retry1 = decomposer.record_retry(node, "Temporary network timeout")
    assert can_retry1 is True
    assert node.retry_count == 1
    assert node.status == TaskStatus.READY

    can_retry2 = decomposer.record_retry(node, "Timeout 2")
    can_retry3 = decomposer.record_retry(node, "Timeout 3")
    can_retry4 = decomposer.record_retry(node, "Timeout 4")

    assert can_retry4 is False
    assert node.status == TaskStatus.FAILED
