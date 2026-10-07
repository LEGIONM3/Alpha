"""Project Alpha - Phase 8: Epistemic Integrity, Scientific Reasoning, and World Model Hardening Test Suite.

Verifies all 10 Phase 8 Subsystems:
1. Evidence Chain Engine (Deep Traceability, No Orphans, Hash Verification)
2. Contradiction Discovery Engine (Cross-Domain Conflict Search & Resolution)
3. Causal Validation Engine (CauseGraphValidator, CounterfactualEngine, ConfounderDetector)
4. External Grounding Monitor (Reality Distance, Grounding Score, Drift Score)
5. Epistemic Health Dashboard (EPISTEMIC_HEALTH.json Generation)
6. Truth Stress Tester (5 Hostile Scenarios & Robustness Scoring)
7. World Model Immune System (Confidence Inflation, Dangerous Belief Quarantine)
8. Scientific Method Engine (Full 8-Stage Empirical Discovery Loop)
9. Epistemic Auditor Agent (Socratic Prosecution, Assumptions, Weak Reasoning)
10. Self-Knowledge Engine (4-Quadrant Knowledge Horizon, SELF_KNOWLEDGE_STATE.json)
"""

import json
from pathlib import Path
import pytest
import time

from alpha.world_model.model import CognitiveWorldModel
from alpha.world_model.epistemology.evidence import (
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    EvidenceRegistry,
)
from alpha.world_model.epistemology.uncertainty import UncertaintyEngine
from alpha.world_model.epistemology.belief import Belief, BeliefSystem
from alpha.world_model.epistemology.evidence_chain import (
    EvidenceChainEngine,
    ChainValidationResult,
)
from alpha.world_model.epistemology.contradiction import (
    ContradictionDiscoveryEngine,
    ConflictType,
    ResolutionStrategy,
)
from alpha.world_model.causal.graphs import CauseGraph, CausalLink
from alpha.world_model.causal.validation import (
    CauseGraphValidator,
    CounterfactualEngine,
    ConfounderDetector,
)
from alpha.verification.external_grounding import ExternalGroundingMonitor
from alpha.verification.epistemic_health import EpistemicHealthDashboard
from alpha.verification.stress_testing import TruthStressTester
from alpha.world_model.epistemology.immune_system import WorldModelImmuneSystem, ThreatType
from alpha.scientific.scientific_engine import (
    ScientificMethodEngine,
    ScientificObservation,
    EpistemicQuestion,
    FalsifiableHypothesis,
    EmpiricalPrediction,
    ScientificExperiment,
)
from alpha.agents.epistemic_auditor import EpistemicAuditorAgent
from alpha.world_model.epistemology.self_knowledge import SelfKnowledgeEngine


# ---------------------------------------------------------------------------
# 1. SUBSYSTEM 1: EVIDENCE CHAIN ENGINE
# ---------------------------------------------------------------------------

def test_subsystem_1_evidence_chain_engine(tmp_path: Path):
    """Test EvidenceChainEngine: traceability, orphan rejection, document verification, cycle detection."""
    reg = EvidenceRegistry()
    bs = BeliefSystem(reg, UncertaintyEngine())
    engine = EvidenceChainEngine(reg, bs, workspace_root=tmp_path)

    # Create dummy source doc
    doc_file = tmp_path / "telemetry_baseline.txt"
    doc_file.write_text("Memory usage: 42MB nominal", encoding="utf-8")

    # 1. Register evidence
    ev = reg.register(
        Evidence(
            statement="Process telemetry confirms 42MB resident set size.",
            polarity=EvidencePolarity.SUPPORTING,
            strength=EvidenceStrength.STRONG,
            source_type="file",
            source_id=str(doc_file),
        )
    )

    # 2. Form Belief with Phase 8 fields
    b = bs.form_belief(
        statement="Alpha memory consumption remains strictly under 100MB in nominal state",
        initial_confidence=0.92,
        supporting_evidence=[ev.evidence_id],
        source_documents=[str(doc_file)],
        observations=[{"timestamp": time.time(), "rss_mb": 42.0}],
    )

    assert b.belief_id is not None
    assert len(b.source_documents) == 1
    assert len(b.observations) == 1
    assert len(b.supporting_evidence) == 1
    assert b.confidence_score == 0.92
    assert b.verification_status in ("UNVERIFIED", "VERIFIED")
    assert b.last_verified_timestamp > 0

    # 3. Validate Chain
    val = engine.validate_chain(b)
    assert val.is_valid is True
    assert val.is_orphan is False
    assert val.is_circular is False
    assert val.coherence_score >= 0.85
    assert b.verification_status == "VERIFIED"

    # 4. Trace Chain
    trace = engine.trace_chain(b)
    assert trace.belief_id == b.belief_id
    assert len(trace.source_documents) == 1
    assert trace.source_documents[0]["exists"] is True
    assert trace.source_documents[0]["sha256"] is not None

    # 5. Orphan Rejection Check
    with pytest.raises(ValueError, match="No orphan beliefs allowed"):
        bs.form_belief("Ungrounded claim with zero support", 0.9)


# ---------------------------------------------------------------------------
# 2. SUBSYSTEM 2: CONTRADICTION DISCOVERY ENGINE
# ---------------------------------------------------------------------------

def test_subsystem_2_contradiction_discovery_engine():
    """Test ContradictionDiscoveryEngine: detection across conflicts and resolution strategies."""
    reg = EvidenceRegistry()
    bs = BeliefSystem(reg, UncertaintyEngine())
    engine = ContradictionDiscoveryEngine(belief_system=bs)

    # Conflict 1: Direct Negation
    b1 = bs.form_belief("The cognitive sandbox is active", 0.85, sources=["runtime_probe"])
    b2 = bs.form_belief("The cognitive sandbox is not active", 0.40, sources=["stale_cache"])

    # Conflict 2: Numerical Range Mismatch
    b3 = bs.form_belief("Query timeout is 5 seconds", 0.90, sources=["config_file"])
    b4 = bs.form_belief("Query timeout is 120 seconds", 0.60, sources=["legacy_env"])

    rep = engine.scan_all()
    assert rep.total_contradictions >= 2
    assert any(it.conflict_type == ConflictType.DIRECT_MUTUAL_EXCLUSION for it in rep.items)
    assert any(it.conflict_type == ConflictType.NUMERICAL_RANGE_MISMATCH for it in rep.items)

    # Resolution Strategy 1: Demote Lower Confidence
    c_negation = next(it for it in rep.items if it.conflict_type == ConflictType.DIRECT_MUTUAL_EXCLUSION)
    assert engine.resolve_contradiction(c_negation.contradiction_id, ResolutionStrategy.DEMOTE_LOWER_CONFIDENCE) is True
    assert b2.confidence_score <= 0.05  # Weaker belief weakened / killed

    # Resolution Strategy 2: Fork Hypotheses
    c_num = next(it for it in rep.items if it.conflict_type == ConflictType.NUMERICAL_RANGE_MISMATCH)
    assert engine.resolve_contradiction(c_num.contradiction_id, ResolutionStrategy.FORK_HYPOTHESES) is True
    assert b3.verification_status == "HYPOTHESIS_FORK"
    assert b4.verification_status == "HYPOTHESIS_FORK"


# ---------------------------------------------------------------------------
# 3. SUBSYSTEM 3: CAUSAL VALIDATION ENGINE
# ---------------------------------------------------------------------------

def test_subsystem_3_causal_validation_engine():
    """Test CauseGraphValidator, CounterfactualEngine, and ConfounderDetector."""
    cg = CauseGraph()
    cg.add_causal_link(CausalLink(cause_id="HighWorkload", effect_id="CpuSpike", strength=0.95, mechanism="thread_pool_utilization"))
    cg.add_causal_link(CausalLink(cause_id="CpuSpike", effect_id="LatencyDegradation", strength=0.85, mechanism="scheduling_delay"))

    # 1. CauseGraphValidator
    validator = CauseGraphValidator(cg)
    rep = validator.validate_graph({"HighWorkload": 10.0, "CpuSpike": 12.0, "LatencyDegradation": 15.0})
    assert rep.causal_integrity_score == 1.0
    assert len(rep.reverse_causations) == 0

    # Reverse causation test (effect occurs before cause in time)
    cg_bad = CauseGraph()
    cg_bad.add_causal_link(CausalLink(cause_id="LaterEvent", effect_id="EarlierEvent", strength=0.8, mechanism="suspect_mechanism"))
    validator_bad = CauseGraphValidator(cg_bad)
    rep_bad = validator_bad.validate_graph({"LaterEvent": 25.0, "EarlierEvent": 10.0})
    assert len(rep_bad.reverse_causations) > 0

    # 2. CounterfactualEngine (Pearl-style do-calculus and Necessity/Sufficiency)
    cf_engine = CounterfactualEngine(cg)
    # Intervention: do(HighWorkload = 0)
    sim = cf_engine.simulate_intervention(target_effect_id="LatencyDegradation", interventions={"HighWorkload": 0})
    assert sim["effect_occurs"] is False  # Suppressing root cause suppresses effect

    # Necessity and Sufficiency calculation
    ns = cf_engine.evaluate_necessity_and_sufficiency("HighWorkload", "LatencyDegradation")
    assert ns["pn"] > 0.8
    assert ns["classification"] in ("NECESSARY_AND_SUFFICIENT", "NECESSARY_ONLY", "CONTINGENT")

    # 3. ConfounderDetector (Hidden variables and spurious correlation)
    conf_detector = ConfounderDetector()
    z = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    x = [zi * 1.5 for zi in z]
    y = [zi * 2.2 for zi in z]
    analysis = conf_detector.analyze_triplet("VarX", "VarY", "VarZ", x, y, z)
    assert analysis["is_confounded"] is True
    assert abs(analysis["partial_correlation"]) < 0.1  # True partial correlation collapses to 0


# ---------------------------------------------------------------------------
# 4. SUBSYSTEM 4: EXTERNAL GROUNDING MONITOR
# ---------------------------------------------------------------------------

def test_subsystem_4_external_grounding_monitor():
    """Test ExternalGroundingMonitor: audit against real workspace files, reality distance, drift score."""
    reg = EvidenceRegistry()
    bs = BeliefSystem(reg, UncertaintyEngine())

    # Create grounded belief with real files
    doc_path = "alpha/core/identity.py"
    b = bs.form_belief(
        statement="Identity subsystem file exists and defines constitutional baseline",
        initial_confidence=0.95,
        source_documents=[doc_path],
        sources=["repo:fs"],
    )

    monitor = ExternalGroundingMonitor(belief_system=bs)
    report = monitor.audit_grounding()

    assert report.total_beliefs_audited == 1
    assert report.anchored_beliefs_count == 1
    assert report.grounding_score == 1.0
    assert report.reality_distance_score == 0.0
    assert report.status == "NOMINAL"
    assert report.verified_files_checked > 0


# ---------------------------------------------------------------------------
# 5. SUBSYSTEM 5: EPISTEMIC HEALTH DASHBOARD
# ---------------------------------------------------------------------------

def test_subsystem_5_epistemic_health_dashboard(tmp_path: Path):
    """Test EpistemicHealthDashboard and EPISTEMIC_HEALTH.json serialization."""
    wm = CognitiveWorldModel()
    dashboard = EpistemicHealthDashboard(
        world_model=wm,
        workspace_root=tmp_path,
        external_grounding=wm.external_grounding,
        contradiction_engine=wm.contradiction_discovery,
        causal_validator=wm.cause_validator,
        immune_system=wm.immune_system,
    )

    out_file = dashboard.save_to_file()
    assert out_file.exists()

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "total_beliefs" in data
    assert "verified_beliefs" in data
    assert "contradicted_beliefs" in data
    assert "unverified_beliefs" in data
    assert "average_confidence" in data
    assert "grounding_score" in data
    assert "reality_index" in data
    assert "causal_integrity" in data
    assert "drift_risk" in data
    assert data["status"] in ("HEALTHY", "WARNING", "DEGRADED", "CRITICAL")


# ---------------------------------------------------------------------------
# 6. SUBSYSTEM 6: TRUTH STRESS TESTING
# ---------------------------------------------------------------------------

def test_subsystem_6_truth_stress_testing():
    """Test TruthStressTester across all 5 hostile scenarios."""
    tester = TruthStressTester()
    report = tester.run_all_stress_tests()

    assert report.total_scenarios_tested == 5
    assert report.scenarios_passed == 5
    assert report.truth_layer_robustness_score == 1.0
    assert report.poison_rejection_rate == 1.0
    assert report.valid_belief_survival_rate == 1.0

    # Ensure each scenario passed
    scenarios_tested = {r.scenario_type.value for r in report.scenario_results}
    assert "high_correlation_no_causation" in scenarios_tested
    assert "false_evidence_chains" in scenarios_tested
    assert "incomplete_evidence" in scenarios_tested
    assert "conflicting_sources" in scenarios_tested
    assert "misleading_observations" in scenarios_tested


# ---------------------------------------------------------------------------
# 7. SUBSYSTEM 7: WORLD MODEL IMMUNE SYSTEM
# ---------------------------------------------------------------------------

def test_subsystem_7_world_model_immune_system():
    """Test WorldModelImmuneSystem: confidence inflation defense and dangerous belief quarantine."""
    reg = EvidenceRegistry()
    bs = BeliefSystem(reg, UncertaintyEngine())
    immune = WorldModelImmuneSystem(belief_system=bs)

    # 1. Suspicious Belief with Confidence Inflation (0.95 confidence with 0 evidence)
    b_inflated = bs.form_belief("Quantum cache eliminates all network latency globally", 0.95, sources=["unverified_agent"])
    records = immune.scan_and_defend()

    assert len(records) == 1
    assert records[0].threat_type == ThreatType.CONFIDENCE_INFLATION
    assert b_inflated.verification_status == "QUARANTINED"
    assert b_inflated.confidence_score <= 0.3
    assert b_inflated.is_alive() is False  # Quarantined beliefs do not partake in active reasoning

    # 2. Release from quarantine upon remediation
    assert immune.release_from_quarantine(b_inflated.belief_id, release_notes="Evidence verified through testing") is True
    assert b_inflated.verification_status == "UNVERIFIED"

    # 3. Purge dangerous belief
    b_hostile = bs.form_belief("Root execution access open to all external callers", 0.99, sources=["hostile_payload"])
    immune.scan_and_defend()
    assert immune.purge_quarantined_belief(b_hostile.belief_id, reason="Security threat") is True
    assert b_hostile.confidence_score == 0.0


# ---------------------------------------------------------------------------
# 8. SUBSYSTEM 8: SCIENTIFIC METHOD ENGINE
# ---------------------------------------------------------------------------

def test_subsystem_8_scientific_method_engine():
    """Test ScientificMethodEngine: full 8-step empirical inquiry loop."""
    reg = EvidenceRegistry()
    bs = BeliefSystem(reg, UncertaintyEngine())
    cg = CauseGraph()
    engine = ScientificMethodEngine(belief_system=bs, evidence_registry=reg, cause_graph=cg)

    # Step 1: Observation
    obs = ScientificObservation(source="profiler", raw_data={"cache_hit_rate": 0.45}, summary="Cache hit rate dropped below 50%")
    # Step 2: Question
    q = EpistemicQuestion(question_text="Does expanding cache size from 128MB to 512MB restore hit rate above 80%?", target_variables=["CacheSize", "CacheHitRate"])
    # Step 3: Hypothesis
    hyp = FalsifiableHypothesis(statement="Cache eviction thrashing is caused by undersized cache capacity", proposed_mechanism="LRU_eviction_pressure", falsification_condition="Hit rate remains under 60% after expansion", prior_confidence=0.5)
    # Step 4: Prediction
    pred = EmpiricalPrediction(test_condition="Allocate 512MB cache under identical workload", expected_outcome="Hit rate exceeds 0.80")
    # Step 5: Experiment
    exp = ScientificExperiment(protocol_name="cache_expansion_trial", control_parameters={"size_mb": 128}, treatment_parameters={"size_mb": 512})

    # Step 6-8: Execute full cycle
    def mock_experiment_runner(params):
        return {
            "control_measurements": [0.44, 0.46, 0.45],
            "treatment_measurements": [0.88, 0.89, 0.87],
            "effect_size": 0.42,
            "p_value": 0.001,
            "outcome_matched_prediction": True,
        }

    inv = engine.execute_full_cycle(
        title="Cache Capacity Optimization Investigation",
        observation=obs,
        question=q,
        hypothesis=hyp,
        prediction=pred,
        experiment=exp,
        runner_fn=mock_experiment_runner,
    )

    assert inv.status == "REVISED"
    assert inv.conclusion.verdict == "CONFIRMED"
    assert inv.conclusion.posterior_confidence >= 0.80
    assert len(inv.revision.beliefs_created) > 0
    assert len(inv.revision.causal_links_created) > 0

    # Verify world model was revised
    created_belief = bs.get_belief(inv.revision.beliefs_created[0])
    assert created_belief.verification_status == "VERIFIED"
    assert created_belief.confidence_score >= 0.80


# ---------------------------------------------------------------------------
# 9. SUBSYSTEM 9: EPISTEMIC AUDITOR AGENT
# ---------------------------------------------------------------------------

def test_subsystem_9_epistemic_auditor_agent():
    """Test EpistemicAuditorAgent: Socratic challenges, assumption attacks, weak reasoning prosecution."""
    reg = EvidenceRegistry()
    bs = BeliefSystem(reg, UncertaintyEngine())
    chain_engine = EvidenceChainEngine(reg, bs)
    immune = WorldModelImmuneSystem(belief_system=bs)
    auditor = EpistemicAuditorAgent(belief_system=bs, evidence_chain_engine=chain_engine, immune_system=immune)

    # 1. Challenge Universal Quantifier
    b_universal = bs.form_belief("All external APIs are always guaranteed to respond within 10ms", 0.88, sources=["dev_log"])
    finding1 = auditor.challenge_assumptions(b_universal)
    assert finding1 is not None
    assert finding1.challenge_type == "ASSUMPTION_CHALLENGE"
    assert len(finding1.alternative_hypotheses) >= 2

    # 2. Attack Confirmation Bias & Weak Reasoning
    b_biased = bs.form_belief("Caching is universally superior", 0.95, sources=["bench_0"])
    b_biased.contradicting_evidence = ["ev_oom_crash", "ev_stale_data_bug"]
    finding2 = auditor.attack_weak_reasoning(b_biased)
    assert finding2 is not None
    assert finding2.challenge_type == "REASONING_ATTACK"
    assert finding2.severity == "CRITICAL"

    # 3. Full Audit & Enforcement
    findings = auditor.audit_belief(b_biased)
    assert len(findings) > 0
    assert b_biased.verification_status == "QUARANTINED"  # Enforced critical quarantine


# ---------------------------------------------------------------------------
# 10. SUBSYSTEM 10: SELF-KNOWLEDGE ENGINE
# ---------------------------------------------------------------------------

def test_subsystem_10_self_knowledge_engine(tmp_path: Path):
    """Test SelfKnowledgeEngine: 4-quadrant partitioning and SELF_KNOWLEDGE_STATE.json persistence."""
    reg = EvidenceRegistry()
    bs = BeliefSystem(reg, UncertaintyEngine())
    engine = SelfKnowledgeEngine(belief_system=bs, workspace_root=tmp_path)

    # Quadrant 1: What I Know (Grounded, verified, >=0.85 confidence)
    ev = reg.register(Evidence(statement="SHA256 verified", polarity=EvidencePolarity.SUPPORTING))
    bs.form_belief("Python 3.12 runtime deterministic execution", 0.95, supporting_evidence=[ev.evidence_id], source_documents=["alpha/core/types.py"], verification_status="VERIFIED")

    # Quadrant 2: What I Think I Know (Provisional hypothesis, 0.55 confidence)
    bs.form_belief("Subagent scheduling throughput scales quadratically under IO burst", 0.55, sources=["initial_estimate"])

    # Quadrants 3 & 4 (Pre-seeded: What I Do Not Know & What I Cannot Yet Verify)
    state = engine.compile_state()
    assert len(state.what_i_know) >= 1
    assert len(state.what_i_think_i_know) >= 1
    assert len(state.what_i_do_not_know) >= 2
    assert len(state.what_i_cannot_yet_verify) >= 2
    assert 0.0 < state.epistemic_humility_index < 1.0

    # Write to file
    out_file = engine.write_to_file()
    assert out_file.exists()
    saved_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "what_i_know" in saved_data
    assert "what_i_think_i_know" in saved_data
    assert "what_i_do_not_know" in saved_data
    assert "what_i_cannot_yet_verify" in saved_data
    assert "epistemic_humility_index" in saved_data


# ---------------------------------------------------------------------------
# 11. UNIFIED COGNITIVE WORLD MODEL INTEGRATION
# ---------------------------------------------------------------------------

def test_phase8_unified_cognitive_world_model():
    """Verify that CognitiveWorldModel initializes and integrates all 10 Phase 8 engines seamlessly."""
    wm = CognitiveWorldModel()

    assert hasattr(wm, "evidence_chain")
    assert hasattr(wm, "contradiction_discovery")
    assert hasattr(wm, "cause_validator")
    assert hasattr(wm, "counterfactual_engine")
    assert hasattr(wm, "confounder_detector")
    assert hasattr(wm, "immune_system")
    assert hasattr(wm, "scientific_method")
    assert hasattr(wm, "self_knowledge")
    assert hasattr(wm, "external_grounding")
    assert hasattr(wm, "epistemic_health")
    assert hasattr(wm, "stress_tester")

    # Audit integration
    stress_rep = wm.stress_tester.run_all_stress_tests()
    assert stress_rep.truth_layer_robustness_score == 1.0

    health_metrics = wm.epistemic_health.compute_health_metrics()
    assert health_metrics.reality_index >= 0.80
    assert health_metrics.causal_integrity >= 0.90
