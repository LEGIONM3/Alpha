"""Tests for Execution Graph, Context, Tool Invocation Engine, and Failure Recovery."""

import pytest
import time
from typing import Any, Dict
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolPermission,
    ToolParameter
)
from alpha.tools.registry import ToolRegistry
from alpha.execution.graph import ExecutionGraph, ExecutionNode, NodeStatus
from alpha.execution.context import ExecutionContext
from alpha.execution.engine import ToolInvocationEngine
from alpha.execution.recovery import (
    RecoverySystem,
    FailureDetector,
    FailureMode
)

class AddTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="math_add",
            description="Adds two integers.",
            capabilities=[ToolCapability.ANALYTICS],
            permissions=[ToolPermission.ANALYTICS],
            parameters={
                "a": ToolParameter(name="a", type="integer", description="First number"),
                "b": ToolParameter(name="b", type="integer", description="Second number")
            }
        )

    def run(self, a: Any, b: Any) -> int:
        return int(a) + int(b)

class FlakyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="flaky_service",
            description="Fails on first invocation, succeeds on second.",
            capabilities=[ToolCapability.API],
            permissions=[ToolPermission.API]
        )
        self.call_count = 0

    def run(self) -> str:
        self.call_count += 1
        if self.call_count == 1:
            raise RuntimeError("Temporary internal error 500")
        return "success_recovered"

class FallbackTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="fallback_backup",
            description="Fallback service.",
            capabilities=[ToolCapability.API],
            permissions=[ToolPermission.API]
        )

    def run(self) -> str:
        return "fallback_result"

class FailingTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="always_fail",
            description="Always raises exception.",
            capabilities=[ToolCapability.API],
            permissions=[ToolPermission.API]
        )

    def run(self) -> str:
        raise RuntimeError("Fatal failure")

def test_dag_cycle_detection():
    graph = ExecutionGraph()
    graph.add_node(ExecutionNode(node_id="A", tool_name="math_add"))
    graph.add_node(ExecutionNode(node_id="B", tool_name="math_add", depends_on=["A"]))
    graph.add_node(ExecutionNode(node_id="C", tool_name="math_add", depends_on=["B"]))

    # Add cycle: A depends on C
    graph.nodes["A"].depends_on.append("C")

    with pytest.raises(ValueError, match="cyclic dependencies"):
        graph.validate_dag()

def test_execution_context_template_interpolation_and_rollback():
    ctx = ExecutionContext()
    ctx.set_variable("base_val", 10)

    from alpha.tools.protocol import ToolResult
    ctx.register_step_result("step1", ToolResult(
        call_id="c1",
        tool_name="math_add",
        success=True,
        output=42
    ))

    # Interpolate variable and step output
    interpolated = ctx.interpolate("Result is {{step1.output}} with base {{base_val}}")
    assert interpolated == "Result is 42 with base 10"

    # Exact object interpolation
    raw_obj = ctx.interpolate("{{step1.output}}")
    assert raw_obj == 42

    # Rollback stack
    reverted = []
    ctx.register_rollback("step1", "revert step 1", lambda: reverted.append("step1_reverted"))
    reports = ctx.execute_rollbacks()
    assert len(reports) == 1
    assert reports[0]["status"] == "success"
    assert reverted == ["step1_reverted"]

def test_parallel_execution_and_dependencies():
    registry = ToolRegistry()
    registry.register_tool(AddTool())
    engine = ToolInvocationEngine(registry=registry, max_workers=4)

    # Graph: (A || B) -> C
    graph = ExecutionGraph()
    graph.add_node(ExecutionNode(node_id="node_a", tool_name="math_add", arguments={"a": 5, "b": 10}))
    graph.add_node(ExecutionNode(node_id="node_b", tool_name="math_add", arguments={"a": 20, "b": 30}))
    graph.add_node(ExecutionNode(
        node_id="node_c",
        tool_name="math_add",
        arguments={"a": "{{node_a.output}}", "b": "{{node_b.output}}"},
        depends_on=["node_a", "node_b"]
    ))

    res = engine.execute_graph(graph)
    assert res.success is True
    assert res.completed_nodes == 3
    assert res.node_results["node_a"] == 15
    assert res.node_results["node_b"] == 50
    assert res.node_results["node_c"] == 65

def test_failure_recovery_retry_loop():
    registry = ToolRegistry()
    registry.register_tool(FlakyTool())
    engine = ToolInvocationEngine(registry=registry)

    graph = ExecutionGraph()
    graph.add_node(ExecutionNode(node_id="flaky_step", tool_name="flaky_service", max_retries=2))

    res = engine.execute_graph(graph)
    assert res.success is True
    assert res.completed_nodes == 1
    assert res.node_results["flaky_step"] == "success_recovered"

def test_failure_recovery_fallback_tool():
    registry = ToolRegistry()
    registry.register_tool(FailingTool())
    registry.register_tool(FallbackTool())

    engine = ToolInvocationEngine(registry=registry)
    graph = ExecutionGraph()
    graph.add_node(ExecutionNode(
        node_id="step_fail",
        tool_name="always_fail",
        fallback_tool="fallback_backup",
        max_retries=0
    ))

    res = engine.execute_graph(graph)
    assert res.success is True
    assert res.completed_nodes == 1
    assert res.node_results["step_fail"] == "fallback_result"
