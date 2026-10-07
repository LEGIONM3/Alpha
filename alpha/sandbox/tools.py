"""Code Execution and Sandbox Tools for Alpha OS."""

import sys
from typing import Any, Dict, List, Optional
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolPermission,
    ToolParameter,
    ValidationRule
)
from alpha.sandbox.executor import SecureExecutionSandbox

class ExecuteCodeTool(BaseTool):
    def __init__(self, sandbox: Optional[SecureExecutionSandbox] = None):
        super().__init__(
            name="sandbox_execute_code",
            description="Executes code in Python, NodeJS, or Rust within an isolated sandbox environment.",
            capabilities=[ToolCapability.CODE_EXECUTION],
            permissions=[ToolPermission.EXEC_CODE],
            parameters={
                "language": ToolParameter(name="language", type="string", description="Programming language: 'python', 'nodejs', or 'rust'.", required=True, enum_values=["python", "nodejs", "rust"]),
                "code": ToolParameter(name="code", type="string", description="Source code snippet to execute.", required=True),
                "timeout_seconds": ToolParameter(name="timeout_seconds", type="float", description="Execution timeout budget in seconds.", required=False, default=15.0)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="code", error_message="Source code cannot be empty.")
            ]
        )
        self.sandbox = sandbox or SecureExecutionSandbox()

    def run(self, language: str, code: str, timeout_seconds: float = 15.0) -> Dict[str, Any]:
        res = self.sandbox.run_code(language=language, code=code, timeout_seconds=timeout_seconds)
        if res.return_code != 0:
            raise RuntimeError(
                f"Execution failed with code {res.return_code}.\n"
                f"Stdout: {res.stdout}\nStderr: {res.stderr}"
            )
        return {
            "status": "success",
            "language": res.language,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "execution_time_ms": res.execution_time_ms,
            "artifacts_created": res.artifacts_created,
            "__artifacts__": res.artifacts_created
        }


class ExecuteShellTool(BaseTool):
    def __init__(self, sandbox: Optional[SecureExecutionSandbox] = None):
        super().__init__(
            name="sandbox_execute_shell",
            description="Executes a safe shell command within a restricted subprocess sandbox.",
            capabilities=[ToolCapability.CODE_EXECUTION, ToolCapability.SYSTEM],
            permissions=[ToolPermission.EXEC_CODE, ToolPermission.SYSTEM],
            parameters={
                "command": ToolParameter(name="command", type="string", description="Shell command string to execute.", required=True),
                "timeout_seconds": ToolParameter(name="timeout_seconds", type="float", description="Execution timeout budget in seconds.", required=False, default=15.0)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="command", error_message="Shell command cannot be empty.")
            ]
        )
        self.sandbox = sandbox or SecureExecutionSandbox()

    def run(self, command: str, timeout_seconds: float = 15.0) -> Dict[str, Any]:
        res = self.sandbox.run_shell(command=command, timeout_seconds=timeout_seconds)
        if res.return_code != 0:
            raise RuntimeError(
                f"Shell command failed with code {res.return_code}.\n"
                f"Stdout: {res.stdout}\nStderr: {res.stderr}"
            )
        return {
            "status": "success",
            "command": command,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "execution_time_ms": res.execution_time_ms,
            "artifacts_created": res.artifacts_created,
            "__artifacts__": res.artifacts_created
        }


class RunUnitTestsTool(BaseTool):
    def __init__(self, sandbox: Optional[SecureExecutionSandbox] = None):
        super().__init__(
            name="sandbox_run_unit_tests",
            description="Runs unit tests (e.g. pytest) against a specified target file or directory.",
            capabilities=[ToolCapability.CODE_EXECUTION, ToolCapability.VERIFICATION],
            permissions=[ToolPermission.EXEC_CODE],
            parameters={
                "test_target": ToolParameter(name="test_target", type="string", description="Path to test file or directory.", required=True),
                "timeout_seconds": ToolParameter(name="timeout_seconds", type="float", description="Timeout in seconds.", required=False, default=30.0)
            }
        )
        self.sandbox = sandbox or SecureExecutionSandbox()

    def run(self, test_target: str, timeout_seconds: float = 30.0) -> Dict[str, Any]:
        cmd = f"{sys.executable} -m pytest {test_target} -v"
        res = self.sandbox.run_shell(command=cmd, timeout_seconds=timeout_seconds)
        passed = (res.return_code == 0)

        if not passed:
            raise AssertionError(
                f"Unit tests failed (code {res.return_code}):\n{res.stdout}\n{res.stderr}"
            )

        return {
            "status": "passed",
            "test_target": test_target,
            "stdout": res.stdout,
            "execution_time_ms": res.execution_time_ms
        }
