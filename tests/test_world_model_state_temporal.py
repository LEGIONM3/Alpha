"""Tests for World State Engine (Part 6) and Temporal Reasoning (Part 7)."""

import pytest
import time
from alpha.world_model.temporal import (
    TimeEngine,
    LifecycleStage,
    LifecycleTracker,
    EventTimeline,
    BeliefTimeline,
    StateTimeline,
)
from alpha.world_model.state import (
    WorldStateSnapshot,
    WorldStateEngine,
)
from alpha.world_model.ontology import (
    OntologyRegistry,
    AgentEntity,
    ProjectEntity,
    TaskEntity,
    GoalEntity,
    ToolEntity,
    SkillEntity,
    DocumentEntity,
    ResourceEntity,
    RiskEntity,
    CapabilityEntity,
    BeliefEntity,
    PredictionEntity,
)
from alpha.world_model.epistemology import BeliefSystem, EvidenceRegistry, UncertaintyEngine, Evidence


def test_time_engine_ticks_and_pause():
    """Verify virtual clock advancement, discrete ticks, and pausing."""
    te = TimeEngine(real_time_start=1000.0)
    assert te.current_virtual_time == 1000.0
    assert te.current_tick == 0

    te.tick()
    assert te.current_tick == 1
    assert te.current_virtual_time == 1001.0

    te.advance_time(10.0)
    assert te.current_virtual_time == 1011.0
    assert te.current_tick >= 10

    te.pause()
    te.tick()
    assert te.current_tick >= 10  # Frozen while paused
    te.resume()


def test_lifecycle_tracking_birth_to_death():
    """Verify birth, growth, change, decay, and death transitions."""
    tracker = LifecycleTracker()
    eid = "entity_alpha"

    t1 = tracker.record_birth(eid, reason="instantiated")
    assert t1.to_stage == LifecycleStage.BIRTH
    assert tracker.get_current_stage(eid) == LifecycleStage.BIRTH

    t2 = tracker.record_growth(eid, reason="promoted")
    assert t2.to_stage == LifecycleStage.GROWTH

    t3 = tracker.record_change(eid, reason="refactored")
    assert t3.to_stage == LifecycleStage.CHANGE

    t4 = tracker.record_decay(eid, reason="deprecated")
    assert t4.to_stage == LifecycleStage.DECAY

    t5 = tracker.record_death(eid, reason="reaped")
    assert t5.to_stage == LifecycleStage.DEATH
    assert tracker.get_current_stage(eid) == LifecycleStage.DEATH

    history = tracker.get_history(eid)
    assert len(history) == 5


def test_belief_timeline_historical_queries():
    """Verify point-in-time answers to: What was true at time T?"""
    bt = BeliefTimeline()
    bid = "belief_01"

    # Time 100: True with conf 0.9
    bt.record_belief_state(bid, "Alpha is stable", 0.9, True, 100.0)
    # Time 200: Weakened to 0.4
    bt.record_belief_state(bid, "Alpha is stable", 0.4, True, 200.0)
    # Time 300: Dead
    bt.record_belief_state(bid, "Alpha is stable", 0.0, False, 300.0)

    # What was believed at T=150?
    at_150 = bt.what_was_believed_at(150.0, min_confidence=0.5)
    assert len(at_150) == 1
    assert at_150[0].confidence == 0.9

    # What was believed at T=250?
    at_250 = bt.what_was_believed_at(250.0, min_confidence=0.5)
    assert len(at_250) == 0  # Confidence 0.4 is below 0.5 threshold


def test_world_state_engine_12_dimensions():
    """Verify World State capturing all 12 dimensions, checkpointing, and projection."""
    ontology = OntologyRegistry()
    ev_reg = EvidenceRegistry()
    unc = UncertaintyEngine()
    beliefs = BeliefSystem(ev_reg, unc)
    wse = WorldStateEngine(ontology, beliefs)

    # Populate sample entities across all 12 types
    ontology.register(AgentEntity(name="A1"))
    ontology.register(ProjectEntity(name="P1"))
    ontology.register(TaskEntity(name="T1", status="pending"))
    ontology.register(GoalEntity(name="G1"))
    ontology.register(ToolEntity(name="Tool1", tool_name="tool_1"))
    ontology.register(SkillEntity(name="S1"))
    ontology.register(DocumentEntity(name="D1"))
    ontology.register(ResourceEntity(name="R1", capacity=100.0, current_load=20.0))
    ontology.register(RiskEntity(name="Risk1"))
    ontology.register(CapabilityEntity(name="Cap1"))
    ontology.register(PredictionEntity(name="Pred1", target_variable="metric", projected_value=1.0))

    ev = ev_reg.register(Evidence(statement="Baseline verified"))
    beliefs.form_belief("System operational", 0.95, evidence_ids=[ev.evidence_id])

    current = wse.get_current_state()
    summary = current.summary()
    assert summary["agent_count"] == 1
    assert summary["project_count"] == 1
    assert summary["task_count"] == 1
    assert summary["goal_count"] == 1
    assert summary["tool_count"] == 1
    assert summary["skill_count"] == 1
    assert summary["document_count"] == 1
    assert summary["resource_count"] == 1
    assert summary["risk_count"] == 1
    assert summary["capability_count"] == 1
    assert summary["belief_count"] == 1
    assert summary["prediction_count"] == 1

    # Checkpoint
    checkpoint = wse.capture_checkpoint(tag="cp1")
    assert checkpoint.state_mode == "historical"

    # Future Projection
    future = wse.project_future_state(horizon_seconds=3600.0)
    assert future.state_mode == "future"
    assert future.tasks[0]["status"] == "projected_completed"

    # Simulated Fork
    sim = wse.fork_simulated_state("sim_01", mutations={"fail_project_id": "P1"})
    assert sim.state_mode == "simulated"
