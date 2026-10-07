"""Tests for Epistemology, Belief System, Evidence Engine, and Uncertainty (Parts 3, 4, 12)."""

import pytest
import time
from alpha.world_model.epistemology import (
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    EvidenceRegistry,
    EvidenceRankingSystem,
    EvidenceAggregator,
    UncertaintyLevel,
    UncertaintyEngine,
    CalibratedEstimate,
    Belief,
    BeliefSystem,
)
from alpha.world_model.ontology import LifecycleState


def test_evidence_registry_ranking_and_aggregation():
    """Verify evidence registration, ranking, and aggregation."""
    registry = EvidenceRegistry()
    ranker = EvidenceRankingSystem()
    aggregator = EvidenceAggregator(ranker)

    ev1 = Evidence(
        statement="Unit tests passed with 100% coverage",
        polarity=EvidencePolarity.SUPPORTING,
        strength=EvidenceStrength.STRONG,
        source_type="code_test"
    )
    ev2 = Evidence(
        statement="Manual review noted occasional memory spike",
        polarity=EvidencePolarity.CONTRADICTING,
        strength=EvidenceStrength.WEAK,
        source_type="log_metric"
    )
    registry.register(ev1)
    registry.register(ev2)

    assert registry.get(ev1.evidence_id) is not None
    assert registry.get(ev2.evidence_id) is not None

    ranked = ranker.rank([ev1, ev2])
    assert ranked[0].evidence_id == ev1.evidence_id  # Strong code_test outranks weak log_metric

    agg = aggregator.aggregate([ev1, ev2])
    assert agg["support_count"] == 1
    assert agg["contradict_count"] == 1
    assert agg["recommended_confidence"] > 0.5


def test_no_orphan_beliefs_enforcement():
    """Verify strict epistemic rule: No orphan beliefs allowed without evidence or sources."""
    registry = EvidenceRegistry()
    uncertainty = UncertaintyEngine()
    beliefs = BeliefSystem(registry, uncertainty)

    # Missing evidence and sources should raise ValueError
    with pytest.raises(ValueError, match="No orphan beliefs allowed"):
        beliefs.form_belief("Arbitrary ungrounded claim", initial_confidence=0.9, evidence_ids=[], sources=[])

    # With evidence
    ev = registry.register(Evidence(statement="Formal proof verified", source_id="math_core"))
    b = beliefs.form_belief("Formal proof holds", initial_confidence=0.95, evidence_ids=[ev.evidence_id])
    assert b.statement == "Formal proof holds"
    assert b.confidence == 0.95


def test_belief_evolution_strengthen_weaken_decay_death():
    """Verify belief evolution: strengthening, weakening, decay over time, and death."""
    registry = EvidenceRegistry()
    uncertainty = UncertaintyEngine()
    beliefs = BeliefSystem(registry, uncertainty)

    ev_sup = registry.register(Evidence(statement="Observation confirms theory", polarity=EvidencePolarity.SUPPORTING))
    b = beliefs.form_belief("System stabilizes under load", initial_confidence=0.5, evidence_ids=[ev_sup.evidence_id])

    # 1. Strengthen
    old_conf = b.confidence
    b.strengthen("ev_new_sup", delta=0.2)
    assert b.confidence > old_conf
    assert len(b.verification_history) == 1

    # 2. Weaken
    b.weaken("ev_contra_01", penalty=0.3)
    assert b.confidence < 0.65

    # 3. Decay
    b.decay_rate = 0.05
    b.apply_decay(elapsed_seconds=120.0)
    assert b.confidence < 0.60

    # 4. Death
    b.weaken("ev_fatal_contra", penalty=0.7)
    assert b.confidence == 0.0
    assert b.lifecycle_state == LifecycleState.DEAD
    assert b.is_alive() is False


def test_uncertainty_engine_representation_and_calibration():
    """Verify UncertaintyLevel mapping, interval bounds, and combination rules."""
    engine = UncertaintyEngine()

    assert engine.classify_confidence(0.0) == UncertaintyLevel.IMPOSSIBLE
    assert engine.classify_confidence(0.08) == UncertaintyLevel.UNKNOWN
    assert engine.classify_confidence(0.25) == UncertaintyLevel.UNLIKELY
    assert engine.classify_confidence(0.55) == UncertaintyLevel.PARTIALLY_KNOWN
    assert engine.classify_confidence(0.75) == UncertaintyLevel.LIKELY
    assert engine.classify_confidence(0.95) == UncertaintyLevel.CERTAIN

    # Bound estimation: lower confidence -> wider bounds
    bounds_high = engine.compute_bounds(0.9, 0.95)
    bounds_low = engine.compute_bounds(0.9, 0.20)
    width_high = bounds_high[1] - bounds_high[0]
    width_low = bounds_low[1] - bounds_low[0]
    assert width_low > width_high

    # Evaluate claim
    claim = engine.evaluate_claim("Cache hits stay above 90%", 0.85, rationale="Observed in 100 runs")
    assert claim.uncertainty_level == UncertaintyLevel.CERTAIN
    assert claim.confidence == 0.85

    # Conjunction & Disjunction
    conj = engine.combine_independent_uncertainties(0.8, 0.9)
    assert conj == 0.72

    disj = engine.combine_disjunctive_uncertainties(0.5, 0.5)
    assert disj == 0.75
