"""Tests for Universal Ontology Engine (Part 1)."""

import pytest
from alpha.world_model.ontology import (
    Entity,
    EntityType,
    LifecycleState,
    EntityVersion,
    ProvenanceRecord,
    PersonEntity,
    OrganizationEntity,
    ProjectEntity,
    AgentEntity,
    SkillEntity,
    ToolEntity,
    TaskEntity,
    GoalEntity,
    MemoryEntity,
    ExperienceEntity,
    DocumentEntity,
    ConceptEntity,
    RuleEntity,
    BeliefEntity,
    ObservationEntity,
    EventEntity,
    CapabilityEntity,
    ResourceEntity,
    RiskEntity,
    DecisionEntity,
    HypothesisEntity,
    TheoryEntity,
    PredictionEntity,
    SimulationEntity,
    RelationshipEntity,
    ENTITY_CLASS_MAP,
    OntologyRegistry,
    OntologyValidator,
    OntologyVersionManager,
    OntologyEvolutionEngine,
)


def test_all_25_entity_types_instantiate():
    """Verify all 25 canonical entity types can be properly created and have expected types."""
    assert len(ENTITY_CLASS_MAP) == 25

    instantiations = [
        PersonEntity(name="Ada Lovelace", email="ada@alpha.ai"),
        OrganizationEntity(name="Alpha Core", mission="Cognitive AGI"),
        ProjectEntity(name="Cognitive World Model"),
        AgentEntity(name="ResearchAgent_01", role="researcher"),
        SkillEntity(name="ASTAnalysis", domain="coding"),
        ToolEntity(name="fs_read_file", tool_name="fs_read_file"),
        TaskEntity(name="Index codebase"),
        GoalEntity(name="Reality Grounding", objective="Eliminate hallucination"),
        MemoryEntity(name="Mem_01", layer="long_term"),
        ExperienceEntity(name="Exp_01", task_context="debugging", action_taken="patch", reward=1.0),
        DocumentEntity(name="Architecture RFC", content="# RFC"),
        ConceptEntity(name="Data Storage", definition="Systems that persist state"),
        RuleEntity(name="Rule_01", condition="high_latency", action="throttle"),
        BeliefEntity(name="Belief_01", statement="Sandboxing guarantees isolation", evidence_ids=["ev_1"]),
        ObservationEntity(name="Obs_01", source="metrics"),
        EventEntity(name="Ev_01", event_type="agent_spawned"),
        CapabilityEntity(name="Cap_PythonAST", category="coding"),
        ResourceEntity(name="ComputeCluster", resource_type="gpu", capacity=8.0),
        RiskEntity(name="OutOfMemoryRisk", severity=0.7, likelihood=0.3),
        DecisionEntity(name="Dec_AdoptWorldModel", chosen_option="Option A"),
        HypothesisEntity(name="Hyp_GraphAdvantage", premise="Graph outperforms flat vector"),
        TheoryEntity(name="Theory_EpistemicGrounding", axioms=["No orphan beliefs"]),
        PredictionEntity(name="Pred_Convergence", target_variable="loss", projected_value=0.01),
        SimulationEntity(name="Sim_ChaosTest", parameters={"fault_rate": 0.1}),
        RelationshipEntity(name="Rel_01", source_id="a", target_id="b", relation_type="causes"),
    ]

    assert len(instantiations) == 25
    for ent in instantiations:
        assert ent.id is not None
        assert ent.importance >= 0.0 and ent.importance <= 1.0
        assert ent.confidence >= 0.0 and ent.confidence <= 1.0
        assert ent.lifecycle_state == LifecycleState.ACTIVE


def test_ontology_versioning_and_rollback():
    """Test version snapshots, diffs, and rollback."""
    mgr = OntologyVersionManager()
    agent = AgentEntity(name="AgentAlpha", role="planner", importance=0.6)

    # Initial snapshot
    v1 = mgr.record_version(agent, summary="Initial deployment")
    assert agent.version == 2

    # Mutate agent
    agent.role = "lead_architect"
    agent.importance = 0.95
    v2 = mgr.record_version(agent, summary="Promotion to architect")
    assert agent.version == 3

    # Diff
    diff = mgr.compute_diff(agent, 1, 2)
    assert diff["entity_id"] == agent.id
    assert "role" in diff["modified"]
    assert diff["modified"]["role"]["from"] == "planner"
    assert diff["modified"]["role"]["to"] == "lead_architect"

    # Rollback to v1
    success = mgr.rollback(agent, 1)
    assert success is True
    assert agent.role == "planner"
    assert agent.importance == 0.6


def test_ontology_validator_constraints():
    """Test validation bounds and rejection of invalid entities."""
    validator = OntologyValidator()

    # Valid entity
    t = TaskEntity(name="Clean cache", importance=0.8, confidence=0.9)
    res = validator.validate_entity(t)
    assert res.is_valid is True

    # Invalid importance
    t_invalid = TaskEntity(name="Bad metric")
    t_invalid.importance = 1.8
    res = validator.validate_entity(t_invalid)
    assert res.is_valid is False
    assert any("Importance" in err for err in res.errors)

    # Orphan belief without evidence or source
    b_orphan = BeliefEntity(name="Orphan", statement="Sun is blue", evidence_ids=[])
    b_orphan.provenance.source_ids = []
    res = validator.validate_entity(b_orphan)
    assert res.is_valid is False
    assert any("orphan" in err.lower() for err in res.errors)


def test_ontology_evolution_and_merging():
    """Test merging secondary entities into primary entity and concept abstraction."""
    engine = OntologyEvolutionEngine()

    e1 = ToolEntity(name="ToolA", tool_name="tool_a", importance=0.5, confidence=0.8)
    e1.attributes = {"speed": "fast"}
    e2 = ToolEntity(name="ToolB", tool_name="tool_b", importance=0.7, confidence=0.6)
    e2.attributes = {"memory": "low"}

    merged = engine.merge_entities(e1, e2, merged_name="CombinedTool")
    assert merged.name == "CombinedTool"
    assert merged.importance == 0.7
    assert merged.confidence == 0.7
    assert merged.attributes["speed"] == "fast"
    assert merged.attributes["memory"] == "low"
    assert e2.lifecycle_state == LifecycleState.DEPRECATED
    assert e2.id in merged.provenance.source_ids

    # Concept abstraction
    c = engine.abstract_to_concept([e1, e2], "OptimizedTooling", "Fast and low-memory tool cluster")
    assert c.name == "OptimizedTooling"
    assert len(c.exemplar_ids) == 2


def test_ontology_registry_operations():
    """Test registry CRUD, indexing by type, search, and removal."""
    registry = OntologyRegistry()

    p = ProjectEntity(name="Apollo", importance=0.9)
    g = GoalEntity(name="Land on Moon", importance=1.0)
    registry.register(p)
    registry.register(g)

    assert registry.count() == 2
    assert registry.get(p.id).name == "Apollo"
    assert registry.get_by_name("apollo").id == p.id

    projects = registry.get_by_type(EntityType.PROJECT)
    assert len(projects) == 1
    assert projects[0].id == p.id

    search_res = registry.search("Moon")
    assert len(search_res) == 1
    assert search_res[0].id == g.id

    # Remove
    assert registry.remove(g.id) is True
    assert registry.get(g.id) is None
    assert registry.count() == 1
