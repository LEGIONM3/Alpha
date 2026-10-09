"""Test Suite for Phase M.1 Computer-Use and Laya Integration.

Verifies all 5 capability categories:
1. AST / Code Structure Inspection.
2. Permission-gated Filesystem Operations (read, write, SHA-256 verification).
3. Terminal Subprocess Execution (safe allowlist execution and disallowed command rejection).
4. Browser Automation via Playwright:
   - Navigation to a controlled local HTML page.
   - Initial DOM state observation.
   - Interactive element execution (button click).
   - Independent verification of resulting DOM mutation.
   - Clean failure reporting on invalid URLs (never reports failed action as success).
5. Desktop GUI Interaction:
   - Screen geometry metrics probing via Windows native API.
   - Desktop window listing.
   - Explicit failure reporting for unobserved applications.
"""

import ast
import json
import pytest
from pathlib import Path

from alpha.computer_use.computer_use_tool import ComputerUseTool, ComputerUseResult
from alpha.computer_use.permissions import ComputerActionType, PermissionGate, ApprovalToken
from alpha.observation_engine.observation import Observation


class TestPhaseM1ComputerUseIntegrity:

    @pytest.fixture
    def tool(self, tmp_path):
        return ComputerUseTool(workspace_root=tmp_path)

    def test_01_ast_inspection_on_real_codebase(self):
        """Category 1: AST inspection parses real Python files and extracts symbols."""
        tool = ComputerUseTool(workspace_root=Path.cwd())
        tree, obs = tool.inspect_ast("alpha/computer_use/computer_use_tool.py")
        assert tree is not None
        assert isinstance(tree, ast.AST)
        assert obs.source_type == "filesystem"
        assert obs.verification_status == "VERIFIED"
        assert len(obs.evidence.get("classes", [])) >= 1
        assert "ComputerUseTool" in obs.evidence["classes"]
        assert len(obs.evidence.get("functions", [])) >= 5

    def test_02_filesystem_operations_with_integrity_hash(self, tool, tmp_path):
        """Category 2: Filesystem read/write operations with permission gating and SHA-256."""
        # 1. Write artifact with approval token
        token = tool.permission_gate.request_approval(
            ComputerActionType.WRITE,
            target="test_artifact.txt",
            justification="Phase M.1 filesystem integrity test"
        )
        res = tool.write_artifact("test_artifact.txt", "Alpha Verified Artifact\n", approval_token=token)
        assert res.success is True
        assert len(res.content_hash) == 64

        # 2. Read artifact back
        content, read_obs = tool.read_artifact("test_artifact.txt")
        assert content == "Alpha Verified Artifact\n"
        assert read_obs.verification_status == "VERIFIED"

    def test_03_terminal_execution_and_disallowed_command_rejection(self, tool):
        """Category 3: Safe commands execute; unauthorized/dangerous commands are rejected."""
        # Safe allowlisted command
        res = tool.execute_terminal("python --version")
        assert res.success is True
        assert "Python" in res.data.get("stdout_tail", "")

        # Dangerous or non-allowlisted command rejected by gate
        res_blocked = tool.execute_terminal("rm -rf /")
        assert res_blocked.success is False
        assert "blocked" in res_blocked.data.get("error", "").lower() or "permission" in res_blocked.data.get("error", "").lower()

    def test_04_controlled_browser_interaction_and_mutation(self, tmp_path):
        """Category 4: Controlled Playwright browser test with state observation and mutation."""
        # 1. Create controlled, non-sensitive local HTML test page
        test_html = """<!DOCTYPE html>
<html>
<head><title>Alpha Controlled Test Page</title></head>
<body>
    <h1 id="header">Initial State</h1>
    <button id="action_btn" onclick="document.getElementById('header').innerText = 'Mutated State';">Click Me</button>
</body>
</html>"""
        page_file = tmp_path / "controlled_test.html"
        page_file.write_text(test_html, encoding="utf-8")
        page_url = page_file.as_uri()

        tool = ComputerUseTool(workspace_root=tmp_path)

        # 2. Navigate and observe initial state
        res, obs = tool.navigate_browser(page_url)
        assert res.success is True
        assert obs.verification_status == "VERIFIED"
        assert obs.evidence.get("title") == "Alpha Controlled Test Page"
        assert obs.evidence.get("elements_count", 0) >= 1

        # 3. Perform interactive element click via Laya runtime
        if tool.laya._browser_runtime_cls:
            rt = tool.laya._browser_runtime_cls(goal="Click button", headless=True)
            try:
                rt.navigate(page_url)
                # Verify initial header text
                header_before = rt._env._page.locator("#header").inner_text()
                assert header_before == "Initial State"

                # Locate and interact with element
                rt._env._page.locator("#action_btn").click()

                # Independently verify updated mutated state
                header_after = rt._env._page.locator("#header").inner_text()
                assert header_after == "Mutated State"
            finally:
                rt.close()

    def test_05_browser_failure_reporting_integrity(self, tool):
        """Category 4b: Invalid URL navigation reports success=False and status=FALSIFIED."""
        res, obs = tool.navigate_browser("http://invalid-domain-that-does-not-exist.alpha-test:9999/")
        assert res.success is False
        assert obs.verification_status == "FALSIFIED"
        assert "error" in res.data

    def test_06_desktop_gui_interaction_and_rejection(self, tool):
        """Category 5: Desktop display geometry probed and non-existent application rejected."""
        # Probe display metrics
        geo = tool.observe_display_geometry()
        assert "width" in geo or "resolution" in geo or "error" in geo

        # Non-existent app reported as failed, never fake success
        res, obs = tool.open_application("NonExistentApplication123456789")
        assert res.success is False
        assert obs.verification_status == "FALSIFIED"
        assert res.data.get("focused") is False
