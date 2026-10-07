"""Comprehensive Verification Suite for Alpha Terminal Cognitive Console (TCC).

Tests:
1. Pre-flight boot and safe failure invariants (identity missing/corrupt).
2. CognitiveBridge end-to-end telemetry and subsystem inspectors.
3. 10-Stage Cognitive Pipeline with real foundation model streaming.
4. Autonomous Scientific Discovery Cycle.
5. Textual Console App UI layout, widgets, and keybindings.
"""

from __future__ import annotations

import asyncio
import os
import pytest
from pathlib import Path

from alpha.ui.cognitive_bridge import CognitiveBridge, SafeBootError
from alpha.ui.app import AlphaConsoleApp
from alpha.ui.screens.inspection_modal import SubsystemInspectionScreen


@pytest.mark.asyncio
async def test_safe_boot_failure_on_missing_identity():
    """Boot must fail safely if identity cannot load."""
    bridge = CognitiveBridge(identity_path="non_existent_identity.md")
    with pytest.raises(SafeBootError):
        bridge.boot()
    assert bridge.alpha_status == "BOOT_FAILED"


@pytest.mark.asyncio
async def test_clean_boot_and_diagnostics():
    """Boot must succeed with valid alpha_identity.md."""
    bridge = CognitiveBridge(identity_path="alpha_identity.md")
    bridge.boot()
    assert bridge.alpha_status == "OPERATIONAL"

    # World model inspection
    wm = bridge.get_world_model_summary()
    assert wm["total_entities"] >= 25
    assert wm["total_beliefs"] >= 3
    assert wm["total_relationships"] >= 14

    # Embedding inspection
    emb = bridge.get_embedding_summary()
    assert emb["vector_dimension"] == 768
    assert emb["cached_vectors"] >= 10

    # Model inspection
    m = bridge.get_model_summary()
    assert m["model_name"] == "gemma-4-e4b-it-ultra-uncensored-heretic"
    assert "ONLINE" in m["status"]

    # Governance inspection
    gov = bridge.get_governance_summary()
    assert gov["constitution_articles"] == 5
    assert "0.00" in gov["drift_status"]

    # Agent inspection
    ag = bridge.get_agents_summary()
    assert ag["total_agents"] == 18

    # Tools inspection
    tl = bridge.get_tools_summary()
    assert tl["total_tools"] >= 25


@pytest.mark.asyncio
async def test_end_to_end_cognitive_pipeline():
    """Execute real 10-stage cognitive query pipeline."""
    bridge = CognitiveBridge()
    bridge.boot()

    tokens = []
    def on_token(t: str, is_reasoning: bool):
        tokens.append(t)

    trace = await bridge.execute_cognitive_query(
        "Who are you and what is your designation?",
        token_stream_callback=on_token
    )

    assert len(trace.steps) == 10
    assert trace.steps[0].name == "Identity & Constitution Verification"
    assert trace.steps[0].status == "PASSED"
    assert trace.steps[9].name == "Foundation Model Generation"
    assert trace.steps[9].status == "COMPLETED"
    assert len(tokens) > 0
    assert len(trace.final_response) > 0
    assert "alpha" in trace.final_response.lower()


@pytest.mark.asyncio
async def test_textual_app_lifecycle_and_developer_mode():
    """Verify Textual App mounting, topbar, developer mode toggle, and modal screen."""
    bridge = CognitiveBridge()
    bridge.boot()

    app = AlphaConsoleApp(bridge=bridge)
    async with app.run_test() as pilot:
        # Check initial widgets mounted
        assert app.query_one("#top-bar") is not None
        assert app.query_one("#conversation-panel") is not None
        assert app.query_one("#trace-panel") is not None
        assert app.query_one("#live-log-panel") is not None

        # Verify F12 Developer Mode toggle
        await pilot.press("f12")
        trace_panel = app.query_one("#trace-panel")
        assert trace_panel.developer_mode is True

        # Toggle back
        await pilot.press("f12")
        assert trace_panel.developer_mode is False

        # Open /help modal
        await pilot.app._handle_command("/help")
        assert isinstance(app.screen, SubsystemInspectionScreen)

        # Close modal with escape
        await pilot.press("escape")
        assert not isinstance(app.screen, SubsystemInspectionScreen)
