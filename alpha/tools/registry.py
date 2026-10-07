"""Universal Tool Registry: Manages registration, lifecycle, invocation, and validation of all Alpha tools."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from alpha.tools.protocol import (
    BaseTool,
    ToolResult,
    ToolMetadata,
    ToolCapability,
    ToolPermission
)
from alpha.tools.sandbox import ToolSandbox

logger = logging.getLogger(__name__)

class ToolValidationReport(BaseModel):
    """Validation report returned by validate_tool_result()."""
    tool_name: str
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    sanitized_output: Any = None

class ToolRegistry:
    """Standardized Tool Registry and Executor for the Alpha Operating System."""

    def __init__(self, sandbox: Optional[ToolSandbox] = None):
        self._tools: Dict[str, BaseTool] = {}
        self.sandbox = sandbox or ToolSandbox()

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool into the system."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool registration: '{tool.name}'")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool '{tool.name}' with capabilities: {[c.value for c in tool.capabilities]}")

    def get_tool(self, tool_name: str) -> BaseTool:
        """Retrieve a registered tool by name."""
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not found in ToolRegistry. Available: {list(self._tools.keys())}")
        return self._tools[tool_name]

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        return tool_name in self._tools

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_seconds: Optional[float] = None,
        call_id: Optional[str] = None
    ) -> ToolResult:
        """Execute a tool through the ToolSandbox."""
        if not self.has_tool(tool_name):
            import uuid
            return ToolResult(
                call_id=call_id or str(uuid.uuid4())[:8],
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is not registered in the ToolRegistry.",
                latency_ms=0.0
            )

        tool = self.get_tool(tool_name)
        return self.sandbox.execute_in_sandbox(
            tool=tool,
            arguments=arguments,
            timeout_seconds=timeout_seconds,
            call_id=call_id
        )

    def validate_tool_result(self, tool_name: str, result: ToolResult) -> ToolValidationReport:
        """Validate the result of a tool execution against declared rules and contracts."""
        if not self.has_tool(tool_name):
            return ToolValidationReport(
                tool_name=tool_name,
                valid=False,
                errors=[f"Unknown tool '{tool_name}' cannot be validated."]
            )

        tool = self.get_tool(tool_name)
        errors: List[str] = []
        warnings: List[str] = []

        if not result.success:
            errors.append(f"Execution marked failed: {result.error}")
        else:
            # Check validation rules declared on the tool
            out_errors = tool.validate_output(result)
            errors.extend(out_errors)

            # Check if output is empty when not expected
            if result.output is None:
                warnings.append("Tool returned None output.")

        return ToolValidationReport(
            tool_name=tool_name,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_output=result.output
        )

    def disable_tool(self, tool_name: str, reason: str = "") -> None:
        """Disable a tool from future invocations."""
        tool = self.get_tool(tool_name)
        tool.enabled = False
        tool.disable_reason = reason or "Manually disabled"
        logger.info(f"Tool '{tool_name}' has been disabled: {tool.disable_reason}")

    def enable_tool(self, tool_name: str) -> None:
        """Re-enable a previously disabled tool."""
        tool = self.get_tool(tool_name)
        tool.enabled = True
        tool.disable_reason = None
        logger.info(f"Tool '{tool_name}' has been enabled.")

    def list_tools(self, filter_enabled: bool = False) -> List[ToolMetadata]:
        """List metadata for registered tools."""
        tools = self._tools.values()
        if filter_enabled:
            tools = [t for t in tools if t.enabled]
        return [t.get_metadata() for t in tools]

    def get_all_capabilities(self) -> List[ToolCapability]:
        """Return all distinct capabilities present across registered tools."""
        caps = set()
        for t in self._tools.values():
            caps.update(t.capabilities)
        return sorted(list(caps), key=lambda x: x.value)
