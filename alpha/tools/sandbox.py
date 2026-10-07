"""Tool Sandbox: Execution isolation, permission checking, timeout enforcement, and resource bounding."""

import sys
import time
import uuid
import traceback
from typing import Any, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from alpha.tools.protocol import (
    BaseTool,
    ToolPermission,
    ToolResult,
    ToolMetadata,
    utc_now
)

class SandboxSecurityError(Exception):
    """Raised when a tool requests an unauthorized permission."""
    pass

class SandboxTimeoutError(Exception):
    """Raised when tool execution exceeds configured time budget."""
    pass

class ToolSandbox:
    """Execution sandbox enforcing security permissions, timeouts, and resource limits."""

    def __init__(
        self,
        default_timeout_seconds: float = 30.0,
        allowed_permissions: Optional[Set[ToolPermission]] = None,
        max_output_length: int = 500_000,
        enable_strict_permissions: bool = True
    ):
        self.default_timeout_seconds = default_timeout_seconds
        self.max_output_length = max_output_length
        self.enable_strict_permissions = enable_strict_permissions
        self.allowed_permissions: Set[ToolPermission] = allowed_permissions or set(ToolPermission)

    def grant_permission(self, permission: ToolPermission) -> None:
        self.allowed_permissions.add(permission)

    def revoke_permission(self, permission: ToolPermission) -> None:
        self.allowed_permissions.discard(permission)

    def verify_permissions(self, tool: BaseTool) -> None:
        """Verify tool permissions against sandbox security policy."""
        if not self.enable_strict_permissions:
            return
        unauthorized = [p for p in tool.permissions if p not in self.allowed_permissions]
        if unauthorized:
            raise SandboxSecurityError(
                f"Tool '{tool.name}' requires unauthorized permissions: {[p.value for p in unauthorized]}"
            )

    def execute_in_sandbox(
        self,
        tool: BaseTool,
        arguments: Dict[str, Any],
        timeout_seconds: Optional[float] = None,
        call_id: Optional[str] = None
    ) -> ToolResult:
        """Safely execute a tool within the sandbox boundaries."""
        cid = call_id or str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # 1. State check
        if not tool.enabled:
            return ToolResult(
                call_id=cid,
                tool_name=tool.name,
                success=False,
                error=f"Tool '{tool.name}' is currently disabled. Reason: {tool.disable_reason or 'No reason provided'}",
                latency_ms=0.0
            )

        # 2. Permission enforcement
        try:
            self.verify_permissions(tool)
        except SandboxSecurityError as sec_err:
            return ToolResult(
                call_id=cid,
                tool_name=tool.name,
                success=False,
                error=f"Security Policy Violation: {str(sec_err)}",
                latency_ms=(time.perf_counter() - start_time) * 1000.0
            )

        # 3. Input validation
        validation_errors = tool.validate_inputs(arguments)
        if validation_errors:
            return ToolResult(
                call_id=cid,
                tool_name=tool.name,
                success=False,
                error=f"Input Validation Failed: {'; '.join(validation_errors)}",
                latency_ms=(time.perf_counter() - start_time) * 1000.0
            )

        timeout = timeout_seconds or self.default_timeout_seconds

        # 4. Isolated Execution with Timeout
        artifacts: List[str] = []
        metadata: Dict[str, Any] = {}
        raw_output = None
        error_msg = None
        success = False

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(tool.run, **arguments)
        try:
            raw_output = future.result(timeout=timeout)
            success = True

            # If tool returns a structured dict with artifacts or metadata
            if isinstance(raw_output, dict):
                if "__artifacts__" in raw_output:
                    artifacts = raw_output.pop("__artifacts__")
                if "__metadata__" in raw_output:
                    metadata = raw_output.pop("__metadata__")

        except FutureTimeoutError:
            error_msg = f"Execution timed out after {timeout:.1f} seconds."
        except Exception as exc:
            tb = traceback.format_exc()
            error_msg = f"{type(exc).__name__}: {str(exc)}\n{tb.splitlines()[-1]}"
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # 5. Output Sanitization & Truncation
        sanitized_output = raw_output
        if isinstance(raw_output, str) and len(raw_output) > self.max_output_length:
            sanitized_output = raw_output[:self.max_output_length] + "\n[OUTPUT TRUNCATED BY SANDBOX]"
            metadata["output_truncated"] = True

        result = ToolResult(
            call_id=cid,
            tool_name=tool.name,
            success=success,
            output=sanitized_output,
            error=error_msg,
            latency_ms=elapsed_ms,
            cost_units=tool.get_metadata().estimated_cost_units,
            artifacts_produced=artifacts,
            metadata=metadata
        )

        # 6. Post-execution validation
        if success:
            out_errors = tool.validate_output(result)
            if out_errors:
                result.success = False
                result.error = f"Output Validation Failed: {'; '.join(out_errors)}"

        return result
