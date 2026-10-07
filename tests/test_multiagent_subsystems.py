"""Test Suite for Project Alpha Phase 3 Multi-Agent Subsystems (Parts 1 to 10)."""

import pytest
import time
from alpha.agents import (
    AgentRuntime,
    AgentMessage,
    MessageType,
    MessagePriority,
    AgentRole,
    AgentStatus,
    CouncilDeliberationSystem,
    CompetitiveReasoningEngine,
    DynamicTeam,
    TeamManager,
    SharedKnowledgeLayer,
    SkillLibrary,
    AgentEvolutionEngine,
    MetaLearningFramework,
    ROLE_TO_CLASS_MAP,
)
from alpha.agents.types import (
    ResearchAgent,
    PlannerAgent,
    ArchitectAgent,
    BuilderAgent,
    CodingAgent,
    TestingAgent,
    ValidationAgent,
    CriticAgent,
    RiskAgent,
    DirectorAgent,
    SecurityAgent,
    OptimizationAgent,
    AnalyticsAgent,
    DocumentationAgent,
    ReflectionAgent,
    MetaLearningAgent,
    MemoryAgent,
    KnowledgeAgent
)

def test_communication_network_integrity_and_priority():
    """Verify cryptographic integrity, priority queuing, and message bus delivery."""
    runtime = AgentRuntime()
    mbox_a = runtime.bus.register_agent("agent_a", "researcher")
    mbox_b = runtime.bus.register_agent("agent_b", "planner")

    # Send LOW priority message
    msg_low = AgentMessage(
        sender_id="agent_a",
        sender_role="researcher",
        recipient_id="agent_b",
        message_type=MessageType.PROPOSAL,
        priority=MessagePriority.LOW,
        payload={"topic": "background"}
    )
    assert msg_low.verify_integrity() is True
    runtime.bus.send(msg_low)

    # Send CRITICAL priority message
    msg_crit = AgentMessage(
        sender_id="agent_a",
        sender_role="researcher",
        recipient_id="agent_b",
        message_type=MessageType.ESCALATION,
        priority=MessagePriority.CRITICAL,
        payload={"alert": "urgent"}
    )
    assert msg_crit.verify_integrity() is True
    runtime.bus.send(msg_crit)

    # Check that priority queue pops CRITICAL before LOW
    first = mbox_b.pop_next()
    assert first is not None
    assert first.priority == MessagePriority.CRITICAL
    assert first.payload["alert"] == "urgent"

    second = mbox_b.pop_next()
    assert second is not None
    assert second.priority == MessagePriority.LOW

    # Verify audit trail
    audit = runtime.bus.get_audit_trail(sender_id="agent_a")
    assert len(audit) == 2
    runtime.shutdown()

def test_agent_lifecycle_and_all_18_archetypes():
    """Verify all 18 agent types spawn, execute domain logic, and have valid specifications."""
    runtime = AgentRuntime()

    assert len(ROLE_TO_CLASS_MAP) == 18

    for role, cls in ROLE_TO_CLASS_MAP.items():
        agent = runtime.lifecycle.spawn(cls, name=f"Test_{role.value}", role=role)
        assert agent.status == AgentStatus.IDLE
        assert agent.role == role
        assert agent.spec.role_name == role.value
        assert len(agent.spec.purpose) > 0
        assert len(agent.spec.success_metrics) > 0
        assert len(agent.spec.failure_modes) > 0
        assert len(agent.spec.communication_rules) > 0

        # Test execution
        task_out = agent.execute_task({"goal": f"Test task for {role.value}"})
        assert isinstance(task_out, dict)
        assert task_out.get("success") is True

    assert runtime.registry.count() == 18

    # Test suspension and resumption
    first_agent = runtime.registry.get_all()[0]
    aid = first_agent.agent_id
    assert runtime.lifecycle.suspend(aid) is True
    assert first_agent.status == AgentStatus.SUSPENDED
    assert runtime.lifecycle.resume(aid) is True
    assert first_agent.status == AgentStatus.IDLE

    # Test monitoring and versioning
    mon = runtime.lifecycle.monitor(aid)
    assert mon is not None
    assert mon["role"] == first_agent.role.value
    upgraded = runtime.lifecycle.upgrade_version(aid, "2.0.0")
    assert upgraded.identity.version == "2.0.0"
    assert upgraded.identity.generation == 2

    runtime.shutdown()

def test_council_deliberation_system():
    """Verify multi-agent deliberation: research, planning, critique, risk, and consensus scoring."""
    runtime = AgentRuntime()
    council = CouncilDeliberationSystem(runtime)

    question = "Design an autonomous fault-tolerant distributed cache"
    verdict = council.deliberate(question)

    assert verdict.question == question
    assert "primary_strategy" in verdict.selected_plan
    assert len(verdict.alternative_plans) >= 2
    assert len(verdict.counterarguments) >= 1
    assert len(verdict.identified_risks) >= 1
    assert 0.0 <= verdict.evidence_score <= 1.0
    assert 0.0 <= verdict.confidence_score <= 1.0
    assert verdict.consensus_status in ("UNANIMOUS", "SUPERMAJORITY", "DIVIDED")
    assert verdict.deliberation_time_ms > 0

    runtime.shutdown()

def test_competitive_reasoning_adversarial_rounds():
    """Verify Red Team attacks and Blue Team defenses produce hardened solution."""
    runtime = AgentRuntime()
    adversarial = CompetitiveReasoningEngine(runtime)

    target_sol = {
        "name": "MicroserviceAuth",
        "description": "Token verification endpoint",
        "parameters": {"token_ttl": 3600}
    }

    result = adversarial.execute_adversarial_session(target_sol, num_rounds=2)

    assert result.original_target == "MicroserviceAuth"
    assert result.rounds_executed == 2
    assert result.flaws_uncovered > 0
    assert result.flaws_patched > 0
    assert result.final_robustness >= result.initial_robustness
    assert len(result.hardened_solution.get("safeguards", [])) >= 2
    assert result.verdict == "HARDENED_AND_VERIFIED"

    runtime.shutdown()

def test_dynamic_project_teams_lifecycle():
    """Verify dynamic team formation, collaborative execution, and clean dissolution."""
    runtime = AgentRuntime()
    tm = TeamManager(runtime)

    team = tm.form_coding_team(task_name="RateLimiterProject", mission_goal="Implement Token Bucket Rate Limiter")
    assert team.status == "FORMED"
    assert len(team.members) >= 5

    exec_result = team.execute_workflow({"target_path": "rate_limiter.py"})
    assert exec_result["success"] is True
    assert exec_result["steps_executed"] >= 6
    assert "final_code" in exec_result
    assert team.status == "COMPLETED"

    dissolve_summary = tm.dissolve_team(team.team_id)
    assert dissolve_summary is not None
    assert dissolve_summary["status"] == "DISSOLVED"
    assert len(tm.active_teams) == 0

    runtime.shutdown()

def test_knowledge_society_publishing_verification_inheritance():
    """Verify shared knowledge layer, publishing, ranking, and role inheritance."""
    kl = SharedKnowledgeLayer()
    initial_count = kl.total_count()
    assert initial_count >= 2

    # Publish new discovery
    item = kl.publish(
        key="pattern:circuit_breaker_3_state",
        title="Three State Circuit Breaker",
        content="Closed, Open, Half-Open state machine prevents cascading outages.",
        author_id="researcher_01",
        author_role="researcher",
        tags=["resilience", "patterns"]
    )
    assert item.is_verified is False

    # Verify discovery
    assert kl.verify_knowledge(item.item_id, verifier_id="critic_01", verifier_role="critic", approve=True) is True
    assert item.is_verified is True

    # Record citations
    kl.cite_knowledge(item.key)
    kl.cite_knowledge(item.key)
    assert item.citation_count == 2
    assert item.compute_ranking() > 0.6

    # Test inheritance for coder role
    inherited = kl.inherit_for_role("coder")
    assert len(inherited) >= 2  # includes core axioms

def test_skill_system():
    """Verify Skill creation, composition, execution, validation, and improvement."""
    lib = SkillLibrary()
    
    # Discovery
    skills = lib.registry.search()
    assert len(skills) >= 2

    # Compose custom skill
    custom_skill = lib.composer.compose_skill(
        name="custom_security_scan",
        description="Inspect code AST, scan forbidden tokens, and emit security flag.",
        steps=[
            {"step": 1, "action": "ast_parse"},
            {"step": 2, "action": "token_filter"},
            {"step": 3, "action": "emit_flag"}
        ],
        tags=["security", "custom"]
    )
    assert custom_skill.is_validated is True

    # Execute skill
    exec_res = lib.executor.execute(custom_skill, {"code": "def hello(): pass"})
    assert exec_res["success"] is True
    assert exec_res["steps_completed"] == 3
    assert custom_skill.execution_count == 1

    # Improve skill
    improved = lib.composer.improve_skill(
        existing_name="custom_security_scan",
        new_steps=[
            {"step": 1, "action": "ast_parse"},
            {"step": 2, "action": "token_filter"},
            {"step": 3, "action": "sandbox_dryrun"},
            {"step": 4, "action": "emit_flag"}
        ]
    )
    assert improved is not None
    assert improved.version == "1.1.0"
    assert lib.registry.get("custom_security_scan").version == "1.1.0"

    # Retire skill
    assert lib.registry.retire_skill("custom_security_scan") is True
    assert lib.registry.get("custom_security_scan").status == "RETIRED"

def test_agent_evolution_and_meta_learning():
    """Verify performance ranking, evolution proposals, and operational rule mining."""
    runtime = AgentRuntime()
    # Spawn two agents
    a1 = runtime.lifecycle.spawn(CodingAgent, name="CoderA", role=AgentRole.CODER)
    a2 = runtime.lifecycle.spawn(CodingAgent, name="CoderB", role=AgentRole.CODER)

    # Simulate performance difference
    a1.record_execution(success=True, latency_ms=15.0)
    a1.record_execution(success=True, latency_ms=18.0)
    a2.record_execution(success=False, latency_ms=90.0)
    a2.record_execution(success=False, latency_ms=95.0)
    a2.record_execution(success=False, latency_ms=110.0)

    evolution = AgentEvolutionEngine(runtime)
    leaderboard = evolution.rank_society()
    assert len(leaderboard) >= 2
    assert leaderboard[0].agent_id == a1.agent_id
    assert leaderboard[0].fitness_score > leaderboard[1].fitness_score

    # Underperformer detection
    proposals = evolution.scan_for_underperformers(fitness_threshold=50.0)
    assert len(proposals) >= 1
    prop = proposals[0]
    assert prop.target_agent_id == a2.agent_id

    # Execute proposal
    res = evolution.execute_proposal(prop.proposal_id)
    assert res["success"] is True

    # Meta-Learning Framework
    meta = MetaLearningFramework()
    meta.record_failure("file_write", "FilePermissionError", {"path": "/etc/shadow"})
    meta.record_success("sandbox_run", {"code_len": 50}, latency_ms=12.0)
    
    rules = meta.generate_operational_rules()
    assert len(rules) >= 1
    active_rules = meta.get_active_rules()
    assert len(active_rules) >= 2  # including seeded core rule

    runtime.shutdown()
