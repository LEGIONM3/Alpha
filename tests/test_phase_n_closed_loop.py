"""Test Suite for Project Alpha Phase N: Real Laya Computer Use and Closed-Loop Execution.

Verifies:
1. Authentic Playwright browser navigation and observation.
2. Qwen-driven closed-loop element interaction with independently observed mutation.
3. Missing elements handling and honest failure classification.
4. Navigation timeout / unreachable endpoint failure handling.
5. Context / browser failure safe termination.
6. Malformed model action proposal handling and recovery.
7. Failed or unobserved actions NEVER recorded as verified success (strict invariant).
8. Action-budget and duration exhaustion boundaries.
9. Transient failure recovery replanning.
10. Trajectory file persistence and EvidenceGraph integration.
11. Desktop GUI modality distinction and isolation handling.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import pytest
import time
import uuid

from alpha.computer_use.closed_loop import (
    LayaClosedLoopRuntime,
    ComputerUseTask,
    ComputerUseTrajectory,
    ModelActionProposal,
    PostActionVerification,
    TrajectoryStepRecord,
)
from alpha.computer_use.permissions import ComputerActionType, PermissionGate, ApprovalToken
from alpha.computer_use.computer_use_tool import ComputerUseTool
from alpha.reasoning.qwen_reasoner import QwenStrategicReasoner, resolve_default_model_endpoint
from alpha.evidence_graph.graph import EvidenceGraph


@pytest.fixture
def test_workspace(tmp_path):
    """Provides an isolated workspace with trajectory directory and local test HTML pages."""
    ws = tmp_path / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    traj_dir = ws / "data" / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)
    return ws


@pytest.fixture
def local_html_page(test_workspace):
    """Creates a deterministic local HTML test page with multiple elements and an interactive control."""
    page_path = test_workspace / "interactive_test.html"
    content = """<!DOCTYPE html>
<html>
<head>
    <title>Alpha Interactive Bounded Test</title>
</head>
<body>
    <header>
        <h1 id="status-heading">Status: Initial Baseline</h1>
        <p id="info-p">Alpha closed-loop verification page</p>
    </header>
    <main>
        <section id="control-panel">
            <button id="mutate-btn" onclick="document.getElementById('status-heading').textContent = atob('U3RhdHVzOiBNdXRhdGVkIEFscGhhIFN0YXRl');">Execute Action</button>
            <input type="text" id="test-input" placeholder="Enter test query" />
        </section>
        <section id="results">
            <span id="output-badge">Badge: Pending</span>
        </section>
    </main>
</body>
</html>
"""
    page_path.write_text(content, encoding="utf-8")
    return page_path


@pytest.fixture
def closed_loop_runtime(test_workspace):
    """Initializes LayaClosedLoopRuntime with live Qwen reasoner and local storage."""
    graph_path = test_workspace / "data" / "evidence_graph.json"
    eg = EvidenceGraph(storage_path=graph_path)
    gate = PermissionGate()
    reasoner = QwenStrategicReasoner(timeout=30.0)
    rt = LayaClosedLoopRuntime(
        workspace_root=test_workspace,
        reasoner=reasoner,
        permission_gate=gate,
        evidence_graph=eg,
        trajectory_dir=test_workspace / "data" / "trajectories"
    )
    return rt


class TestPhaseNClosedLoopExecution:

    def test_01_successful_navigation_and_observation(self, closed_loop_runtime, local_html_page):
        """Case 1: Runtime successfully navigates to local test page and observes actual DOM state."""
        task = ComputerUseTask(
            goal="Navigate to local test page and observe interactive elements",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            expected_postcondition={"url_contains": "interactive_test.html"},
            max_steps=1,
            max_duration_seconds=30.0
        )
        traj = closed_loop_runtime.execute_task(task)

        assert traj.task_id == task.task_id
        assert traj.status == "VERIFIED_SUCCESS"
        assert len(traj.steps) >= 1
        assert traj.steps[0].pre_state_hash != ""
        assert traj.steps[0].verification.get("outcome") in ("SUCCESS", "PARTIAL")

    def test_02_element_interaction_and_independently_observed_mutation(self, closed_loop_runtime, local_html_page):
        """Case 2: Full closed loop where Qwen selects button, actuator clicks, and mutation is verified."""
        task = ComputerUseTask(
            goal="Click the button to update status to Mutated Alpha State",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            expected_postcondition={"dom_contains": "Status: Mutated Alpha State"},
            max_steps=3,
            max_duration_seconds=45.0
        )
        traj = closed_loop_runtime.execute_task(task)

        assert traj.status == "VERIFIED_SUCCESS"
        assert traj.final_verification is not None
        assert traj.final_verification.get("postcondition_satisfied") is True
        # Verify that state mutation was genuinely observed
        has_changed_step = any(s.verification.get("state_changed") is True for s in traj.steps)
        assert has_changed_step is True

    def test_03_missing_element_rejection_and_failure(self, closed_loop_runtime, local_html_page):
        """Case 3: Proposing action on nonexistent element fails safely and records failure."""
        task = ComputerUseTask(
            goal="Click nonexistent non_existent_button_99",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            expected_postcondition={"dom_contains": "Never Occurs"},
            max_steps=1,
            max_duration_seconds=30.0
        )

        # Force proposal with absent target
        bad_proposal = ModelActionProposal(
            action="CLICK",
            target_id="non_existent_element_xyz_999",
            rationale="Intentional bad target test",
            intended_effect="Trigger missing element error"
        )
        closed_loop_runtime._deliberate_next_action = lambda **kw: (bad_proposal, {"note": "forced_bad_target"})

        traj = closed_loop_runtime.execute_task(task)
        assert traj.status in ("VERIFIED_FAILURE", "BUDGET_EXHAUSTED")
        assert len(traj.steps) >= 1
        step1 = traj.steps[0]
        # Invariant: Action failure must not be recorded as success
        assert step1.verification.get("outcome") != "SUCCESS"

    def test_04_navigation_timeout_or_unreachable_endpoint(self, closed_loop_runtime):
        """Case 4: Navigation to unresolvable local port cleanly fails with honest error."""
        task = ComputerUseTask(
            goal="Navigate to invalid closed endpoint",
            modality="BROWSER",
            target_url="http://127.0.0.1:59998/nonexistent_page",
            max_steps=1,
            max_duration_seconds=5.0
        )
        traj = closed_loop_runtime.execute_task(task)
        assert traj.status in ("VERIFIED_FAILURE", "TIMEOUT")
        assert traj.error is not None
        assert "failed" in traj.error.lower() or "exception" in traj.error.lower() or "timeout" in traj.error.lower()

    def test_05_browser_process_failure_safe_termination(self, closed_loop_runtime, test_workspace):
        """Case 5: Missing runtime backend terminates safely without silent mock masking."""
        task = ComputerUseTask(
            goal="Test unavailable runtime",
            modality="BROWSER",
            target_url="file:///dummy.html"
        )
        # Temporarily null out runtime class
        closed_loop_runtime.laya._browser_runtime_cls = None
        traj = closed_loop_runtime.execute_task(task)

        assert traj.status == "VERIFIED_FAILURE"
        assert "unavailable" in traj.error.lower()

    def test_06_malformed_model_output_handling_and_recovery(self, closed_loop_runtime, local_html_page):
        """Case 6: Malformed model output failsafe does not execute random or destructive actions."""
        task = ComputerUseTask(
            goal="Test malformed output recovery",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            max_steps=2,
            max_duration_seconds=30.0
        )

        call_count = 0
        def fake_deliberate(**kw):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Malformed output returns safe WAIT
                return (
                    ModelActionProposal(action="WAIT", payload="50", rationale="Malformed json recovery", intended_effect="Wait"),
                    {"malformed": True}
                )
            else:
                # Valid completion
                return (
                    ModelActionProposal(action="COMPLETE", rationale="Done", intended_effect="Done"),
                    {"ok": True}
                )

        closed_loop_runtime._deliberate_next_action = fake_deliberate
        traj = closed_loop_runtime.execute_task(task)
        assert len(traj.steps) >= 1
        assert traj.steps[0].action_proposal["action"] == "WAIT"

    def test_07_invariant_failed_action_never_recorded_as_success(self, closed_loop_runtime, local_html_page):
        """Case 7: Strict Invariant: Claiming COMPLETE when postconditions failed must be FALSIFIED."""
        task = ComputerUseTask(
            goal="Verify strict postcondition enforcement",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            expected_postcondition={"dom_contains": "THIS_TEXT_DEFINITELY_DOES_NOT_EXIST_ANYWHERE"},
            max_steps=2,
            max_duration_seconds=30.0
        )

        # Model claims COMPLETE immediately despite postcondition being unsatisfied
        premature_complete = ModelActionProposal(
            action="COMPLETE",
            rationale="Hallucinated success claim",
            intended_effect="Claim done"
        )
        closed_loop_runtime._deliberate_next_action = lambda **kw: (premature_complete, {})

        traj = closed_loop_runtime.execute_task(task)
        # MUST NOT be marked VERIFIED_SUCCESS!
        assert traj.status != "VERIFIED_SUCCESS"
        assert traj.status == "VERIFIED_FAILURE"
        assert traj.final_verification["verification_status"] == "FALSIFIED"

    def test_08_action_budget_and_duration_exhaustion(self, closed_loop_runtime, local_html_page):
        """Case 8: Task with unmet criteria terminates cleanly when max_steps budget is reached."""
        task = ComputerUseTask(
            goal="Endless wait task testing step budget",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            expected_postcondition={"dom_contains": "Unattainable Condition"},
            max_steps=2,
            max_duration_seconds=45.0
        )
        wait_proposal = ModelActionProposal(
            action="WAIT",
            payload="100",
            rationale="Idle step",
            intended_effect="Nothing"
        )
        closed_loop_runtime._deliberate_next_action = lambda **kw: (wait_proposal, {})

        traj = closed_loop_runtime.execute_task(task)
        assert traj.total_steps == 2
        assert traj.status in ("BUDGET_EXHAUSTED", "VERIFIED_FAILURE")

    def test_09_recovery_after_transient_failure(self, closed_loop_runtime, local_html_page):
        """Case 9: Step 1 fails, replans with valid action on step 2, achieving verified success."""
        task = ComputerUseTask(
            goal="Test recovery replanning",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            expected_postcondition={"dom_contains": "Status: Mutated Alpha State"},
            max_steps=3,
            max_recoveries=2,
            max_duration_seconds=45.0
        )

        step_counter = 0
        def dynamic_planner(current_obs, **kw):
            nonlocal step_counter
            step_counter += 1
            if step_counter == 1:
                # Step 1: propose invalid target that fails
                return (
                    ModelActionProposal(action="CLICK", target_id="bad_target_e99", rationale="Fail step", intended_effect="Error"),
                    {"step": 1}
                )
            else:
                # Step 2: recover by finding real button
                btn_id = None
                for el in current_obs.get("elements", []):
                    if "Execute Action" in el.get("name", ""):
                        btn_id = el.get("id")
                        break
                return (
                    ModelActionProposal(action="CLICK", target_id=btn_id or "e0", rationale="Recover step", intended_effect="Mutate"),
                    {"step": 2}
                )

        closed_loop_runtime._deliberate_next_action = lambda current_obs, **kw: dynamic_planner(current_obs, **kw)
        traj = closed_loop_runtime.execute_task(task)

        assert traj.recovery_count >= 1
        assert traj.status == "VERIFIED_SUCCESS"
        assert traj.final_verification["postcondition_satisfied"] is True

    def test_10_trajectory_persistence_and_evidence_graph_linkage(self, closed_loop_runtime, local_html_page, test_workspace):
        """Case 10: Trajectory record is persisted to disk and linked into EvidenceGraph."""
        task = ComputerUseTask(
            goal="Persistence and evidence linkage verification",
            modality="BROWSER",
            target_url=local_html_page.as_uri(),
            expected_postcondition={"dom_contains": "Status: Mutated Alpha State"},
            max_steps=2
        )
        traj = closed_loop_runtime.execute_task(task)

        # 1. Verify JSON file on disk
        traj_file = test_workspace / "data" / "trajectories" / f"{traj.task_id}_{traj.run_id}.json"
        assert traj_file.exists()
        saved_data = json.loads(traj_file.read_text(encoding="utf-8"))
        assert saved_data["task_id"] == traj.task_id
        assert len(saved_data["steps"]) == len(traj.steps)

        # 2. Verify EvidenceGraph has Action and Outcome nodes
        assert len(closed_loop_runtime.evidence_graph.action_nodes) >= 1
        assert len(closed_loop_runtime.evidence_graph.outcome_nodes) >= 1

        # 3. Verify decision audit trail append
        audit_file = test_workspace / "data" / "decision_audit_trail.jsonl"
        assert audit_file.exists()
        lines = [line.strip() for line in audit_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) >= 1
        last_rec = json.loads(lines[-1])
        assert last_rec["task_id"] == traj.task_id

    def test_11_desktop_gui_interaction_and_isolation_handling(self, closed_loop_runtime):
        """Case 11: Desktop task checks target window honestly and reports falsification if absent."""
        task = ComputerUseTask(
            goal="Inspect absent desktop application window",
            modality="DESKTOP",
            window_title="Nonexistent_Calculator_App_99",
            max_steps=1,
            max_duration_seconds=15.0
        )
        traj = closed_loop_runtime.execute_task(task)

        assert traj.modality == "DESKTOP"
        assert traj.status == "VERIFIED_FAILURE"
        assert "not found" in traj.error.lower()
        assert traj.final_verification["verification_status"] == "FALSIFIED"
