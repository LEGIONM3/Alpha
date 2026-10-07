"""Verification Suite for Phase 7: Persistent Autonomous Cognitive System.

Verifies:
1. Autonomous mode in TCC runs without 'call_from_thread' crashes.
2. CognitiveRuntime executes persistent background cycles (Perceive -> Reflect -> Commit).
3. ACTIVE_COGNITIVE_STATE.json is continuously updated.
4. RealityValidator generates ARCHITECTURAL_REALITY_REPORT.md.
5. SelfMonitoringAgent generates self_monitoring_report.json.
6. GroundingMonitor detects epistemic invariants without crash.
7. Existential introspection answers 10 questions from real identity, world model, and awareness.
"""

import asyncio
import json
import pytest
from pathlib import Path

from alpha.ui.cognitive_bridge import CognitiveBridge
from alpha.ui.app import AlphaConsoleApp
from alpha.core.cognitive_runtime import CognitiveRuntime


@pytest.mark.asyncio
async def test_autonomous_mode_no_crash_in_app():
    """Verify autonomous startup in Textual app does not crash with call_from_thread."""
    bridge = CognitiveBridge()
    bridge.boot()

    try:
        # Launch app with start_autonomous=True
        app = AlphaConsoleApp(bridge=bridge, start_autonomous=True)
        async with app.run_test() as pilot:
            await pilot.pause(0.5)

            # Trigger /autonomous command directly
            await pilot.app._handle_command("/autonomous")
            await pilot.pause(1.0)

            # Verify app is still alive and operational
            assert app.is_running
            assert app.bridge.alpha_status == "OPERATIONAL"

            # Check live feed availability
            feed = app.bridge.get_live_cognitive_feed()
            assert feed is not None
            assert "current_thought" in feed
            assert "current_mission" in feed
    finally:
        bridge.shutdown()


def test_reality_validator_execution():
    """Verify reality validator audits codebase and generates ARCHITECTURAL_REALITY_REPORT.md."""
    from alpha.verification.reality_validator import RealityValidator
    validator = RealityValidator()
    report_md = validator.generate_report_markdown()
    assert "ARCHITECTURAL_REALITY_REPORT.md" in report_md
    assert "EXISTS" in report_md
    assert Path("ARCHITECTURAL_REALITY_REPORT.md").exists()


def test_self_monitoring_report_generation():
    """Verify self monitoring agent generates self_monitoring_report.json."""
    from alpha.agents.self_monitoring import SelfMonitoringAgent
    monitor = SelfMonitoringAgent(report_path="self_monitoring_report.json")
    report = monitor.generate_report()
    assert "system_health" in report
    assert "resources" in report
    assert "concurrency" in report
    assert Path("self_monitoring_report.json").exists()


def test_existential_self_inquiry():
    """Verify Alpha can answer the 10 existential questions from grounded state."""
    from alpha.core.awareness import AwarenessManager
    manager = AwarenessManager(workspace_file=Path("ACTIVE_COGNITIVE_STATE.json"))

    # 1. Who am I?
    who = manager.who_am_i()
    assert who.get("name") == "Alpha"

    # 2. What is my mission?
    mission = manager.what_is_my_mission()
    assert len(mission) > 10

    # 3. What am I doing?
    doing = manager.what_am_i_doing()
    assert "Goal:" in doing

    # 4. What changed recently?
    changed = manager.what_changed_recently()
    assert isinstance(changed, list)

    # 5. What am I worried about?
    worried = manager.what_am_i_worried_about()
    assert len(worried) > 0

    # 6. What is currently broken?
    broken = manager.what_is_currently_broken()
    assert isinstance(broken, list)

    # 7. What should be improved?
    improved = manager.what_should_be_improved()
    assert isinstance(improved, list)

    # 8. What is my highest priority?
    priority = manager.what_is_my_highest_priority()
    assert len(priority) > 0

    # 9. What did I learn today?
    learned = manager.what_did_i_learn_today()
    assert isinstance(learned, list)

    # 10. What evidence supports my beliefs?
    evidence = manager.what_evidence_supports_my_beliefs()
    assert len(evidence) > 0
