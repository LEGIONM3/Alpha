"""Unit tests for Component 3: Planner."""

import pytest
from alpha.decomposer.decomposer import TaskDecomposer
from alpha.planner.planner import Planner
from alpha.core.types import ComplexityScore

@pytest.fixture
def planner_setup():
    decomposer = TaskDecomposer()
    planner = Planner()
    return decomposer, planner

def test_plan_generation_from_tree(planner_setup):
    decomposer, planner = planner_setup
    tree = decomposer.decompose("Deploy container service to production")
    plan = planner.create_plan_from_tree(tree)

    assert len(plan.steps) >= 3
    assert plan.total_estimated_tokens > 0
    assert plan.total_estimated_time_s > 0

    step_nums = [s.step_number for s in plan.steps]
    assert step_nums == list(range(1, len(plan.steps) + 1))

def test_resource_estimation_and_validation_contracts(planner_setup):
    decomposer, planner = planner_setup
    tree = decomposer.decompose("Configure cache")
    plan = planner.create_plan_from_tree(tree)

    for step in plan.steps:
        assert step.resources.estimated_input_tokens >= 150
        assert step.resources.timeout_seconds > 0
        assert len(step.validation_contracts) >= 1
        # Check that non-empty rule is present
        assert any("len(output.strip()) > 0" in vc.rule for vc in step.validation_contracts)
