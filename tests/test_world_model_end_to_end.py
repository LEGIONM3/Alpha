"""End-to-End integration tests for Cognitive World Model."""

import pytest
from alpha.world_model import (
    CognitiveWorldModel,
    AgentEntity,
    ProjectEntity,
    TaskEntity,
    GoalEntity,
    ToolEntity,
    BeliefEntity,
    ConceptEntity,
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    RelationType,
    LifecycleState,
)


def test_end_to_end_world_model_initialization():
    """Verify default initialization seeds foundational goal, project, belief, and graph links."""
    cwm = CognitiveWorldModel()
    assert cwm.ontology.count() >= 2
    assert cwm.graph.node_count() >= 3
    assert cwm.graph.edge_count() >= 2

    # Verify foundational belief is registered
    beliefs = cwm.what_is_true(min_confidence=0.9)
    assert len(beliefs) >= 1
    assert "deterministic verification" in beliefs[0]["statement"].lower()


def test_end_to_end_entity_graph_cross_sync():
    """Verify entities registered in ontology are automatically synchronized as graph nodes and lifecycle tracked."""
    cwm = CognitiveWorldModel()

    coder = AgentEntity(name="Coder_Apex", role="coder")
    tool = ToolEntity(name="pytest_tool", tool_name="pytest_tool")
    task = TaskEntity(name="RunTestTask")

    cwm.register_entity(coder)
    cwm.register_entity(tool)
    cwm.register_entity(task)

    assert cwm.graph.has_node(coder.id)
    assert cwm.graph.has_node(tool.id)
    assert cwm.graph.has_node(task.id)

    # Establish relations
    cwm.relate(coder.id, tool.id, RelationType.USES)
    cwm.relate(coder.id, task.id, RelationType.DEPENDS_ON)

    out_edges = cwm.graph.get_out_edges(coder.id)
    assert len(out_edges) == 2


def test_end_to_end_causal_counterfactual_cascade():
    """Verify multi-step causal cascade and counterfactual simulation."""
    cwm = CognitiveWorldModel()

    # Chain: A -> B -> C
    cwm.register_causal_link("ServiceA", "ServiceB", strength=0.9, mechanism="RPC")
    cwm.register_causal_link("ServiceB", "ServiceC", strength=0.85, mechanism="EventBus")

    # Impact prediction
    impact = cwm.causal.predict_change_impact("ServiceA", severity=1.0)
    assert impact["blast_radius"] == 2
    assert impact["affected_nodes"][0]["node_id"] == "ServiceB"

    # Counterfactual: without ServiceA, does ServiceC occur?
    cf = cwm.causal.evaluate_counterfactual("ServiceA", "ServiceC")
    assert cf["effect_occurs"] is False
    assert cf["causal_necessity"] == "necessary"


def test_end_to_end_belief_strengthen_and_decay_cycle():
    """Verify full lifecycle of belief: evidence arrival -> strengthening -> decay -> death."""
    cwm = CognitiveWorldModel()

    ev1 = cwm.record_evidence("Empirical benchmark 1 passed", EvidencePolarity.SUPPORTING, EvidenceStrength.STRONG)
    b = cwm.form_belief("Architecture scale holds up to 10k agents", 0.60, evidence_ids=[ev1.evidence_id])

    # Strengthen with second evidence
    ev2 = cwm.record_evidence("Empirical benchmark 2 passed", EvidencePolarity.SUPPORTING, EvidenceStrength.STRONG, claim_id=b.belief_id)
    assert b.confidence > 0.65

    # Decay over virtual time
    cwm.time_engine.advance_time(3600.0)  # 1 hour
    b.decay_rate = 0.08
    cwm.beliefs.age_beliefs(elapsed_seconds=3600.0)
    assert b.confidence < 0.60

    # Fatal contradiction leads to death
    ev_contra = cwm.record_evidence("Memory leak observed at 5k agents", EvidencePolarity.CONTRADICTING, EvidenceStrength.STRONG, claim_id=b.belief_id)
    assert b.confidence == 0.0
    assert b.lifecycle_state == LifecycleState.DEAD


def test_end_to_end_reality_state_checkpoints_and_diffs():
    """Verify multi-temporal state capture and historical state retrieval."""
    cwm = CognitiveWorldModel()

    # T1
    snap1 = cwm.capture_world_state(tag="t1")
    t1_time = snap1.timestamp

    # Add task
    t = TaskEntity(name="Critical Patch", status="pending")
    cwm.register_entity(t)

    # T2
    snap2 = cwm.capture_world_state(tag="t2")

    assert snap2.summary()["task_count"] == snap1.summary()["task_count"] + 1

    # Query historical state at T1
    historical = cwm.world_state.get_historical_state(t1_time)
    assert historical is not None
    assert historical.summary()["task_count"] == snap1.summary()["task_count"]


def test_end_to_end_self_model_introspection_query():
    """Verify that Alpha answers all 10 self-reflective questions with structured depth."""
    cwm = CognitiveWorldModel()
    intro = cwm.introspect_self()

    assert "Project Alpha" in intro.who_am_i
    assert "Reality-Based Intelligence" in intro.who_am_i or "Cognitive" in intro.what_am_i
    assert len(intro.what_can_i_do) >= 1
    assert len(intro.what_can_i_not_do) >= 4
    assert len(intro.what_are_my_goals) >= 1
    assert len(intro.what_do_i_believe) >= 1
    assert len(intro.what_do_i_not_know) >= 1
    assert len(intro.what_should_i_learn_next) >= 1


def test_end_to_end_concept_taxonomy_and_discovery():
    """Verify concept discovery and taxonomic tree construction."""
    cwm = CognitiveWorldModel()

    t1 = ToolEntity(name="MySQL", tool_name="mysql", attributes={"category": "rdbms"})
    t2 = ToolEntity(name="PostgreSQL", tool_name="postgresql", attributes={"category": "rdbms"})
    cwm.register_entity(t1)
    cwm.register_entity(t2)

    concept = cwm.concept_discovery.form_concept_from_exemplars(
        concept_name="Relational Database Systems",
        definition="Structured SQL-based relational storage.",
        exemplar_entities=[t1, t2]
    )
    cwm.register_entity(concept)

    assert concept.name == "Relational Database Systems"
    assert len(concept.exemplar_ids) == 2


def test_end_to_end_distillation_pipeline_integrity():
    """Verify 1,000 memories distill into 10 concepts preserving provenance."""
    cwm = CognitiveWorldModel()

    memories = [
        {"id": f"m_{i}", "content": f"Memory item on subsystem {i % 10}", "tag": f"sub_{i % 5}"}
        for i in range(1000)
    ]
    concepts = cwm.distillation.distill_memories_to_concepts(memories, target_concept_count=10)
    assert len(concepts) == 10
    total_exemplars = sum(len(c.exemplar_ids) for c in concepts)
    assert total_exemplars > 20


def test_end_to_end_civilizational_knowledge_inheritance():
    """Verify civilizational knowledge publishing, rating, and role-based inheritance."""
    cwm = CognitiveWorldModel()

    asset = cwm.civilizational_knowledge.publish(
        key="standard:api_circuit_breaker",
        title="Circuit Breaker Standard",
        content="Fail open with cached response after 3 consecutive 5xx errors.",
        author_id="architect_agent",
        author_role="architect",
        tags=["core", "architecture"],
        auto_verify=True
    )

    inherited = cwm.civilizational_knowledge.inherit_for_role("architect")
    assert any(a.key == "standard:api_circuit_breaker" for a in inherited)


def test_end_to_end_simulation_sandbox_isolation():
    """Verify that simulating a severe failure in reality sandbox leaves live world state untouched."""
    cwm = CognitiveWorldModel()

    proj = ProjectEntity(name="CoreInfrastructure")
    cwm.register_entity(proj)

    # Pre-simulation check
    assert cwm.ontology.get(proj.id).lifecycle_state == LifecycleState.ACTIVE

    # Run project failure simulation
    sim_outcome = cwm.simulation.simulate_project_failure(proj.id)
    assert sim_outcome.scenario_type == "project_failure"

    # Post-simulation check: live state must remain ACTIVE!
    assert cwm.ontology.get(proj.id).lifecycle_state == LifecycleState.ACTIVE
