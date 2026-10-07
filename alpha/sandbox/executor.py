"""Secure Execution Sandbox: Coordinates multi-language execution, enforces limits, and tracks artifacts."""

import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from alpha.sandbox.runners import (
    CodeExecutionResult,
    PythonRunner,
    NodeRunner,
    RustRunner,
    ShellRunner
)

class SecureExecutionSandbox:
    """Multi-language execution sandbox with resource bounds and artifact tracking."""

    def __init__(self, sandbox_dir: Optional[str] = None, default_timeout: float = 15.0):
        self.sandbox_dir = Path(sandbox_dir).resolve() if sandbox_dir else Path(tempfile.gettempdir()) / "alpha_sandbox"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.default_timeout = default_timeout

        self.python_runner = PythonRunner(working_dir=str(self.sandbox_dir))
        self.node_runner = NodeRunner(working_dir=str(self.sandbox_dir))
        self.rust_runner = RustRunner(working_dir=str(self.sandbox_dir))
        self.shell_runner = ShellRunner(working_dir=str(self.sandbox_dir))

    def run_code(self, language: str, code: str, timeout_seconds: Optional[float] = None) -> CodeExecutionResult:
        lang = language.lower().strip()
        timeout = timeout_seconds or self.default_timeout

        if lang in ("python", "py"):
            return self.python_runner.execute(code, timeout_seconds=timeout)
        elif lang in ("node", "nodejs", "javascript", "js"):
            return self.node_runner.execute(code, timeout_seconds=timeout)
        elif lang in ("rust", "rs"):
            return self.rust_runner.execute(code, timeout_seconds=timeout)
        else:
            raise ValueError(f"Unsupported sandbox language: '{language}'. Supported: python, nodejs, rust.")

    def run_shell(self, command: str, timeout_seconds: Optional[float] = None) -> CodeExecutionResult:
        timeout = timeout_seconds or self.default_timeout
        return self.shell_runner.execute(command, timeout_seconds=timeout)
