"""Comprehensive Test Suite for Reality Integration Milestone.

Verifies:
1. Real ObservationEngine (AST parsing, doc inspection, log analysis, telemetry, zero replay)
2. Real ResearchEngine (code search, dependency tracing, doc citations, error detection)
3. Real KnowledgeGapDetector (untested modules, unknown subsystems, low confidence beliefs)
4. Real HypothesisEngine (falsifiable propositions, falsification conditions, verification plans)
5. Real BeliefRevisionEngine (Bayesian confidence updates, contradiction detection, ontology sync)
6. Real NovelKnowledgeScore (differential tracking, no manual incrementation)
7. End-to-End AlphaRuntimeCycle integration
"""

import pytest
from pathlib import Path

from alpha.observation_engine.engine import ObservationEngine, ObservationRecord
from alpha.research_engine.engine import ResearchEngine, ResearchFinding
from alpha.knowledge.detector import KnowledgeGapDetector, KnowledgeGap
from alpha.hypothesizing.engine import HypothesisEngine, Hypothesis
from alpha.knowledge.belief_reviser import BeliefRevisionEngine
from alpha.knowledge.metrics import NovelKnowledgeScore
from alpha.runtime_cycle import AlphaRuntimeCycle
from alpha.world_model import CognitiveWorldModel


def test_observation_engine_reality_and_deduplication():
    """Phase A: Verifies ObservationEngine acquires empirical records without replay."""
    engine = ObservationEngine()
    engine.reset_state()

    obs1 = engine.acquire_observations(targets=["codebase", "telemetry"])
    assert len(obs1) > 0
    assert all(isinstance(o, ObservationRecord) for o in obs1)
    assert all(len(o.hash) == 64 for o in obs1)  # SHA-256 hash
    assert all(o.confidence >= 0.5 for o in obs1)

    obs2 = engine.acquire_observations(targets=["codebase", "telemetry"])
    assert len(obs2) > 0

    # Ensure no hashes are duplicated across cycles
    hashes1 = {o.hash for o in obs1}
    hashes2 = {o.hash for o in obs2}
    assert hashes1.isdisjoint(hashes2), "ObservationEngine must never replay observed hashes!"


def test_research_engine_empirical_citations():
    """Phase B: Verifies ResearchEngine produces genuine code and doc citations."""
    engine = ResearchEngine()
    findings = engine.investigate("How does ontology registry validate entities in Project Alpha?")

    assert len(findings) > 0
    assert all(isinstance(f, ResearchFinding) for f in findings)
    assert all(len(f.citations) > 0 for f in findings)
    assert all(len(f.evidence) > 0 for f in findings)
    assert all(f.confidence > 0.5 for f in findings)
    assert any("alpha/" in c for f in findings for c in f.citations)


def test_knowledge_gap_detector_repository_audit():
    """Phase C: Verifies KnowledgeGapDetector detects empirical voids."""
    detector = KnowledgeGapDetector()
    wm = CognitiveWorldModel()
    engine = ObservationEngine()
    obs = engine.acquire_observations()

    gaps = detector.detect(observations=obs, world_model=wm)
    assert len(gaps) > 0
    assert all(isinstance(g, KnowledgeGap) for g in gaps)
    assert all(len(g.evidence) > 0 for g in gaps)
    assert all(1 <= g.urgency <= 5 for g in gaps)

    categories = {g.category for g in gaps}
    assert any(c in categories for c in ["untested_path", "unknown_module", "missing_causal_link", "unused_system", "missing_implementation", "highest_epistemic_investigation", "strategic_investigation", "contradiction"])


def test_hypothesis_engine_falsifiability():
    """Phase D: Verifies HypothesisEngine produces falsifiable hypotheses."""
    engine = HypothesisEngine()
    obs = [
        ObservationRecord(
            source="SourceCode:alpha/core/identity.py",
            timestamp="2026-10-07T00:00:00",
            confidence=0.99,
            content="Module alpha/core/identity.py contains ConstitutionEngine.",
            category="CodeStructure"
        )
    ]
    findings = [
        ResearchFinding(
            finding_summary="Untested module path detected in alpha/agents/communication/bus.py.",
            evidence=["alpha/agents/communication/bus.py:1: class MessageBus"],
            citations=["alpha/agents/communication/bus.py:1"],
            source_paths=["alpha/agents/communication/bus.py"],
            confidence=0.90
        )
    ]

    hyps = engine.generate_hypotheses(observations=obs, findings=findings)
    assert len(hyps) > 0
    assert all(isinstance(h, Hypothesis) for h in hyps)
    assert all(len(h.falsification_conditions) > 0 for h in hyps)
    assert all(len(h.verification_plan) > 0 for h in hyps)
    assert all(h.status == "PENDING_TEST" for h in hyps)


def test_belief_revision_epistemic_updates():
    """Phase E: Verifies BeliefRevisionEngine strengthens, weakens, and detects contradictions."""
    wm = CognitiveWorldModel()
    reviser = BeliefRevisionEngine(world_model=wm)

    # 1. Strengthening
    b = wm.form_belief("Formal AST validators prevent arbitrary corruption.", initial_confidence=0.60, sources=["system"])
    initial_conf = b.confidence

    support_finding = ResearchFinding(
        finding_summary="AST validators prevent arbitrary corruption in sandbox executions.",
        evidence=["alpha/world_model/model.py:255"],
        citations=["alpha/world_model/model.py:255"],
        source_paths=["alpha/world_model/model.py"],
        confidence=0.95
    )

    reviser.revise_world_model(world_model=wm, findings=[support_finding])
    assert b.confidence > initial_conf

    # 2. Contradiction & Weakening
    b_contra = wm.form_belief("The bus module is fully verified and stable.", initial_confidence=0.80, sources=["seed"])
    contra_finding = ResearchFinding(
        finding_summary="The bus module is untested and has failure risk.",
        evidence=["alpha/agents/communication/bus.py:1"],
        citations=["alpha/agents/communication/bus.py:1"],
        source_paths=["alpha/agents/communication/bus.py"],
        confidence=0.95
    )

    _, contradictions = reviser.revise_world_model(world_model=wm, findings=[contra_finding])
    assert len(contradictions) >= 1
    assert b_contra.confidence < 0.80


def test_novel_knowledge_score_differentials():
    """Phase F: Verifies NovelKnowledgeScore strictly tracks runtime activity differentials."""
    scorer = NovelKnowledgeScore()
    scorer.reset_state()

    obs = [
        ObservationRecord(source="A", timestamp="2026-10-07T00:00:00", content="Data 1", category="Code"),
        ObservationRecord(source="B", timestamp="2026-10-07T00:00:00", content="Data 2", category="Code"),
    ]
    findings = [
        ResearchFinding(finding_summary="Fact 1", evidence=["evidence"], citations=["f:1"], source_paths=["f"], confidence=0.9)
    ]

    score1 = scorer.record_runtime_activity(observations=obs, findings=findings)
    assert score1 > 0
    m1 = scorer.get_current_metrics()
    assert m1.new_observations_count == 2
    assert m1.new_findings_count == 1

    # Exact replay does not increase score
    score2 = scorer.record_runtime_activity(observations=obs, findings=findings)
    assert score2 == score1


def test_runtime_cycle_operational_execution():
    """Phase G Preview: Verifies single cycle execution of AlphaRuntimeCycle."""
    cycle = AlphaRuntimeCycle(verbose=False)
    result = cycle.run_cycle()

    assert result["success"] is True
    assert result["observations_count"] > 0
    assert result["findings_count"] > 0
    assert result["hypotheses_count"] > 0
    assert result["beliefs_count"] > 0
    assert result["learning_score"] > 0
