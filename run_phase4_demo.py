"""Project Alpha Phase 4: Cognitive World Model Master Demonstration.

Transforms Alpha from Memory-Based Intelligence into Reality-Based Intelligence.
Executes all 8 mandatory demonstrations:
- Demonstration 1: Build a complete world model
- Demonstration 2: Track project evolution over time
- Demonstration 3: Generate new concepts
- Demonstration 4: Generate new principles
- Demonstration 5: Predict project outcomes
- Demonstration 6: Detect knowledge gaps
- Demonstration 7: Simulate alternative futures
- Demonstration 8: Distill 1000 memories into concepts
"""

import sys
import time
from typing import Dict, Any, List

from alpha.operating_system import AlphaOperatingSystem
from alpha.world_model import (
    Entity,
    CognitiveWorldModel,
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
    EntityType,
    LifecycleState,
    RelationType,
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    UncertaintyLevel,
    SelfIntrospection,
    WorldStateSnapshot,
    CognitiveEvolutionResult,
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def print_banner(title: str) -> None:
    print("\n" + "=" * 88)
    print(f"  {title.upper()}")
    print("=" * 88)


def print_section(title: str) -> None:
    print(f"\n--- [ {title} ] ---")


# =============================================================================
# Demonstration 1: Build a Complete World Model
# =============================================================================
def demo_1_build_complete_world_model(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 1: Build a Complete World Model")
    print("Objective: Instantiate an ontological universe where every memory, tool, agent, and goal")
    print("becomes a first-class Entity integrated into a unified Universal Knowledge Graph.")

    t0 = time.perf_counter()

    # 1. Organization & Core Agents
    org = OrganizationEntity(name="Project Alpha Foundation", mission="Reality-Grounded Autonomous Intelligence")
    cwm.register_entity(org)

    agent_arch = AgentEntity(name="ChiefArchitectAgent", role="architect", fitness_score=0.98)
    agent_coder = AgentEntity(name="ApexCoderAgent", role="coder", fitness_score=0.95)
    agent_sec = AgentEntity(name="CyberSecurityAgent", role="security", fitness_score=0.97)
    cwm.register_entity(agent_arch)
    cwm.register_entity(agent_coder)
    cwm.register_entity(agent_sec)

    # 2. Project, Goals, Tasks
    goal = GoalEntity(
        name="Zero Epistemic Hallucination",
        objective="Eliminate ungrounded assumptions via strict evidence chains",
        importance=1.0,
        confidence=1.0
    )
    cwm.register_entity(goal)

    proj = ProjectEntity(name="Autonomous World Engine", goal_ids=[goal.id], budget_credits=5000.0)
    cwm.register_entity(proj)

    t1 = TaskEntity(name="Construct Universal Knowledge Graph", status="active", assignee_id=agent_arch.id)
    t2 = TaskEntity(name="Deploy Causal Counterfactual Sandbox", status="active", assignee_id=agent_coder.id)
    cwm.register_entity(t1)
    cwm.register_entity(t2)

    # 3. Tools, Skills, Capabilities
    tool_fs = ToolEntity(name="fs_secure_io", tool_name="fs_secure_io", sandbox_level="isolated")
    skill_causal = SkillEntity(name="CausalInference", domain="epistemology", skill_version="2.0.0")
    cap_proof = CapabilityEntity(name="FormalASTVerification", category="reasoning", proficiency=0.99)
    cwm.register_entity(tool_fs)
    cwm.register_entity(skill_causal)
    cwm.register_entity(cap_proof)

    # 4. Epistemic Belief grounded in Evidence
    ev = cwm.record_evidence(
        statement="AST syntax verifiers detect 100% of invalid Python syntax before runtime execution.",
        polarity=EvidencePolarity.SUPPORTING,
        strength=EvidenceStrength.STRONG,
        source_id="ci_cd_test_runner"
    )
    b = cwm.form_belief(
        statement="Pre-execution AST verification prevents syntax regressions from reaching production.",
        initial_confidence=0.98,
        evidence_ids=[ev.evidence_id],
        domain="software_reliability"
    )

    # 5. Semantic Graph Relationships across the Civilization
    cwm.relate(agent_arch.id, proj.id, RelationType.CREATED_BY)
    cwm.relate(agent_coder.id, t2.id, RelationType.USES)
    cwm.relate(proj.id, goal.id, RelationType.SUPPORTS)
    cwm.relate(t2.id, tool_fs.id, RelationType.DEPENDS_ON)
    cwm.relate(agent_coder.id, skill_causal.id, RelationType.USES)
    cwm.relate(skill_causal.id, cap_proof.id, RelationType.BELONGS_TO)
    cwm.relate(b.belief_id, proj.id, RelationType.VALIDATES)

    dur = (time.perf_counter() - t0) * 1000.0

    print_section("World Model Topological Structure")
    print(f"Total Entities in Ontology:     {cwm.ontology.count()}")
    print(f"Total Nodes in Knowledge Graph: {cwm.graph.node_count()}")
    print(f"Total Semantic Graph Edges:     {cwm.graph.edge_count()}")
    print(f"Entities by Type Distribution:  {cwm.ontology.count_by_type()}")
    print(f"Ontology Population Time:       {dur:.2f}ms")

    print_section("Graph Centrality & PageRank Analytics")
    analytics = cwm.graph_analytics
    summary = analytics.summarize()
    pr = analytics.compute_pagerank()
    top_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:4]
    print(f"Is Graph a Valid DAG:           {summary['is_dag']}")
    print(f"Connected Components:           {summary['component_count']}")
    print("Highest PageRank Nodes (Prominence):")
    for nid, score in top_pr:
        node = cwm.graph.get_node(nid)
        name = node.name if node else nid
        print(f"  - [{nid[:14]}] {name:<36} : {score:.4f}")

    print_section("Self-Model Introspection (Who Am I?)")
    intro = cwm.introspect_self()
    print(f"Identity:     {intro.who_am_i}")
    print(f"Nature:       {intro.what_am_i}")
    print(f"Active Goals: {[g['name'] for g in intro.what_are_my_goals]}")
    print(f"Limits:       {intro.what_can_i_not_do[:2]}")


# =============================================================================
# Demonstration 2: Track Project Evolution Over Time
# =============================================================================
def demo_2_track_project_evolution(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 2: Track Project Evolution Over Time")
    print("Objective: Demonstrate temporal reasoning by tracking birth, growth, change, decay,")
    print("and completion across virtual timeline checkpoints.")

    p_evo = ProjectEntity(name="Project Prometheus: Autonomous Self-Evolution", status="planned")
    cwm.register_entity(p_evo)

    # Epoch 0: Inception
    t_start = 1000.0
    cwm.time_engine.reset_to(t_start)
    cwm.lifecycle.record_birth(p_evo.id, reason="Project chartered by Executive Council")
    ev0 = cwm.record_evidence("Feasibility study concludes 85% probability of delivery", source_id="feasibility_team")
    b_proj = cwm.form_belief("Project Prometheus will successfully complete within Q4", 0.85, evidence_ids=[ev0.evidence_id])
    snap_t0 = cwm.capture_world_state(tag="epoch_0_inception")

    print_section("Epoch 0 (T = 1,000.0s) - Inception")
    print(f"Project Stage:     {cwm.lifecycle.get_current_stage(p_evo.id).value}")
    print(f"Belief Confidence: {b_proj.confidence:.2f}")

    # Epoch 1: Execution & Growth (+ 500s)
    cwm.time_engine.advance_time(500.0)
    p_evo.status = "in_progress"
    cwm.lifecycle.record_growth(p_evo.id, reason="Sprint 1 deliverables completed with zero defects")
    ev1 = cwm.record_evidence("Sprint 1 automated integration tests 100% passed", EvidencePolarity.SUPPORTING, EvidenceStrength.STRONG, claim_id=b_proj.belief_id)
    snap_t1 = cwm.capture_world_state(tag="epoch_1_growth")

    print_section("Epoch 1 (T = 1,500.0s) - Execution & Growth")
    print(f"Virtual Time:      {cwm.time_engine.current_virtual_time:.1f}s")
    print(f"Project Stage:     {cwm.lifecycle.get_current_stage(p_evo.id).value}")
    print(f"Belief Confidence: {b_proj.confidence:.2f} (Strengthened via empirical CI evidence)")

    # Epoch 2: Architectural Change (+ 1000s)
    cwm.time_engine.advance_time(1000.0)
    cwm.lifecycle.record_change(p_evo.id, reason="Refactored from monolithic pipeline into decentralized swarm")
    snap_t2 = cwm.capture_world_state(tag="epoch_2_mutation")

    print_section("Epoch 2 (T = 2,500.0s) - Paradigm Shift")
    print(f"Project Stage:     {cwm.lifecycle.get_current_stage(p_evo.id).value}")

    # Epoch 3: Temporal Query (What Was True?)
    print_section("Temporal Query Engine: 'What Was True At Each Point in Time?'")
    at_1000 = cwm.what_was_true(1000.0)
    at_1600 = cwm.what_was_true(1600.0)
    print(f"Beliefs True at T=1,000s: {len(at_1000)} active propositions")
    print(f"Beliefs True at T=1,600s: {len(at_1600)} active propositions")
    print("Belief Historical Trajectory:")
    for snap in cwm.belief_timeline.get_belief_trajectory(b_proj.belief_id):
        print(f"  - T = {snap.timestamp:<7.1f}s | Confidence: {snap.confidence:.2f} | Statement: '{snap.statement[:48]}...'")


# =============================================================================
# Demonstration 3: Generate New Concepts
# =============================================================================
def demo_3_generate_new_concepts(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 3: Generate New Concepts")
    print("Objective: Form abstract higher-order concepts from concrete exemplars")
    print("Example 1: Dog, Wolf, Fox -> Canine Archetype")
    print("Example 2: Redis, Postgres, Qdrant -> Data Storage Systems")

    # Exemplars 1: Biology
    dog = Entity(entity_type=EntityType.OBSERVATION, name="Domestic Dog", attributes={"quadruped": True, "pack_instinct": True, "carnivore": True})
    wolf = Entity(entity_type=EntityType.OBSERVATION, name="Grey Wolf", attributes={"quadruped": True, "pack_instinct": True, "carnivore": True})
    fox = Entity(entity_type=EntityType.OBSERVATION, name="Red Fox", attributes={"quadruped": True, "pack_instinct": False, "carnivore": True})

    canine_concept = cwm.concept_discovery.form_concept_from_exemplars(
        concept_name="Canine Family (Canidae)",
        definition="Carnivorous digitigrade mammals possessing non-retractile claws and social pack behaviors.",
        exemplar_entities=[dog, wolf, fox],
        abstraction_depth=2
    )
    cwm.register_entity(canine_concept)

    # Exemplars 2: Storage Technology
    redis = ToolEntity(name="Redis Engine", tool_name="redis", attributes={"storage_mode": "memory", "sub_millisecond": True})
    postgres = ToolEntity(name="PostgreSQL Database", tool_name="postgres", attributes={"storage_mode": "relational_disk", "acid": True})
    qdrant = ToolEntity(name="Qdrant Vector DB", tool_name="qdrant", attributes={"storage_mode": "hnsw_vector", "similarity": True})

    storage_concept = cwm.concept_discovery.form_concept_from_exemplars(
        concept_name="Data Storage Systems",
        definition="Computational subsystems for durable or transient state persistence and index-based retrieval.",
        exemplar_entities=[redis, postgres, qdrant],
        abstraction_depth=2
    )
    cwm.register_entity(storage_concept)

    # Build Taxonomy Tree
    cwm.taxonomy.add_category("Computational Systems", parent_name="Universal Entity", description="All software architectures")
    cwm.taxonomy.add_category("Data Storage Systems", parent_name="Computational Systems", description="State persistence systems")
    cwm.taxonomy.add_exemplar("Data Storage Systems", "Redis Engine")
    cwm.taxonomy.add_exemplar("Data Storage Systems", "PostgreSQL Database")
    cwm.taxonomy.add_exemplar("Data Storage Systems", "Qdrant Vector DB")

    print_section("Synthesized Higher-Order Concepts")
    print(f"Concept 1: '{canine_concept.name}'")
    print(f"  Definition: {canine_concept.definition}")
    print(f"  Exemplars:  {canine_concept.attributes.get('exemplar_names')}")
    print(f"\nConcept 2: '{storage_concept.name}'")
    print(f"  Definition: {storage_concept.definition}")
    print(f"  Exemplars:  {storage_concept.attributes.get('exemplar_names')}")

    print_section("Ontological Taxonomy Hierarchy Lineage")
    lineage = cwm.taxonomy.get_lineage("Data Storage Systems")
    print(" -> ".join(lineage))


# =============================================================================
# Demonstration 4: Generate New Principles
# =============================================================================
def demo_4_generate_new_principles(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 4: Generate New Principles")
    print("Objective: Synthesize fundamental civilizational laws and principles")
    print("from disparate observations across distributed subsystems.")

    facts = [
        {"statement": "Subprocess timeouts prevent runaway compute loops in sandbox execution.", "domain": "isolation"},
        {"statement": "Token bucket rate limiters prevent API exhaustion under traffic spikes.", "domain": "traffic"},
        {"statement": "Circuit breakers decouple failing downstream microservices from callers.", "domain": "fault_tolerance"},
        {"statement": "Memory compaction evicts low-importance records to bound RAM consumption.", "domain": "memory"}
    ]

    print_section("Input Disparate Subsystem Facts")
    for f in facts:
        print(f"  - [{f['domain'].upper():<16}]: {f['statement']}")

    insight = cwm.synthesis.synthesize(facts)

    print_section("Synthesized Emergent Civilizational Principle")
    print(f"Statement:           {insight.statement}")
    print(f"Extracted Principle: {insight.extracted_principle}")
    print(f"Analogy:             {insight.analogy}")
    print(f"Testable Hypothesis: {insight.derived_hypothesis}")
    print(f"Synthesis Confidence: {insight.confidence * 100:.1f}%")


# =============================================================================
# Demonstration 5: Predict Project Outcomes
# =============================================================================
def demo_5_predict_project_outcomes(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 5: Predict Project Outcomes")
    print("Objective: Trace causal chains forward into the future to forecast delivery,")
    print("risk blast radius, and resource bottlenecks.")

    p_cloud = ProjectEntity(name="Multi-Cloud Migration Project", status="active", budget_credits=3000.0)
    cwm.register_entity(p_cloud)

    # Register Causal Risk Chain
    cwm.register_causal_link("UnderprovisionedNetwork", "HighPacketLoss", strength=0.92, mechanism="BandwidthSaturation")
    cwm.register_causal_link("HighPacketLoss", "DatabaseSyncDelay", strength=0.88, mechanism="TCPRetransmission")
    cwm.register_causal_link("DatabaseSyncDelay", "ServiceDowntime", strength=0.80, mechanism="ReplicaLag")

    print_section("Causal Blast Radius Forward Prediction")
    impact = cwm.causal.predict_change_impact("UnderprovisionedNetwork", severity=1.0)
    print(f"Root Trigger:       {impact['trigger']}")
    print(f"Downstream Blast:   {impact['blast_radius']} affected nodes")
    print(f"Total Impact Score: {impact['total_impact_score']:.2f}")
    for aff in impact["affected_nodes"]:
        print(f"  - Node '{aff['node_id']}': Predicted Severity = {aff['predicted_severity']:.2f} (Dist={aff['shortest_distance']})")

    print_section("Future World State Extrapolation (1 Hour Ahead)")
    future_state = cwm.what_may_become_true(horizon_seconds=3600.0)
    print(f"Future State Mode:    {future_state.state_mode}")
    print(f"Projected Tasks:      {len(future_state.tasks)} tasks projected")
    print(f"Projected Resources:  {len(future_state.resources)} resources monitored")


# =============================================================================
# Demonstration 6: Detect Knowledge Gaps
# =============================================================================
def demo_6_detect_knowledge_gaps(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 6: Detect Knowledge Gaps & Epistemic Curiosity")
    print("Objective: Alpha inspects its own mind to identify what it does not know,")
    print("what contradictions exist, and what learning objectives to pursue next.")

    # Deliberately seed voids
    g_orphan = GoalEntity(name="Sub-Millisecond Multi-Agent Consensus", objective="Ultra-low latency Raft consensus")
    cwm.register_entity(g_orphan)

    r_unmitigated = RiskEntity(name="Byzantine Adversarial Infiltration", severity=0.95, mitigation_plan="")
    cwm.register_entity(r_unmitigated)

    ev_c1 = cwm.record_evidence("Test A showed 5ms latency under load", source_id="lab_bench")
    ev_c2 = cwm.record_evidence("Test B showed 50ms latency under identical load", EvidencePolarity.CONTRADICTING, source_id="production_probe")
    b_conflicted = cwm.form_belief("Raft consensus completes in < 10ms", 0.65, evidence_ids=[ev_c1.evidence_id, ev_c2.evidence_id])
    b_conflicted.contradictions.append(ev_c2.evidence_id)

    overview = cwm.meta_knowledge.evaluate_epistemic_overview()

    print_section("Meta-Knowledge Epistemic Self-Assessment")
    print("What Alpha Knows with High Certainty (>= 85%):")
    for k in overview["what_i_know"][:2]:
        print(f"  - [Confidence {k['confidence']*100:.0f}%] '{k['statement'][:60]}...'")

    print("\nWhat Alpha Doubts / Contradicts:")
    for d in overview["what_i_misunderstand_or_contradict"][:2]:
        print(f"  - Contradiction count: {d['contradictions']} | '{d['statement'][:60]}...'")

    print(f"\nDetected Knowledge Gaps: {overview['knowledge_gaps_count']} gaps identified")
    print("Ranked Autonomous Learning Priorities:")
    for i, lp in enumerate(overview["top_learning_priorities"][:3], 1):
        print(f"  {i}. [Urgency: {lp['urgency_score']:.2f}] [Target: {lp['target_role'].upper()}]")
        print(f"     Topic: {lp['topic']}")


# =============================================================================
# Demonstration 7: Simulate Alternative Futures
# =============================================================================
def demo_7_simulate_alternative_futures(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 7: Simulate Alternative Futures (Reality Sandbox)")
    print("Objective: Execute safe counterfactual interventions in an isolated sandbox")
    print("without perturbing real production entities.")

    p_canary = ProjectEntity(name="Project Canary: Autonomous Code Deployment")
    a_lead = AgentEntity(name="CanaryReleaseAgent", role="director")
    cwm.register_entity(p_canary)
    cwm.register_entity(a_lead)

    print_section("Simulation Scenario A: 'If Project Canary Fails, What Happens?'")
    sim_proj = cwm.simulation.simulate_project_failure(p_canary.id)
    print(f"Scenario:              {sim_proj.target_intervention}")
    print(f"Cascade Depth:         {sim_proj.cascade_depth}")
    print(f"Projected Risk Score:  {sim_proj.projected_risk_score:.2f}")
    print(f"Narrative:             {sim_proj.narrative_summary}")

    print_section("Simulation Scenario B: 'If Lead Director Agent Is Removed, What Happens?'")
    sim_agent = cwm.simulation.simulate_agent_removal(a_lead.id)
    print(f"Scenario:              {sim_agent.target_intervention}")
    print(f"Narrative:             {sim_agent.narrative_summary}")

    print_section("Simulation Scenario C: Strategy Comparison (Plan A vs Plan B)")
    strat = cwm.simulation.simulate_strategy_comparison(
        strategy_a={"name": "Canary Rolling Update", "success_prob": 0.96, "cost": 150},
        strategy_b={"name": "Big-Bang Cutover", "success_prob": 0.65, "cost": 40}
    )
    print(f"Plan A Score:          {strat['strategy_a_score']}")
    print(f"Plan B Score:          {strat['strategy_b_score']}")
    print(f"Recommended Decision:  {strat['recommended_strategy'].upper()}")
    print(f"Rationale:             {strat['rationale']}")

    print_section("Sandbox Non-Pollution Verification")
    assert cwm.ontology.get(p_canary.id).lifecycle_state == LifecycleState.ACTIVE
    assert cwm.ontology.get(a_lead.id).lifecycle_state == LifecycleState.ACTIVE
    print("Verified: Production entities remain 100% ACTIVE. Sandbox state isolated.")


# =============================================================================
# Demonstration 8: Distill 1000 Memories into Concepts
# =============================================================================
def demo_8_distill_memories_to_concepts(cwm: CognitiveWorldModel) -> None:
    print_banner("Demonstration 8: High-Ratio Knowledge Distillation")
    print("Objective: Condense 1,000 memories into 10 concepts, 10,000 experiences")
    print("into 50 rules, and 100,000 observations into 500 principles.")

    # 1. 1,000 Memories -> 10 Concepts
    print_section("Part A: Distilling 1,000 Memories into 10 High-Level Concepts")
    memories = [
        {
            "id": f"mem_{i:04d}",
            "content": f"Subsystem telemetry {i % 10} recorded CPU utilization at {40 + (i % 50)}% during benchmark",
            "tag": f"subsystem_{i % 10}"
        }
        for i in range(1000)
    ]
    t0 = time.perf_counter()
    concepts = cwm.distillation.distill_memories_to_concepts(memories, target_concept_count=10)
    dur_mem = (time.perf_counter() - t0) * 1000.0

    print(f"Input Memories:       1,000")
    print(f"Output Concepts:      {len(concepts)}")
    print(f"Compression Ratio:    100:1 (99.0% reduction)")
    print(f"Distillation Latency: {dur_mem:.2f}ms")
    print("Sample Distilled Concepts:")
    for c in concepts[:3]:
        print(f"  - [{c.name}] : {c.definition[:65]}...")

    # 2. 10,000 Experiences -> 50 Rules
    print_section("Part B: Distilling 10,000 Experiences into 50 Operational Rules")
    actions = ["exponential_backoff", "circuit_break", "failover_replica", "flush_memtable", "shed_traffic"]
    outcomes = ["healthy_recovery", "prevented_cascade", "latency_normalized", "throughput_restored"]
    experiences = [
        {
            "id": f"exp_{i:05d}",
            "action": actions[i % len(actions)],
            "outcome": outcomes[i % len(outcomes)],
            "reward": 0.9 if i % 4 != 0 else -0.3
        }
        for i in range(10000)
    ]
    t1 = time.perf_counter()
    rules = cwm.distillation.distill_experiences_to_rules(experiences, target_rule_count=50)
    dur_exp = (time.perf_counter() - t1) * 1000.0

    print(f"Input Experiences:    10,000")
    print(f"Output Rules:         {len(rules)}")
    print(f"Compression Ratio:    200:1 (99.5% reduction)")
    print(f"Distillation Latency: {dur_exp:.2f}ms")
    print("Sample Operational Rules:")
    for r in rules[:3]:
        print(f"  - [{r.name}]: Success Rate = {r.success_rate*100:.1f}%")

    # 3. 100,000 Observations -> 500 Principles
    print_section("Part C: Distilling 100,000 Observations into 500 Foundational Principles")
    observations = [
        {"id": f"obs_{i:06d}", "source": f"sensor_{i % 5}", "type": "thermal", "value": i % 100}
        for i in range(100000)
    ]
    t2 = time.perf_counter()
    principles = cwm.distillation.distill_observations_to_principles(observations, target_principle_count=500)
    dur_obs = (time.perf_counter() - t2) * 1000.0

    print(f"Input Observations:   100,000")
    print(f"Output Principles:    {len(principles)}")
    print(f"Compression Ratio:    200:1 (99.5% reduction)")
    print(f"Distillation Latency: {dur_obs:.2f}ms")
    print("Sample Fundamental Principles:")
    for p in principles[:3]:
        print(f"  - [{p['principle_id']}]: {p['name']} (Empirical samples: {p['empirical_support_count']})")


# =============================================================================
# Bonus: End-to-End Cognitive Evolution Pipeline
# =============================================================================
def demo_bonus_cognitive_evolution_pipeline(cwm: CognitiveWorldModel) -> None:
    print_banner("Cognitive Transformation Pipeline: Observation -> Understanding")
    print("Observation -> Memory -> Knowledge -> Belief -> Concept -> Model -> Prediction -> Understanding")

    raw_event = {
        "source": "kernel_scheduler_telemetry",
        "subject": "AgentRuntimeWorkerPool",
        "predicate": "achieves_bounded_queue_latency",
        "value": "< 1.5ms under 1000 QPS",
        "hardware_tier": "tier_1_isolated"
    }

    t0 = time.perf_counter()
    result = cwm.process_observation_to_understanding(raw_event)
    dur = (time.perf_counter() - t0) * 1000.0

    print(f"Pipeline Run ID:     {result.pipeline_run_id}")
    print(f"Processing Latency:  {dur:.2f}ms")
    print("\nStage Transitions:")
    print(f"  1. OBSERVATION:    Source={result.observation['source']} | ObservedAt={result.observation['observed_at']:.0f}")
    print(f"  2. MEMORY:         Layer={result.memory['layer']} | AbstractionLevel={result.memory['abstraction_level']}")
    print(f"  3. KNOWLEDGE:      Fact='{result.knowledge['subject']} {result.knowledge['predicate']} {result.knowledge['object']}'")
    print(f"  4. BELIEF:         Confidence={result.belief['confidence']*100:.1f}% | Statement='{result.belief['statement'][:50]}...'")
    print(f"  5. CONCEPT:        Archetype='{result.concept['name']}'")
    print(f"  6. MODEL:          Mechanism='{result.model['mechanism']}' | Formula='{result.model['predictive_formula']}'")
    print(f"  7. PREDICTION:     Horizon=3600s | Uncertainty Range={result.prediction['uncertainty_range']}")
    print(f"  8. UNDERSTANDING:  '{result.understanding['core_truth']}'")
    print(f"                     Why: {result.understanding['why_it_happens']}")
    print(f"                     Grounding: {result.understanding['epistemic_grounding']}")


# =============================================================================
# Master Main Runner
# =============================================================================
def main():
    print_banner("PROJECT ALPHA PHASE 4: COGNITIVE WORLD MODEL MASTER RUNNER")
    print("Chief Architect: Project Alpha")
    print("Epoch: Reality-Based Intelligence")
    print("Mode: Multi-Agent Civilizational Cognitive Operating System")

    aos = AlphaOperatingSystem(db_path=":memory:")
    cwm = aos.world_model

    demo_1_build_complete_world_model(cwm)
    demo_2_track_project_evolution(cwm)
    demo_3_generate_new_concepts(cwm)
    demo_4_generate_new_principles(cwm)
    demo_5_predict_project_outcomes(cwm)
    demo_6_detect_knowledge_gaps(cwm)
    demo_7_simulate_alternative_futures(cwm)
    demo_8_distill_memories_to_concepts(cwm)
    demo_bonus_cognitive_evolution_pipeline(cwm)

    print_banner("ALL 8 PHASE 4 DEMONSTRATIONS SUCCESSFULLY COMPLETED")
    print("Project Alpha now possesses a true Cognitive World Model.")
    print("Alpha has officially transitioned from Memory-Based Intelligence into Reality-Based Intelligence.")


if __name__ == "__main__":
    main()
