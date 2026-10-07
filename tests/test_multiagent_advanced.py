"""Test Suite for Project Alpha Phase 3 Advanced Subsystems (Parts 11 to 16)."""

import pytest
import time
from alpha.agents import (
    AgentRuntime,
    AgentRole,
    AgentStatus,
    CivilizationMemorySystem,
    RetentionPolicy,
    SystemObserver,
    ExecutionMarketplace,
    ResourceEconomy,
    ChangeGovernanceSystem,
    VirtualSandboxWorld,
    ROLE_TO_CLASS_MAP,
)
from alpha.agents.types import CodingAgent, TestingAgent, AnalyticsAgent

def test_memory_civilization_9_layers():
    """Verify all 9 memory layers, retention policies, compression, and version snapshots."""
    mem = CivilizationMemorySystem()

    # 1. Short Term
    mem.short_term.store("scratch_1", "temporary computation", tags=["temp"], importance=0.2)
    assert mem.short_term.retrieve("scratch_1") == "temporary computation"

    # 2. Working
    mem.working.store("var_a", 42, tags=["calc"])
    assert mem.working.retrieve("var_a") == 42

    # 3. Project
    mem.project.store("team_task", "implement token bucket", tags=["sprint_1"])
    assert mem.project.retrieve("team_task") == "implement token bucket"

    # 4. Long Term
    mem.long_term.store("user_pref", "prefers python 3.12", tags=["profile"], importance=0.8)
    assert mem.long_term.retrieve("user_pref") == "prefers python 3.12"

    # 5. Knowledge
    mem.knowledge.store("concept_rag", "Retrieval Augmented Generation", tags=["rag"], importance=0.9)
    assert mem.knowledge.retrieve("concept_rag") == "Retrieval Augmented Generation"

    # 6. Collective
    mem.collective.store("axiom_1", "All code requires sandbox testing", tags=["consensus"], importance=1.0)
    assert mem.collective.retrieve("axiom_1") == "All code requires sandbox testing"

    # 7. Agent
    mem.agent.store("agent_history", "completed 10 tasks", tags=["trajectory"])
    assert mem.agent.retrieve("agent_history") == "completed 10 tasks"

    # 8. Reflection
    mem.reflection.store("reflection_001", "pre-validation saved 80% latency", tags=["lesson"], importance=0.85)
    assert mem.reflection.retrieve("reflection_001") == "pre-validation saved 80% latency"

    # 9. Experience
    mem.experience.store("exp_001", {"action": "run_sandbox", "reward": 1.0}, tags=["reinforce"])
    assert mem.experience.retrieve("exp_001")["reward"] == 1.0

    assert mem.total_entries() == 9

    # Query with tags and importance
    results = mem.long_term.query(tag="profile", min_importance=0.5)
    assert len(results) == 1

    # Compression test
    compressed = mem.short_term.compress()
    assert isinstance(compressed, int)

    # Snapshot version control
    snap = mem.collective.create_snapshot()
    assert snap["name"] == "collective"
    assert "axiom_1" in snap["entries"]

def test_system_observer_and_telemetry():
    """Verify observer telemetry snapshots, latency percentiles, and improvement reports."""
    runtime = AgentRuntime()
    # Spawn agents and simulate activity
    a1 = runtime.lifecycle.spawn(CodingAgent, name="ObsCoder", role=AgentRole.CODER)
    a2 = runtime.lifecycle.spawn(TestingAgent, name="ObsTester", role=AgentRole.TESTER)

    a1.record_execution(success=True, latency_ms=12.0)
    a1.record_execution(success=True, latency_ms=25.0)
    a2.record_execution(success=True, latency_ms=40.0)

    observer = SystemObserver(runtime)
    snap = observer.capture_snapshot()

    assert snap.total_agents >= 2
    assert snap.total_tasks_completed == 3
    assert snap.avg_latency_ms > 0
    assert snap.p50_latency_ms > 0

    report = observer.generate_improvement_report()
    assert report.health_status in ("OPTIMAL", "CONGESTED", "DEGRADED")
    assert len(report.recommendations) >= 1

    runtime.shutdown()

def test_execution_marketplace_economy_and_auction():
    """Verify job posting, bidding, auction selection, and escrow settlement."""
    runtime = AgentRuntime()
    w1 = runtime.lifecycle.spawn(CodingAgent, name="Worker1", role=AgentRole.CODER)
    w2 = runtime.lifecycle.spawn(CodingAgent, name="Worker2", role=AgentRole.CODER)

    w1.record_execution(success=True, latency_ms=10.0, reward=2.0)

    market = ExecutionMarketplace(runtime)
    job = market.post_job(
        title="Synthesize quicksort function",
        payload={"spec": "quicksort algorithm", "language": "python"},
        required_role=AgentRole.CODER,
        budget_credits=100.0
    )
    assert job.status == "OPEN"
    assert job.escrow_credits == 100.0

    # Auction and execute
    result = market.auction_and_execute(job.job_id)
    assert result["success"] is True
    assert result["winning_agent"] in ("Worker1", "Worker2")
    assert result["worker_balance"] > market.economy.initial_balance
    assert job.status == "COMPLETED"

    runtime.shutdown()

def test_change_governance_and_rollback():
    """Verify governance pipeline: proposal, review, canary test, approval, deploy, and rollback."""
    gov = ChangeGovernanceSystem()

    # 1. Propose
    prop = gov.submit_proposal(
        proposer_id="agent_architect",
        proposer_role="architect",
        title="Upgrade max concurrency limit",
        description="Raise thread worker pool from 4 to 16",
        target_subsystem="scheduler_config",
        proposed_change={"max_workers": 16}
    )
    assert prop.status == "PROPOSED"

    # 2. Review
    assert gov.review_proposal(prop.proposal_id, reviewer_id="agent_critic", reviewer_role="critic", comments="Approved with canary test", approved=True) is True
    assert prop.status == "REVIEWED"

    # 3. Canary Test
    canary = gov.run_canary_test(prop.proposal_id, test_runner_callable=lambda cfg: cfg.get("max_workers") > 0)
    assert canary["canary_passed"] is True
    assert prop.status == "TESTED_CANARY"

    # 4. Approval
    assert gov.approve_proposal(prop.proposal_id, director_id="agent_director") is True
    assert prop.status == "APPROVED"

    # 5. Deployment
    deploy_res = gov.deploy_change(prop.proposal_id)
    assert deploy_res["success"] is True
    assert gov.active_configurations["scheduler_config"]["max_workers"] == 16
    assert prop.status == "DEPLOYED"

    # 6. Rollback
    rollback_res = gov.rollback_change(prop.proposal_id)
    assert rollback_res["success"] is True
    assert gov.active_configurations["scheduler_config"] == {}
    assert prop.status == "ROLLED_BACK"

def test_simulation_virtual_sandbox_world():
    """Verify safe experimentation, hypothesis testing, and failure isolation."""
    sandbox = VirtualSandboxWorld()

    # Hypothesis 1: Valid parameter
    h1 = sandbox.create_hypothesis(
        author_id="researcher_01",
        statement="Increasing batch size to 8 preserves deterministic stability",
        experimental_variables={"parameter_test": 8.0},
        expected_outcome="Stability preserved"
    )
    run1 = sandbox.run_experiment(h1.hypothesis_id)
    assert run1.passed is True
    assert h1.status == "CONFIRMED"
    assert len(run1.lessons_extracted) >= 1

    # Hypothesis 2: Hazardous edge case (negative boundary)
    h2 = sandbox.create_hypothesis(
        author_id="critic_01",
        statement="Negative cache capacity triggers buffer underflow",
        experimental_variables={"parameter_test": -1.0},
        expected_outcome="Catches safe error"
    )
    run2 = sandbox.run_experiment(h2.hypothesis_id)
    assert run2.passed is False
    assert h2.status == "REFUTED"
    assert len(run2.safe_failures_recorded) >= 1

def test_100_agent_society_scale_and_concurrency():
    """Verify scalability: spawn 100 agents, register in runtime, broadcast and execute."""
    runtime = AgentRuntime(max_workers=16)

    # Spawn 100 specialized agents distributed across the 18 roles
    roles_list = list(ROLE_TO_CLASS_MAP.keys())
    for i in range(100):
        role = roles_list[i % len(roles_list)]
        cls = ROLE_TO_CLASS_MAP[role]
        runtime.lifecycle.spawn(
            cls,
            name=f"Agent_{i:03d}_{role.value}",
            role=role,
            version="1.0.0"
        )

    assert runtime.registry.count() == 100

    # Test broadcast message across all 100 agents
    broadcast_count = runtime.bus.broadcast(
        message=runtime.registry.get_all()[0].send_message(
            recipient_id="*",
            message_type="proposal",
            payload={"directive": "Civilization Synchronization"}
        )
    )
    assert broadcast_count == 99  # 99 recipients excluding sender

    # Verify mailbox reception on arbitrary agent
    sample_agent = runtime.registry.get_all()[50]
    unread = sample_agent.mailbox.peek_unread_count()
    assert unread >= 1
    received_msg = sample_agent.receive_next_message()
    assert received_msg is not None
    assert received_msg.payload["directive"] == "Civilization Synchronization"

    # Run observer on 100-agent society
    observer = SystemObserver(runtime)
    snap = observer.capture_snapshot()
    assert snap.total_agents == 100
    assert snap.total_messages_exchanged > 0

    runtime.shutdown()
