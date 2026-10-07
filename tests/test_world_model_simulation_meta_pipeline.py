"""Tests for Self Model (Part 8), Simulation (Part 13), Civilizational Knowledge (Part 14), Meta-Knowledge (Part 15), Cognitive Pipeline (Part 16), and Master OS Integration (Part 17)."""

import pytest
from alpha.world_model import (
    CognitiveWorldModel,
    SelfModel,
    WorldSimulationEngine,
    CivilizationalKnowledgeSystem,
    MetaKnowledgeEngine,
    CognitivePipeline,
    AgentEntity,
    ProjectEntity,
    TaskEntity,
    GoalEntity,
    EntityType,
    ToolEntity,
    BeliefEntity,
    RiskEntity,
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    RelationType,
)
from alpha.operating_system import AlphaOperatingSystem


def test_self_model_all_10_existential_questions():
    """Verify Alpha's Self Model provides answers to all 10 existential and operational questions."""
    cwm = CognitiveWorldModel()

    # Register sample entities
    a = AgentEntity(name="CodingAgent_01", role="coder")
    t = ToolEntity(name="fs_write_file", tool_name="fs_write_file")
    g = GoalEntity(name="Zero Bug Tolerance", objective="Ensure all contracts verified")
    task = TaskEntity(name="Refactor graph engine", status="in_progress")
    cwm.register_entity(a)
    cwm.register_entity(t)
    cwm.register_entity(g)
    cwm.register_entity(task)

    intro = cwm.introspect_self()
    assert "Alpha" in intro.who_am_i
    assert "Cognitive Operating System" in intro.what_am_i
    assert len(intro.what_can_i_do) > 0
    assert len(intro.what_can_i_not_do) > 0
    assert len(intro.what_are_my_goals) > 0
    assert len(intro.what_am_i_currently_doing) > 0
    assert len(intro.what_do_i_believe) > 0
    assert isinstance(intro.what_do_i_know, list)
    assert len(intro.what_do_i_not_know) > 0
    assert len(intro.what_should_i_learn_next) > 0


def test_world_simulation_engine_what_if_scenarios():
    """Verify Reality Sandbox simulations: Project failure, Agent removal, Belief falsification."""
    cwm = CognitiveWorldModel()

    p = ProjectEntity(name="BackendMigration")
    a = AgentEntity(name="DBAdminAgent", role="dba")
    t1 = TaskEntity(name="MigrateSchema", assignee_id=a.id)
    cwm.register_entity(p)
    cwm.register_entity(a)
    cwm.register_entity(t1)

    # 1. Simulate Project Failure
    sim_proj = cwm.simulation.simulate_project_failure(p.id)
    assert sim_proj.scenario_type == "project_failure"
    assert sim_proj.status == "completed"

    # 2. Simulate Agent Removal
    sim_agent = cwm.simulation.simulate_agent_removal(a.id)
    assert sim_agent.scenario_type == "agent_removal"
    assert len(sim_agent.affected_entities) >= 1  # Task t1 becomes unassigned

    # 3. Strategy Comparison (Plan A vs Plan B)
    strat = cwm.simulation.simulate_strategy_comparison(
        strategy_a={"success_prob": 0.95, "cost": 40},
        strategy_b={"success_prob": 0.70, "cost": 90}
    )
    assert strat["recommended_strategy"] == "strategy_a"


def test_civilizational_knowledge_publishing_and_inheritance():
    """Verify civilizational knowledge publishing, peer verification, citation, and inheritance."""
    cks = CivilizationalKnowledgeSystem()

    # Publish
    item = cks.publish(
        key="rule:subprocesses",
        title="Subprocess Guard",
        content="Always set timeout on child processes",
        author_id="agent_sec",
        author_role="security",
        tags=["core", "security"]
    )
    assert item.is_verified is False

    # Verify
    cks.verify(item.asset_id, verifier_id="agent_arch", approved=True)
    assert item.is_verified is True
    assert item.verification_score > 0.5

    # Cite
    cks.cite(item.key)
    assert item.citation_count == 1

    # Inherit for security role
    inherited = cks.inherit_for_role("security")
    assert len(inherited) == 1
    assert inherited[0].key == "rule:subprocesses"


def test_meta_knowledge_gap_detection_and_curiosity():
    """Verify gap detection, curiosity probe generation, and learning priority ranking."""
    cwm = CognitiveWorldModel()

    # Unmapped goal without tasks triggers a gap
    g = GoalEntity(name="Autonomous Deployment", objective="Deploy without human gate")
    cwm.register_entity(g)

    # Risk without mitigation triggers a gap
    r = RiskEntity(name="External API Outage", severity=0.8, mitigation_plan="")
    cwm.register_entity(r)

    overview = cwm.meta_knowledge.evaluate_epistemic_overview()
    assert overview["knowledge_gaps_count"] >= 2
    assert len(overview["top_learning_priorities"]) >= 2


def test_cognitive_transformation_pipeline_8_stages():
    """Verify end-to-end transformation: Observation -> Memory -> Knowledge -> Belief -> Concept -> Model -> Prediction -> Understanding."""
    cwm = CognitiveWorldModel()

    raw_data = {
        "source": "api_gateway_monitor",
        "subject": "AuthenticationService",
        "predicate": "maintains_p99_latency",
        "value": "< 120ms",
        "sample_count": 5000
    }

    result = cwm.process_observation_to_understanding(raw_data)
    assert result.observation is not None
    assert result.memory is not None
    assert result.knowledge["subject"] == "AuthenticationService"
    assert result.belief["confidence"] > 0.8
    assert "Concept" in result.concept["name"]
    assert result.model["cause"] is not None
    assert result.prediction["uncertainty_range"] is not None
    assert "AuthenticationService" in result.understanding["core_truth"]
    assert result.duration_ms >= 0.0


def test_alpha_operating_system_world_model_master_integration():
    """Verify AlphaOperatingSystem has world_model as single source of truth."""
    aos = AlphaOperatingSystem(db_path=":memory:")
    assert hasattr(aos, "world_model")
    assert isinstance(aos.world_model, CognitiveWorldModel)

    # Verify tools registered in world model
    tools_in_world = aos.world_model.ontology.get_by_type(EntityType.TOOL)
    assert len(tools_in_world) > 10

    # Self Introspection
    intro = aos.introspect_reality()
    assert "Alpha" in intro.who_am_i

    # Deliberation writes to world model
    verdict = aos.deliberate("Should system enable aggressive caching?")
    beliefs_in_world = aos.world_model.what_is_true(min_confidence=0.5)
    assert any("caching" in b["statement"].lower() for b in beliefs_in_world)

    # Live world state
    snap = aos.get_world_state()
    assert snap.summary()["tool_count"] > 10
