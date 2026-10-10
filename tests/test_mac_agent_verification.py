"""Verification Campaign Test Suite for the Apple Silicon Mac Computer-Use Agent (Phase 7).

Separates:
1. TestMacAgentAcceptanceAndClosedLoop (Tests 01 - 14):
   Platform-independent & real local HTTP/Playwright/Qwen acceptance tests executed on the Legion.
2. TestRealAppleSiliconMacNativeIntegration (Native Tests 01 - 03):
   Genuine macOS Aqua / Accessibility / Quartz vertical-slice integration tests.
   Explicitly marked SKIPPED (NOT RUN) when executed on a non-macOS host.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
import pytest
import requests

from alpha.computer_use.closed_loop import (
    ComputerUseTask,
    LayaClosedLoopRuntime,
)
from alpha.computer_use.mac_agent import (
    CancelTaskRequest,
    EmergencyStopRequest,
    ExecuteActionRequest,
    LocatorStrategy,
    MacActionType,
    MacAgentClientError,
    MacAgentHTTPServer,
    MacAgentPolicy,
    MacAgentServiceCore,
    MacComputerUseClient,
    MacModality,
    MacPermissionStatus,
    MacPlatformProbe,
    MacPlatformReport,
    ObserveRequest,
    SemanticLocator,
    VerificationStatus,
    VerifyOutcomeRequest,
)
from alpha.evidence_graph.graph import EvidenceGraph
from alpha.reasoning.qwen_reasoner import QwenStrategicReasoner


TEST_SHARED_SECRET = "alpha-mac-secret-token-987654321"


@pytest.fixture
def mac_test_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "mac_agent_ws"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "data" / "trajectories").mkdir(parents=True, exist_ok=True)
    return ws


@pytest.fixture
def harmless_local_form_page(mac_test_workspace: Path) -> Path:
    """Creates a harmless local HTML page with semantic form controls and dynamic state mutation."""
    html_file = mac_test_workspace / "mac_form_test.html"
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Alpha Mac Agent Local Verification Form</title>
</head>
<body>
    <h1 id="banner">Form Status: Awaiting Input</h1>
    <form id="verify-form" onsubmit="event.preventDefault(); submitForm();">
        <label for="project-name">Project Name</label>
        <input id="project-name" name="project_name" type="text" placeholder="Enter project name" />

        <label for="priority-select">Priority Level</label>
        <select id="priority-select" name="priority">
            <option value="low">Low</option>
            <option value="high">High</option>
        </select>

        <button id="submit-btn" type="submit">Submit Verification</button>
    </form>
    <div id="danger-zone">
        <button id="delete-btn" type="button" onclick="document.getElementById('banner').textContent = 'Deleted';">Delete Account Permanently</button>
    </div>
    <script>
        function submitForm() {
            const nameVal = document.getElementById('project-name').value || 'Unnamed';
            const prioVal = document.getElementById('priority-select').value;
            // Construct target string dynamically so it only exists in DOM after real submission
            const prefix = atob('Rm9ybSBTdGF0dXM6IFN1Ym1pdHRlZA==');
            document.getElementById('banner').textContent = prefix + ' [' + nameVal + ':' + prioVal + ']';
        }
    </script>
</body>
</html>
"""
    html_file.write_text(html_content, encoding="utf-8")
    return html_file


@pytest.fixture
def running_mac_agent_server(mac_test_workspace: Path):
    """Starts a live MacAgentHTTPServer bound to 127.0.0.1 on an ephemeral port with headless Chromium."""
    audit_path = mac_test_workspace / "data" / "mac_agent_audit.jsonl"
    policy = MacAgentPolicy(
        max_actions_per_task=10,
        max_duration_seconds=60.0,
        max_retries_per_task=2,
    )
    core = MacAgentServiceCore(
        auth_token=TEST_SHARED_SECRET,
        authorized_client_ips={"127.0.0.1", "::1"},
        policy=policy,
        audit_log_path=audit_path,
        headless_browser=True,
    )
    server = MacAgentHTTPServer(core=core, bind_host="127.0.0.1", bind_port=0)
    server.start()
    try:
        yield server
    finally:
        server.stop()


class TestMacAgentAcceptanceAndClosedLoop:
    """Minimum 14 acceptance tests + closed-loop Qwen integration."""

    def test_01_schema_validation_rejects_malformed_requests(self, running_mac_agent_server: MacAgentHTTPServer):
        """Acceptance Test 1: Strict schema validation rejects extra fields, invalid JSON, and unreasoned coordinates."""
        base_url = running_mac_agent_server.base_url
        headers = {"Authorization": f"Bearer {TEST_SHARED_SECRET}", "Content-Type": "application/json"}

        # 1a. Malformed raw JSON
        r_bad_json = requests.post(f"{base_url}/v1/observe", headers=headers, data="{not_valid_json", timeout=5)
        assert r_bad_json.status_code == 400
        assert r_bad_json.json()["error_code"] == "MALFORMED_JSON"

        # 1b. Extra forbidden field in request
        r_extra = requests.post(
            f"{base_url}/v1/observe",
            headers=headers,
            json={"api_version": "v1", "task_id": "t1", "unexpected_hacker_field": True},
            timeout=5,
        )
        assert r_extra.status_code == 422
        assert r_extra.json()["error_code"] == "SCHEMA_VALIDATION_FAILED"

        # 1c. Coordinate locator without coordinate_fallback_reason is rejected
        r_coord = requests.post(
            f"{base_url}/v1/execute_action",
            headers=headers,
            json={
                "api_version": "v1",
                "task_id": "t1",
                "action_type": "BROWSER_CLICK",
                "locator": {"by": "coordinates", "x": 100, "y": 200},
            },
            timeout=5,
        )
        assert r_coord.status_code == 422
        assert "coordinate_fallback_reason" in r_coord.json()["error"]

    def test_02_authentication_rejects_missing_or_invalid_credentials(
        self, running_mac_agent_server: MacAgentHTTPServer
    ):
        """Acceptance Test 2: Missing or wrong Bearer token fails closed with HTTP 401."""
        base_url = running_mac_agent_server.base_url

        # Missing header
        r_no_auth = requests.get(f"{base_url}/v1/health", timeout=5)
        assert r_no_auth.status_code == 401
        assert r_no_auth.json()["error_code"] == "AUTHENTICATION_FAILED"

        # Invalid token
        client_bad = MacComputerUseClient(base_url=base_url, auth_token="wrong-token-value-000")
        with pytest.raises(MacAgentClientError) as exc_info:
            client_bad.health()
        assert exc_info.value.status_code == 401
        assert exc_info.value.error_code == "AUTHENTICATION_FAILED"

    def test_03_unknown_action_types_and_remote_shell_rejected(
        self, running_mac_agent_server: MacAgentHTTPServer
    ):
        """Acceptance Test 3: Unknown action types and arbitrary shell commands are rejected."""
        base_url = running_mac_agent_server.base_url
        headers = {"Authorization": f"Bearer {TEST_SHARED_SECRET}"}

        r_unknown = requests.post(
            f"{base_url}/v1/execute_action",
            headers=headers,
            json={
                "api_version": "v1",
                "task_id": "t_unknown",
                "action_type": "ARBITRARY_SHELL_EXEC",
            },
            timeout=5,
        )
        assert r_unknown.status_code == 422
        assert r_unknown.json()["error_code"] == "SCHEMA_VALIDATION_FAILED"

        # Client-level terminal execution contract explicitly refuses remote shell
        client = MacComputerUseClient(base_url=base_url, auth_token=TEST_SHARED_SECRET)
        from alpha.computer_use.permissions import ApprovalToken, ComputerActionType

        tok = ApprovalToken(action_type=ComputerActionType.EXECUTE, target="ls", reason="test")
        shell_res = client.execute_terminal_action("rm -rf /", approval_token=tok)
        assert shell_res["ok"] is False
        assert shell_res["error_code"] == "REMOTE_SHELL_FORBIDDEN"

    def test_04_agent_reports_missing_permissions_honestly(self, mac_test_workspace: Path):
        """Acceptance Test 4: Missing macOS Accessibility/Screen Recording permissions are reported honestly."""
        unpermitted_darwin_report = MacPlatformReport(
            system="Darwin",
            is_macos=True,
            architecture="arm64",
            is_apple_silicon=True,
            macos_version="15.1",
            macos_build="24B83",
            macos_release_family="macOS 15 Sequoia",
            is_root_process=False,
            is_graphical_user_session=True,
            session_manager_type="Aqua",
            logged_in_user="mac_operator",
            playwright_available=True,
            permissions=MacPermissionStatus(
                accessibility_granted=False,
                screen_recording_granted=False,
                automation_granted=False,
                missing_permissions=["ACCESSIBILITY", "SCREEN_RECORDING"],
                remediation_instructions=[
                    "Grant Accessibility permission in System Settings -> Privacy & Security -> Accessibility."
                ],
            ),
            ready_for_browser=True,
            ready_for_native_gui=False,
        )
        probe = MacPlatformProbe(override_report=unpermitted_darwin_report)
        core = MacAgentServiceCore(
            auth_token=TEST_SHARED_SECRET,
            platform_probe=probe,
            audit_log_path=mac_test_workspace / "data" / "audit_perm.jsonl",
            headless_browser=True,
        )
        try:
            caps = core.get_capabilities()
            assert caps.browser_supported is True
            assert caps.native_gui_supported is False
            assert "NATIVE_GUI" not in caps.modalities_supported
            assert "ACCESSIBILITY" in caps.platform_report["permissions"]["missing_permissions"]

            # Attempting a native GUI click must fail clearly with MISSING_ACCESSIBILITY_PERMISSION
            act_resp = core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_perm",
                    modality=MacModality.NATIVE_GUI,
                    action_type=MacActionType.NATIVE_CLICK,
                    app_name="AlphaMacTestApp",
                    locator=SemanticLocator(by=LocatorStrategy.ROLE, role="button", name="Increment Counter"),
                )
            )
            assert act_resp.ok is False
            assert act_resp.error_code == "MISSING_ACCESSIBILITY_PERMISSION"
            assert act_resp.verification is not None
            assert act_resp.verification.verification_status == VerificationStatus.FALSIFIED
        finally:
            core.close()

    def test_05_browser_launch_and_local_page_navigation(
        self, running_mac_agent_server: MacAgentHTTPServer, harmless_local_form_page: Path
    ):
        """Acceptance Test 5: Browser launches with isolated profile and navigates to allowed local URL."""
        client = MacComputerUseClient(
            base_url=running_mac_agent_server.base_url,
            auth_token=TEST_SHARED_SECRET,
        )
        nav_resp = client.execute_action(
            ExecuteActionRequest(
                task_id="t_nav_05",
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_NAVIGATE,
                url=harmless_local_form_page.as_uri(),
                expected_postcondition={"title_contains": "Alpha Mac Agent Local Verification Form"},
            )
        )
        assert nav_resp.ok is True
        assert nav_resp.post_observation is not None
        assert "mac_form_test.html" in nav_resp.post_observation.url
        assert nav_resp.post_observation.page_title == "Alpha Mac Agent Local Verification Form"
        assert "alpha_mac_browser_profile_" in nav_resp.post_observation.metadata.get("isolated_profile_dir", "")
        assert nav_resp.verification is not None
        assert nav_resp.verification.verification_status == VerificationStatus.VERIFIED

    def test_06_real_browser_form_fill_and_submit(
        self, running_mac_agent_server: MacAgentHTTPServer, harmless_local_form_page: Path
    ):
        """Acceptance Test 6: A real browser form can be filled and submitted on a harmless local test page."""
        client = MacComputerUseClient(
            base_url=running_mac_agent_server.base_url,
            auth_token=TEST_SHARED_SECRET,
        )
        task_id = "t_form_06"

        # 1. Navigate to form page
        client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_NAVIGATE,
                url=harmless_local_form_page.as_uri(),
            )
        )

        # 2. Fill 'Project Name' by semantic label
        type_resp = client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_TYPE,
                locator=SemanticLocator(by=LocatorStrategy.LABEL, value="Project Name"),
                text="AlphaSiliconBridge",
            )
        )
        assert type_resp.ok is True
        assert type_resp.verification is not None
        assert type_resp.verification.state_changed is True

        # 3. Select 'High' priority by semantic label
        sel_resp = client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_SELECT,
                locator=SemanticLocator(by=LocatorStrategy.LABEL, value="Priority Level"),
                text="high",
            )
        )
        assert sel_resp.ok is True

        # 4. Click 'Submit Verification' button by semantic role + accessible name
        click_resp = client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_CLICK,
                locator=SemanticLocator(
                    by=LocatorStrategy.ROLE,
                    role="button",
                    name="Submit Verification",
                ),
                capture_screenshot=True,
                expected_postcondition={
                    "dom_contains": "Form Status: Submitted [AlphaSiliconBridge:high]"
                },
            )
        )
        assert click_resp.ok is True
        assert click_resp.post_observation is not None
        assert click_resp.post_observation.screenshot_base64 is not None
        assert len(click_resp.post_observation.screenshot_base64) > 100
        assert click_resp.verification is not None
        assert click_resp.verification.verification_status == VerificationStatus.VERIFIED
        assert click_resp.verification.postcondition_satisfied is True

    def test_07_browser_resulting_state_independently_verified(
        self, running_mac_agent_server: MacAgentHTTPServer, harmless_local_form_page: Path
    ):
        """Acceptance Test 7: The browser's resulting state is independently inspected and verified."""
        client = MacComputerUseClient(
            base_url=running_mac_agent_server.base_url,
            auth_token=TEST_SHARED_SECRET,
        )
        task_id = "t_verify_07"

        nav_resp = client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_NAVIGATE,
                url=harmless_local_form_page.as_uri(),
            )
        )
        baseline_hash = nav_resp.post_observation.state_hash if nav_resp.post_observation else ""

        client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_TYPE,
                locator=SemanticLocator(by=LocatorStrategy.LABEL, value="Project Name"),
                text="IndependentCheck",
            )
        )
        client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_CLICK,
                locator=SemanticLocator(by=LocatorStrategy.ROLE, role="button", name="Submit Verification"),
            )
        )

        # Independent verification call (/v1/verify_outcome)
        indep_verif = client.verify_outcome(
            VerifyOutcomeRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                expected_postcondition={
                    "dom_contains": "Form Status: Submitted [IndependentCheck:low]"
                },
                baseline_state_hash=baseline_hash,
            )
        )
        assert indep_verif.ok is True
        assert indep_verif.verification.verification_status == VerificationStatus.VERIFIED
        assert indep_verif.verification.state_changed is True
        assert indep_verif.verification.pre_state_hash == baseline_hash
        assert indep_verif.verification.post_state_hash != baseline_hash

    def test_08_deliberate_failed_action_and_dry_run_truthful_reporting(
        self, running_mac_agent_server: MacAgentHTTPServer, harmless_local_form_page: Path
    ):
        """Acceptance Test 8: Deliberate failed action returns FALSIFIED; dry-run returns INCONCLUSIVE without mutating."""
        client = MacComputerUseClient(
            base_url=running_mac_agent_server.base_url,
            auth_token=TEST_SHARED_SECRET,
        )
        task_id = "t_fail_08"
        client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_NAVIGATE,
                url=harmless_local_form_page.as_uri(),
            )
        )

        # Dry-run click on Submit button must not mutate state
        dry_resp = client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_CLICK,
                locator=SemanticLocator(by=LocatorStrategy.ROLE, role="button", name="Submit Verification"),
                dry_run=True,
            )
        )
        assert dry_resp.ok is True
        assert dry_resp.dry_run is True
        assert dry_resp.verification is not None
        assert dry_resp.verification.verification_status == VerificationStatus.INCONCLUSIVE
        assert dry_resp.verification.state_changed is False

        # Deliberate failure: click non-existent button
        fail_resp = client.execute_action(
            ExecuteActionRequest(
                task_id=task_id,
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_CLICK,
                locator=SemanticLocator(by=LocatorStrategy.ROLE, role="button", name="NonExistentGhostButton99"),
                timeout_seconds=1.0,
                expected_postcondition={"dom_contains": "Form Status: Submitted"},
            )
        )
        assert fail_resp.ok is False
        assert fail_resp.verification is not None
        assert fail_resp.verification.verification_status == VerificationStatus.FALSIFIED
        assert fail_resp.verification.postcondition_satisfied is False

    def test_09_cancellation_and_emergency_stop_prevent_further_actions(
        self, running_mac_agent_server: MacAgentHTTPServer, harmless_local_form_page: Path
    ):
        """Acceptance Test 9: Per-task cancellation and global emergency stop immediately block actions."""
        client = MacComputerUseClient(
            base_url=running_mac_agent_server.base_url,
            auth_token=TEST_SHARED_SECRET,
        )

        # 1. Per-task cancellation
        cancel_status = client.cancel_task("task_to_cancel", reason="User aborted task")
        assert cancel_status.cancelled is True
        assert cancel_status.status == "CANCELLED"

        blocked_Cancel = client.execute_action(
            ExecuteActionRequest(
                task_id="task_to_cancel",
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_NAVIGATE,
                url=harmless_local_form_page.as_uri(),
            )
        )
        assert blocked_Cancel.ok is False
        assert blocked_Cancel.error_code == "TASK_CANCELLED"

        # 2. Global emergency stop
        estop_health = client.emergency_stop(reason="Critical operator halt")
        assert estop_health.emergency_stop_engaged is True
        assert estop_health.status == "emergency_stopped"

        blocked_estop = client.execute_action(
            ExecuteActionRequest(
                task_id="any_other_task",
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_NAVIGATE,
                url=harmless_local_form_page.as_uri(),
            )
        )
        assert blocked_estop.ok is False
        assert blocked_estop.error_code == "EMERGENCY_STOP_ACTIVE"

        # Reset emergency stop for subsequent operations
        reset_health = client.emergency_stop(reason="Operator cleared stop", reset=True)
        assert reset_health.emergency_stop_engaged is False

    def test_10_timeouts_and_action_budgets_obey_configured_limits(
        self, mac_test_workspace: Path, harmless_local_form_page: Path
    ):
        """Acceptance Test 10: Action budgets and retries strictly enforce configured limits."""
        policy = MacAgentPolicy(max_actions_per_task=2, max_duration_seconds=30.0, max_retries_per_task=1)
        core = MacAgentServiceCore(
            auth_token=TEST_SHARED_SECRET,
            policy=policy,
            audit_log_path=mac_test_workspace / "data" / "audit_budget.jsonl",
            headless_browser=True,
        )
        try:
            # Action 1 (allowed)
            r1 = core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_budget",
                    action_type=MacActionType.BROWSER_NAVIGATE,
                    url=harmless_local_form_page.as_uri(),
                )
            )
            assert r1.ok is True

            # Action 2 (allowed)
            r2 = core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_budget",
                    action_type=MacActionType.WAIT,
                    wait_ms=50,
                )
            )
            assert r2.ok is True

            # Action 3 (exceeds max_actions=2 -> blocked!)
            r3 = core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_budget",
                    action_type=MacActionType.WAIT,
                    wait_ms=50,
                )
            )
            assert r3.ok is False
            assert r3.error_code == "ACTION_BUDGET_EXHAUSTED"

            # Verify retry limit
            ok_retry1, _ = policy.record_action_attempt("t_budget", is_retry=True)
            assert ok_retry1 is True
            ok_retry2, msg_retry2 = policy.record_action_attempt("t_budget", is_retry=True)
            assert ok_retry2 is False
            assert "Retry budget exhausted" in msg_retry2
        finally:
            core.close()

    def test_11_audit_records_contain_chain_and_redact_secrets(
        self, running_mac_agent_server: MacAgentHTTPServer, harmless_local_form_page: Path, mac_test_workspace: Path
    ):
        """Acceptance Test 11: Audit log records observation-action-outcome chain and scrubs secrets."""
        client = MacComputerUseClient(
            base_url=running_mac_agent_server.base_url,
            auth_token=TEST_SHARED_SECRET,
        )
        client.execute_action(
            ExecuteActionRequest(
                task_id="t_audit_11",
                modality=MacModality.BROWSER,
                action_type=MacActionType.BROWSER_NAVIGATE,
                url=harmless_local_form_page.as_uri(),
                rationale="Navigate with secret password=SuperSecretPassword123 and Bearer abcdef123456",
            )
        )

        audit_file = mac_test_workspace / "data" / "mac_agent_audit.jsonl"
        assert audit_file.exists()
        raw_log = audit_file.read_text(encoding="utf-8")
        assert "SuperSecretPassword123" not in raw_log
        assert "abcdef123456" not in raw_log
        assert "[REDACTED_SECRET]" in raw_log

        entries = [json.loads(line) for line in raw_log.splitlines() if line.strip()]
        exec_entries = [e for e in entries if e.get("event_type") == "EXECUTE_ACTION" and e.get("task_id") == "t_audit_11"]
        assert len(exec_entries) >= 1
        rec = exec_entries[-1]
        assert rec["pre_observation_id"] is not None
        assert rec["pre_state_hash"] != ""
        assert rec["post_observation_id"] is not None
        assert rec["post_state_hash"] != ""
        assert rec["verification"]["verification_status"] == "VERIFIED"

    def test_12_legion_to_mac_private_connection_and_qwen_closed_loop(
        self, running_mac_agent_server: MacAgentHTTPServer, harmless_local_form_page: Path, mac_test_workspace: Path
    ):
        """Acceptance Test 12: Legion reaches Mac agent over private connection and executes live Qwen closed loop."""
        client = MacComputerUseClient(
            base_url=running_mac_agent_server.base_url,
            auth_token=TEST_SHARED_SECRET,
        )
        health = client.health()
        assert health.ready is True

        eg = EvidenceGraph(storage_path=mac_test_workspace / "data" / "evidence_graph.json")
        reasoner = QwenStrategicReasoner(timeout=30.0)
        closed_loop = LayaClosedLoopRuntime(
            workspace_root=mac_test_workspace,
            reasoner=reasoner,
            evidence_graph=eg,
            trajectory_dir=mac_test_workspace / "data" / "trajectories",
            mac_client=client,
        )

        task = ComputerUseTask(
            goal="Click the Submit Verification button to submit the form",
            modality="MAC_BROWSER",
            target_url=harmless_local_form_page.as_uri(),
            expected_postcondition={"dom_contains": "Form Status: Submitted"},
            max_steps=3,
            max_duration_seconds=45.0,
        )
        traj = closed_loop.execute_task(task)
        assert traj.status == "VERIFIED_SUCCESS"
        assert len(traj.steps) >= 1
        assert len(eg.action_nodes) >= 1
        assert len(eg.outcome_nodes) >= 1

    def test_13_mac_rejects_unauthorized_client_ip_and_public_bind(self, mac_test_workspace: Path):
        """Acceptance Test 13: Rejects unauthorized client IPs (HTTP 403) and refuses non-private bind hosts."""
        core = MacAgentServiceCore(
            auth_token=TEST_SHARED_SECRET,
            authorized_client_ips={"10.99.99.99"},  # 127.0.0.1 is NOT in authorized list
            audit_log_path=mac_test_workspace / "data" / "audit_ip.jsonl",
            headless_browser=True,
        )
        # 13a. Refuses to bind to 0.0.0.0 or public internet IP
        with pytest.raises(ValueError, match="Refusing to bind"):
            MacAgentHTTPServer(core=core, bind_host="0.0.0.0", bind_port=0)
        with pytest.raises(ValueError, match="Refusing to bind"):
            MacAgentHTTPServer(core=core, bind_host="8.8.8.8", bind_port=0)

        # 13b. Rejects unauthorized client IP with HTTP 403
        server = MacAgentHTTPServer(core=core, bind_host="127.0.0.1", bind_port=0)
        server.start()
        try:
            client = MacComputerUseClient(base_url=server.base_url, auth_token=TEST_SHARED_SECRET)
            with pytest.raises(MacAgentClientError) as exc_info:
                client.health()
            assert exc_info.value.status_code == 403
            assert exc_info.value.error_code == "UNAUTHORIZED_CLIENT_IP"
        finally:
            server.stop()

    def test_14_restarting_service_preserves_safe_defaults_and_consequential_gate(
        self, mac_test_workspace: Path, harmless_local_form_page: Path
    ):
        """Acceptance Test 14: Fresh service restart enforces deny-by-default URL/App rules and consequential action confirmation."""
        # Simulate service restart by creating a new MacAgentServiceCore with default policy
        restarted_core = MacAgentServiceCore(
            auth_token=TEST_SHARED_SECRET,
            audit_log_path=mac_test_workspace / "data" / "audit_restart.jsonl",
            headless_browser=True,
        )
        try:
            assert restarted_core.policy.deny_by_default is True
            assert restarted_core.policy.require_consequential_confirmation is True

            # 14a. Unapproved external URL is blocked by default
            unapproved_url_resp = restarted_core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_restart",
                    modality=MacModality.BROWSER,
                    action_type=MacActionType.BROWSER_NAVIGATE,
                    url="https://untrusted-external-domain.example.com/login",
                )
            )
            assert unapproved_url_resp.ok is False
            assert unapproved_url_resp.error_code == "URL_NOT_ALLOWED"

            # 14b. Forbidden application ('Terminal') is blocked by default
            forbidden_app_resp = restarted_core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_restart",
                    modality=MacModality.NATIVE_GUI,
                    action_type=MacActionType.NATIVE_LAUNCH_APP,
                    app_name="Terminal",
                )
            )
            assert forbidden_app_resp.ok is False
            assert forbidden_app_resp.error_code == "APPLICATION_NOT_ALLOWED"

            # 14c. Consequential action ('Delete Account Permanently') is blocked without user confirmation
            restarted_core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_restart",
                    modality=MacModality.BROWSER,
                    action_type=MacActionType.BROWSER_NAVIGATE,
                    url=harmless_local_form_page.as_uri(),
                )
            )
            conseq_blocked = restarted_core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_restart",
                    modality=MacModality.BROWSER,
                    action_type=MacActionType.BROWSER_CLICK,
                    locator=SemanticLocator(
                        by=LocatorStrategy.ROLE,
                        role="button",
                        name="Delete Account Permanently",
                    ),
                    consequential_confirmed_by_user=False,
                )
            )
            assert conseq_blocked.ok is False
            assert conseq_blocked.error_code == "CONSEQUENTIAL_CONFIRMATION_REQUIRED"

            # 14d. With explicit user confirmation, consequential action is permitted
            conseq_allowed = restarted_core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_restart",
                    modality=MacModality.BROWSER,
                    action_type=MacActionType.BROWSER_CLICK,
                    locator=SemanticLocator(
                        by=LocatorStrategy.ROLE,
                        role="button",
                        name="Delete Account Permanently",
                    ),
                    consequential_confirmed_by_user=True,
                )
            )
            assert conseq_allowed.ok is True
        finally:
            restarted_core.close()


@pytest.mark.skipif(
    sys.platform != "darwin",
    reason="NOT RUN: Physical Apple Silicon macOS host required for native Darwin/Aqua/AXUIElement tests.",
)
class TestRealAppleSiliconMacNativeIntegration:
    """Native macOS integration tests to be executed directly on the Apple Silicon MacBook."""

    def test_mac_native_01_apple_silicon_arm64_and_aqua_session_detection(self):
        """Verifies live Darwin kernel, arm64 architecture, and logged-in Aqua GUI session."""
        probe = MacPlatformProbe()
        rep = probe.inspect_platform()
        assert rep.is_macos is True
        assert rep.is_apple_silicon is True
        assert rep.is_root_process is False
        assert rep.is_graphical_user_session is True

    def test_mac_native_02_harmless_test_app_launch_click_and_independent_verification(
        self, mac_test_workspace: Path
    ):
        """Launches AlphaMacTestApp on macOS, clicks 'Increment Counter', and verifies UI mutation."""
        core = MacAgentServiceCore(
            auth_token=TEST_SHARED_SECRET,
            audit_log_path=mac_test_workspace / "data" / "audit_native_mac.jsonl",
        )
        try:
            launch_resp = core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_mac_native",
                    modality=MacModality.NATIVE_GUI,
                    action_type=MacActionType.NATIVE_LAUNCH_APP,
                    app_name="AlphaMacTestApp",
                )
            )
            assert launch_resp.ok is True

            click_resp = core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_mac_native",
                    modality=MacModality.NATIVE_GUI,
                    action_type=MacActionType.NATIVE_CLICK,
                    app_name="Python",
                    locator=SemanticLocator(
                        by=LocatorStrategy.ROLE,
                        role="button",
                        name="Increment Counter",
                    ),
                    expected_postcondition={"text_contains": "Status: Mutated | Counter: 1"},
                )
            )
            assert click_resp.ok is True
            assert click_resp.verification is not None
            assert click_resp.verification.verification_status == VerificationStatus.VERIFIED
        finally:
            core.close()

    def test_mac_native_03_native_screenshot_capture_with_tcc_permission(
        self, mac_test_workspace: Path
    ):
        """Captures a native macOS screen image after verifying TCC Screen Recording permission."""
        core = MacAgentServiceCore(
            auth_token=TEST_SHARED_SECRET,
            audit_log_path=mac_test_workspace / "data" / "audit_native_sc.jsonl",
        )
        try:
            sc_resp = core.handle_execute_action(
                ExecuteActionRequest(
                    task_id="t_mac_sc",
                    modality=MacModality.NATIVE_GUI,
                    action_type=MacActionType.NATIVE_SCREENSHOT,
                    app_name="Finder",
                    capture_screenshot=True,
                )
            )
            assert sc_resp.ok is True
            assert sc_resp.post_observation is not None
            assert sc_resp.post_observation.screenshot_base64 is not None
        finally:
            core.close()
