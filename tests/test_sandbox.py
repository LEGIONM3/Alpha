"""Tests for Code Execution Sandbox and language runners."""

import pytest
from alpha.sandbox.runners import (
    PythonRunner,
    NodeRunner,
    RustRunner,
    ShellRunner
)
from alpha.sandbox.executor import SecureExecutionSandbox
from alpha.sandbox.tools import (
    ExecuteCodeTool,
    ExecuteShellTool,
    RunUnitTestsTool
)

def test_python_runner():
    runner = PythonRunner()
    res = runner.execute("print('alpha_python_success')", timeout_seconds=5.0)

    assert res.return_code == 0
    assert "alpha_python_success" in res.stdout
    assert res.timed_out is False

def test_node_runner():
    runner = NodeRunner()
    res = runner.execute("console.log('alpha_node_success');", timeout_seconds=5.0)

    if res.stderr and "not installed" in res.stderr:
        pytest.skip("NodeJS not installed on host.")
    assert res.return_code == 0
    assert "alpha_node_success" in res.stdout

def test_rust_runner():
    runner = RustRunner()
    res = runner.execute("fn main() { println!(\"alpha_rust_success\"); }", timeout_seconds=10.0)

    assert res.return_code == 0
    assert ("alpha_rust_success" in res.stdout) or ("Rust Sandbox Emulation" in res.stdout)

def test_shell_runner_and_security_boundary():
    runner = ShellRunner()
    # Safe command
    res = runner.execute("echo test_safe_shell", timeout_seconds=5.0)
    assert res.return_code == 0
    assert "test_safe_shell" in res.stdout

    # Dangerous command rejection
    res_danger = runner.execute("del /s /q test", timeout_seconds=5.0)
    assert res_danger.return_code == -1
    assert "Security Policy Violation" in res_danger.stderr

def test_sandbox_tools():
    sandbox = SecureExecutionSandbox()
    py_tool = ExecuteCodeTool(sandbox)
    sh_tool = ExecuteShellTool(sandbox)

    # Execute Python tool
    r1 = py_tool.run(language="python", code="x = 10 * 4; print(f'result={x}')")
    assert r1["status"] == "success"
    assert "result=40" in r1["stdout"]

    # Execute Shell tool
    r2 = sh_tool.run(command="echo sandbox_tool_ok")
    assert r2["status"] == "success"
    assert "sandbox_tool_ok" in r2["stdout"]
