"""Tests for Universal Tool Interface, ToolRegistry, ToolSandbox, and ToolDiscovery."""

import pytest
import time
from typing import Any, Dict
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolPermission,
    ToolParameter,
    ValidationRule,
    ToolResult
)
from alpha.tools.registry import ToolRegistry
from alpha.tools.sandbox import ToolSandbox, SandboxSecurityError
from alpha.tools.discovery import ToolCapabilityGraph, ToolSemanticVector

class EchoTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="test_echo",
            description="Echoes back input message with uppercase transformation.",
            capabilities=[ToolCapability.ANALYTICS],
            permissions=[ToolPermission.ANALYTICS],
            parameters={
                "message": ToolParameter(name="message", type="string", description="Text to echo", required=True)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="message", error_message="message cannot be empty")
            ]
        )

    def run(self, message: str) -> str:
        return message.upper()

class SlowTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="test_slow",
            description="Simulates a slow tool.",
            capabilities=[ToolCapability.ANALYTICS],
            permissions=[ToolPermission.ANALYTICS],
            parameters={"sleep_s": ToolParameter(name="sleep_s", type="float", description="Seconds to sleep", required=True)}
        )

    def run(self, sleep_s: float) -> str:
        time.sleep(sleep_s)
        return "done"

class PrivilegedTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="test_privileged",
            description="Requires system permission.",
            capabilities=[ToolCapability.CODE_EXECUTION],
            permissions=[ToolPermission.SYSTEM]
        )

    def run(self) -> str:
        return "unlocked"

def test_tool_registry_lifecycle():
    registry = ToolRegistry()
    tool = EchoTool()
    registry.register_tool(tool)

    assert registry.has_tool("test_echo")
    assert registry.get_tool("test_echo").name == "test_echo"

    # Execution
    res = registry.execute_tool("test_echo", {"message": "hello world"})
    assert res.success is True
    assert res.output == "HELLO WORLD"

    # Validation
    val_report = registry.validate_tool_result("test_echo", res)
    assert val_report.valid is True

    # Disable / Enable
    registry.disable_tool("test_echo", "maintenance")
    assert tool.enabled is False
    res_disabled = registry.execute_tool("test_echo", {"message": "hello"})
    assert res_disabled.success is False
    assert "disabled" in res_disabled.error.lower()

    registry.enable_tool("test_echo")
    assert tool.enabled is True
    res_enabled = registry.execute_tool("test_echo", {"message": "hello"})
    assert res_enabled.success is True

def test_sandbox_security_enforcement():
    sandbox = ToolSandbox(allowed_permissions={ToolPermission.ANALYTICS})
    registry = ToolRegistry(sandbox=sandbox)
    registry.register_tool(PrivilegedTool())

    res = registry.execute_tool("test_privileged", {})
    assert res.success is False
    assert "Security Policy Violation" in res.error

def test_sandbox_timeout_handling():
    sandbox = ToolSandbox(default_timeout_seconds=0.2)
    registry = ToolRegistry(sandbox=sandbox)
    registry.register_tool(SlowTool())

    res = registry.execute_tool("test_slow", {"sleep_s": 1.0})
    assert res.success is False
    assert "timed out" in res.error.lower()

def test_sandbox_input_validation():
    registry = ToolRegistry()
    registry.register_tool(EchoTool())

    # Missing required argument
    res_missing = registry.execute_tool("test_echo", {})
    assert res_missing.success is False
    assert "Missing required parameter" in res_missing.error

    # Empty validation rule triggered
    res_empty = registry.execute_tool("test_echo", {"message": ""})
    assert res_empty.success is False
    assert "cannot be empty" in res_empty.error

def test_tool_discovery_and_embeddings():
    registry = ToolRegistry()
    echo = EchoTool()
    registry.register_tool(echo)
    graph = ToolCapabilityGraph(registry)

    # Capability lookup
    tools = graph.get_tools_by_capability(ToolCapability.ANALYTICS)
    assert len(tools) == 1
    assert tools[0].name == "test_echo"

    # Semantic intent search
    discovered = graph.discover_tools("uppercase echo text", top_k=1)
    assert len(discovered) == 1
    assert discovered[0].tool_name == "test_echo"
    assert discovered[0].relevance_score > 0.0

    # Explanation
    info = graph.explain_tool("test_echo")
    assert info["name"] == "test_echo"
    assert "why_it_exists" in info
    assert "when_to_use" in info
