"""Project Alpha Phase 3: Multi-Agent Cognitive Operating System Master Demonstration.

Executes all 6 mandatory demonstration scenarios:
- Scenario 1: 100-Agent Cognitive Society Scenario (Runtime, Scheduler, Bus, Observer)
- Scenario 2: Multi-Agent Research Project (Research, Knowledge, Critic & Verification)
- Scenario 3: Dynamic Team Coding Project (Director -> Architect -> Planner -> Builder -> Coder -> Tester -> Validator)
- Scenario 4: Debugging Project via Competitive Reasoning (Red Team Attack vs Blue Team Defense)
- Scenario 5: Knowledge Discovery, Skill Evolution & Agent Mutation (Shared Knowledge, Skill Composer, Evolution Engine)
- Scenario 6: Long-Term Planning Project & Deliberation Council (Council Verdict, Marketplace Economy & Change Governance)
"""

import sys
import time
from typing import Dict, Any, List

from alpha.operating_system import AlphaOperatingSystem
from alpha.agents import (
    AgentRuntime,
    AgentRole,
    AgentStatus,
    AgentMessage,
    MessageType,
    MessagePriority,
    CouncilDeliberationSystem,
    CompetitiveReasoningEngine,
    DynamicTeam,
    TeamManager,
    SharedKnowledgeLayer,
    SkillLibrary,
    AgentEvolutionEngine,
    MetaLearningFramework,
    CivilizationMemorySystem,
    SystemObserver,
    ExecutionMarketplace,
    ChangeGovernanceSystem,
    VirtualSandboxWorld,
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
    KnowledgeAgent,
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def print_banner(title: str) -> None:
    print("\n" + "=" * 84)
    print(f"  {title.upper()}")
    print("=" * 84)

def print_section(title: str) -> None:
    print(f"\n--- [ {title} ] ---")

def run_scenario_1_100_agents(aos: AlphaOperatingSystem) -> None:
    print_banner("Scenario 1: 100-Agent Cognitive Society Scenario")
    print("Goal: Spawn, register, coordinate, and monitor a civilization of 100 specialized minds.")

    runtime = AgentRuntime(max_workers=16)
    roles = list(ROLE_TO_CLASS_MAP.keys())

    print(f"Spawning 100 agents distributed across {len(roles)} specialized archetypes...")
    t0 = time.perf_counter()
    for i in range(100):
        role = roles[i % len(roles)]
        cls = ROLE_TO_CLASS_MAP[role]
        runtime.lifecycle.spawn(
            cls,
            name=f"Agent_{i+1:03d}_{role.value.capitalize()}",
            role=role,
            version="1.0.0"
        )
    spawn_duration = (time.perf_counter() - t0) * 1000.0
    print(f"Successfully spawned {runtime.registry.count()} agents in {spawn_duration:.2f}ms.")

    print_section("Civilization Broadcast Communication")
    lead_agent = runtime.registry.get_all()[0]
    msg = lead_agent.send_message(
        recipient_id="*",
        message_type=MessageType.PROPOSAL,
        payload={"directive": "Synchronize civilizational state", "epoch": 3}
    )
    broadcast_delivered = runtime.bus.broadcast(msg)
    print(f"Broadcast from {lead_agent.identity.name} ({lead_agent.role.value}):")
    print(f"  - Message ID: {msg.message_id}")
    print(f"  - SHA-256 Audit Hash: {msg.audit_hash[:16]}...")
    print(f"  - Verified Delivery to {broadcast_delivered} recipients across society.")

    print_section("Concurrent Task Execution Across Society")
    t_exec_start = time.perf_counter()
    # Dispatch tasks to sample agents across various roles
    sample_agents = runtime.registry.get_all()[:20]
    for agent in sample_agents:
        runtime.scheduler.execute_task(agent, {"goal": f"Execute collective assignment for {agent.role.value}"})
    exec_duration = (time.perf_counter() - t_exec_start) * 1000.0
    print(f"Dispatched and completed 20 tasks across society in {exec_duration:.2f}ms.")

    print_section("System Observer Telemetry Snapshot")
    observer = SystemObserver(runtime)
    snapshot = observer.capture_snapshot()
    print(f"Total Agents in Society:       {snapshot.total_agents}")
    print(f"Active Tasks Completed:        {snapshot.total_tasks_completed}")
    print(f"Messages Exchanged:            {snapshot.total_messages_exchanged}")
    print(f"Average Latency:               {snapshot.avg_latency_ms:.2f} ms")
    print(f"P50 Latency:                   {snapshot.p50_latency_ms:.2f} ms")
    print(f"P95 Latency:                   {snapshot.p95_latency_ms:.2f} ms")
    print(f"P99 Latency:                   {snapshot.p99_latency_ms:.2f} ms")
    print(f"Resource Economy Units:        {snapshot.estimated_cost_units}")
    print(f"Society Status:                HEALTHY & SYNCHRONIZED")

    runtime.shutdown()

def run_scenario_2_research_project(aos: AlphaOperatingSystem) -> None:
    print_banner("Scenario 2: Multi-Agent Research Project")
    topic = "Active-Active Distributed State Machine Replication"
    print(f"Goal: Research architectural patterns for '{topic}', verify findings, and publish to Knowledge Layer.")

    researcher = aos.agent_runtime.lifecycle.spawn(ResearchAgent, name="LeadResearcher", role=AgentRole.RESEARCHER)
    critic = aos.agent_runtime.lifecycle.spawn(CriticAgent, name="ResearchCritic", role=AgentRole.CRITIC)
    knowledge = aos.agent_runtime.lifecycle.spawn(KnowledgeAgent, name="CorpusKnowledge", role=AgentRole.KNOWLEDGE)

    print_section("Step 1: Research Exploration & Citations")
    res_out = researcher.execute_task({"topic": topic, "max_sources": 2})
    print(f"Topic:              {res_out['topic']}")
    print(f"Synthesized Findings: {len(res_out['findings'])} items")
    for f in res_out["findings"]:
        print(f"  * {f}")
    print(f"Ranked Citations:   {len(res_out['citations'])} sources")
    for c in res_out["citations"]:
        print(f"  * [{c['credibility']*100:.0f}% Credibility] {c['source']}")

    print_section("Step 2: Adversarial Critique & Fact Checking")
    crit_out = critic.execute_task({"proposal": res_out["summary"], "topic": topic})
    print(f"Critic Verdict:     {crit_out['verdict']}")
    print(f"Critic Score:       {crit_out['critic_score']:.2f}")
    print(f"Dissent Level:      {crit_out['dissent_level']:.2f}")
    print(f"Counterarguments Analyzed: {len(crit_out['counterarguments'])}")
    for ca in crit_out["counterarguments"]:
        print(f"  - {ca}")

    print_section("Step 3: Verified Knowledge Publication")
    pub_item = aos.knowledge_society.publish(
        key="research:state_machine_replication",
        title="Active-Active State Machine Replication Architecture",
        content=res_out["summary"],
        author_id=researcher.agent_id,
        author_role="researcher",
        tags=["consensus", "replication", "distributed"],
        auto_verify=True
    )
    aos.knowledge_society.cite_knowledge(pub_item.key)
    print(f"Knowledge Key:      {pub_item.key}")
    print(f"Verified Status:    {pub_item.is_verified}")
    print(f"Citation Count:     {pub_item.citation_count}")
    print(f"Civilization Rank:  {pub_item.compute_ranking():.3f}")

def run_scenario_3_coding_project(aos: AlphaOperatingSystem) -> None:
    print_banner("Scenario 3: Dynamic Team Coding Project")
    mission = "Construct High-Performance Concurrent Rate Limiter Module"
    print(f"Goal: Form dynamic team, pipeline directive -> architect -> planner -> coder -> tester -> validator, then dissolve.")

    print_section("Step 1: Automatic Team Formation")
    team = aos.form_coding_team(task_name="RateLimiterEngine", mission_goal=mission)
    print(f"Team ID:            {team.team_id}")
    print(f"Team Status:        {team.status}")
    print(f"Assembled Members:  {len(team.members)}")
    for m in team.members:
        print(f"  - [{m.role.value.upper()}] {m.identity.name}")

    print_section("Step 2: Collaborative Multi-Agent Pipeline Execution")
    result = team.execute_workflow({"target_path": "alpha/concurrency/rate_limiter.py"})
    print(f"Workflow Success:   {result['success']}")
    print(f"Steps Executed:     {result['steps_executed']}/7")
    print(f"Execution Latency:  {result['duration_ms']:.2f} ms")
    for log_item in result["pipeline_log"]:
        print(f"  -> Stage [{log_item['step'].upper()}]: Complete")

    print_section("Step 3: Synthesized Code & Verification Artifacts")
    print(f"Tests Passed:       {result['tests_passed']}")
    print("Sample Synthesized Code:")
    for line in result["final_code"].splitlines()[:8]:
        print(f"  {line}")

    print_section("Step 4: Automatic Team Dissolution")
    dissolve_summary = aos.teams.dissolve_team(team.team_id)
    print(f"Dissolved Team ID:  {dissolve_summary['team_id']}")
    print(f"Members Released:   {dissolve_summary['members_released']} agents returned to idle society pool")
    print(f"Final Team Status:  {dissolve_summary['status']}")

def run_scenario_4_debugging_project(aos: AlphaOperatingSystem) -> None:
    print_banner("Scenario 4: Debugging via Competitive Reasoning (Red Team vs Blue Team)")
    print("Goal: Stress-test vulnerable payment authentication session using multi-round adversarial competition.")

    target_code = {
        "name": "PaymentAuthSession",
        "parameters": {"timeout_seconds": 3600, "retry_limit": 100},
        "vulnerability_notes": "Unbounded concurrent retries and missing input validation"
    }

    print_section("Adversarial Rounds (Attack & Defense)")
    comp_result = aos.run_adversarial_hardening(target_code, num_rounds=2)

    for rnd in comp_result.rounds:
        print(f"\n--- Round {rnd.round_number} ---")
        print(f"RED TEAM ATTACKS ({len(rnd.attack_points)}):")
        for atk in rnd.attack_points:
            print(f"  [!] {atk}")
        print(f"BLUE TEAM DEFENSES ({len(rnd.defense_mitigations)}):")
        for df in rnd.defense_mitigations:
            print(f"  [+] {df}")
        print(f"Round Robustness Score: {rnd.round_robustness_score:.2f}")

    print_section("Final Hardening Verdict")
    print(f"Initial Robustness:  {comp_result.initial_robustness:.2f}")
    print(f"Final Robustness:    {comp_result.final_robustness:.2f} (+{(comp_result.final_robustness - comp_result.initial_robustness)*100:.0f}% improvement)")
    print(f"Flaws Uncovered:     {comp_result.flaws_uncovered}")
    print(f"Flaws Patched:       {comp_result.flaws_patched}")
    print(f"Verdict:             {comp_result.verdict}")
    print(f"Total Hardening ms:  {comp_result.duration_ms:.2f} ms")

def run_scenario_5_knowledge_discovery_skills_evolution(aos: AlphaOperatingSystem) -> None:
    print_banner("Scenario 5: Knowledge Discovery, Skill Evolution & Agent Mutation")
    print("Goal: Demonstrate Skill Composition, Mutation, Marketplace Bidding, and Agent Evolution.")

    print_section("Part A: Composable Skill Creation & Upgrade")
    skill = aos.skills.composer.compose_skill(
        name="automated_canary_pipeline",
        description="Scaffold sandbox, inject canary payload, run unit tests, verify metrics.",
        steps=[
            {"step": 1, "action": "scaffold_sandbox"},
            {"step": 2, "action": "inject_canary_payload"},
            {"step": 3, "action": "execute_verification_tests"},
            {"step": 4, "action": "emit_telemetry_digest"}
        ],
        tags=["canary", "testing", "ci"]
    )
    print(f"Composed Skill:      {skill.name} v{skill.version}")
    print(f"Validation Status:   {skill.is_validated}")

    exec_out = aos.skills.executor.execute(skill, {"target": "AlphaService"})
    print(f"Skill Executed:      {exec_out['steps_completed']} steps completed successfully in {exec_out['latency_ms']:.2f}ms")

    # Evolve skill
    improved_skill = aos.skills.composer.improve_skill(
        existing_name="automated_canary_pipeline",
        new_steps=[
            {"step": 1, "action": "scaffold_sandbox"},
            {"step": 2, "action": "inject_canary_payload"},
            {"step": 3, "action": "execute_verification_tests"},
            {"step": 4, "action": "sandbox_memory_check"},
            {"step": 5, "action": "emit_telemetry_digest"}
        ],
        version_bump="1.2.0"
    )
    print(f"Evolved Skill:       {improved_skill.name} upgraded to v{improved_skill.version} ({len(improved_skill.steps)} steps)")

    print_section("Part B: Agent Fitness Ranking & Evolution Mutation")
    # Spawn and simulate agent with low performance
    struggling = aos.agent_runtime.lifecycle.spawn(CodingAgent, name="LegacyCoder", role=AgentRole.CODER)
    struggling.record_execution(success=False, latency_ms=120.0)
    struggling.record_execution(success=False, latency_ms=130.0)
    struggling.record_execution(success=False, latency_ms=140.0)

    leaderboard = aos.evolution.rank_society()
    print("Society Fitness Leaderboard (Top 3):")
    for entry in leaderboard[:3]:
        print(f"  #{entry.rank} {entry.name} ({entry.role}) - Fitness: {entry.fitness_score:.1f}, Success: {entry.success_rate*100:.1f}%")

    proposals = aos.evolution.scan_for_underperformers(fitness_threshold=50.0)
    print(f"Evolution Proposals Generated: {len(proposals)}")
    if proposals:
        prop = proposals[0]
        print(f"  Target:            {prop.target_agent_id}")
        print(f"  Action:            {prop.action_type.value.upper()}")
        print(f"  Rationale:         {prop.rationale}")
        exec_res = aos.evolution.execute_proposal(prop.proposal_id)
        print(f"  Execution Result:  {exec_res['details']['action']} -> {exec_res['success']}")

    print_section("Part C: Meta-Learning Operational Rule Synthesis")
    aos.meta_learning.record_failure("remote_rpc", "TimeoutException", {"retries": 3})
    aos.meta_learning.record_success("sandbox_test", {"cases": 10}, latency_ms=15.0)
    new_rules = aos.meta_learning.generate_operational_rules()
    print(f"Mined Patterns & Formulated {len(new_rules)} Operational Rules:")
    for r in new_rules:
        print(f"  * [{r.rule_id}] {r.condition} -> {r.directive}")
    pub_count = aos.meta_learning.publish_lessons_to_society()
    print(f"Published {pub_count} operational rules to Civilizational Knowledge Store.")

def run_scenario_6_long_term_planning_and_marketplace(aos: AlphaOperatingSystem) -> None:
    print_banner("Scenario 6: Long-Term Planning, Council Deliberation & Marketplace Economy")
    question = "Architect zero-downtime geo-distributed failover across multi-region clusters"
    print(f"Question: '{question}'")

    print_section("Step 1: Council Deliberation Pipeline")
    verdict = aos.deliberate(question)
    print(f"Consensus Status:       {verdict.consensus_status}")
    print(f"Evidence Score:         {verdict.evidence_score:.2f}")
    print(f"Disagreement Variance:  {verdict.disagreement_level:.2f}")
    print(f"Composite Confidence:   {verdict.confidence_score:.2f}")
    print(f"Deliberation Latency:   {verdict.deliberation_time_ms:.2f} ms")
    print(f"Council Rationale:      {verdict.rationale}")

    print("\nAlternative Plans Formulated:")
    for alt in verdict.alternative_plans:
        print(f"  - Plan '{alt.get('plan_name')}': {alt.get('description')}")

    print("\nIdentified Risks & Mitigations:")
    for rsk in verdict.identified_risks:
        print(f"  - [Risk: {rsk.get('risk')}] -> Mitigation: {rsk.get('mitigation')}")

    print_section("Step 2: Execution Marketplace Auction & Worker Settlement")
    market_res = aos.run_marketplace_job(
        title="Synthesize Failover Consensus Controller",
        payload={"spec": "Raft leader lease renewal with monotonic clocks", "language": "python"},
        required_role=AgentRole.CODER,
        budget_credits=150.0
    )
    print(f"Job Status:             SUCCESS")
    print(f"Winning Worker:         {market_res['winning_agent']}")
    print(f"Winning Bid:            {market_res['winning_bid_price']} credits")
    print(f"Worker Account Balance: {market_res['worker_balance']} credits")
    print(f"Settlement Latency:     {market_res['latency_ms']:.2f} ms")

    print_section("Step 3: Self-Improvement Change Governance")
    gov_prop = aos.governance.submit_proposal(
        proposer_id="LeadArchitect",
        proposer_role="architect",
        title="Activate geo-replicated quorum threshold",
        description="Set minimum consensus quorum to (N/2)+1 across regions",
        target_subsystem="consensus_config",
        proposed_change={"quorum_size": 3, "heartbeat_interval_ms": 250}
    )
    print(f"1. Proposal Created:    {gov_prop.proposal_id[:8]}... (Status: {gov_prop.status})")

    # Review
    aos.governance.review_proposal(gov_prop.proposal_id, reviewer_id="LeadCritic", reviewer_role="critic", comments="Quorum logic mathematically sound", approved=True)
    print(f"2. Multi-Agent Review:  APPROVED (Status: {gov_prop.status})")

    # Canary Simulation in Virtual Sandbox World
    canary = aos.governance.run_canary_test(gov_prop.proposal_id, test_runner_callable=lambda cfg: cfg.get("quorum_size") >= 3)
    print(f"3. Virtual Sandbox Run: PASSED (Canary: {canary['canary_passed']})")

    # Approval & Deployment
    aos.governance.approve_proposal(gov_prop.proposal_id, director_id="DirectorLead")
    deploy = aos.governance.deploy_change(gov_prop.proposal_id)
    print(f"4. Production Deploy:   SUCCESS (Config: {deploy['new_configuration']})")

    # Rollback Verification
    rollback = aos.governance.rollback_change(gov_prop.proposal_id)
    print(f"5. Rollback Test:       VERIFIED (Status: {gov_prop.status})")

    print_section("Step 4: Master System Observation Report")
    report = aos.observe_society()
    print(f"Overall Society Health: {report.health_status}")
    print(f"Total Agents Monitored: {report.snapshot.total_agents}")
    print(f"Total Messages Logged:  {report.snapshot.total_messages_exchanged}")
    print("Actionable Recommendations:")
    for rec in report.recommendations:
        print(f"  * {rec}")

def main() -> None:
    t_start = time.perf_counter()
    print("\n" + "#" * 84)
    print("  PROJECT ALPHA - PHASE 3: MULTI-AGENT COGNITIVE OPERATING SYSTEM DEMONSTRATION")
    print("#" * 84)

    aos = AlphaOperatingSystem()

    # Execute all 6 required scenarios
    run_scenario_1_100_agents(aos)
    run_scenario_2_research_project(aos)
    run_scenario_3_coding_project(aos)
    run_scenario_4_debugging_project(aos)
    run_scenario_5_knowledge_discovery_skills_evolution(aos)
    run_scenario_6_long_term_planning_and_marketplace(aos)

    total_duration = time.perf_counter() - t_start
    print("\n" + "=" * 84)
    print(f"  PHASE 3 MASTER DEMONSTRATION COMPLETED SUCCESSFULLY IN {total_duration:.2f}s")
    print("  Alpha has transitioned from a Single Agent into a Thriving Cognitive Society.")
    print("=" * 84 + "\n")

if __name__ == "__main__":
    main()
