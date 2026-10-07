"""Tests for Causal Reasoning Engine (Part 5)."""

import pytest
from alpha.world_model.causal import (
    CausalLink,
    CauseGraph,
    EffectGraph,
    DependencyGraph,
    InfluenceNetwork,
    CauseDetector,
    DependencyDiscovery,
    TemporalCorrelationAnalyzer,
    CounterfactualAnalyzer,
    RootCauseAnalyzer,
    ImpactPredictor,
    CausalReasoningEngine,
)


def test_cause_and_effect_graph_forward_tracing():
    """Verify forward tracing of downstream ripple effects."""
    cg = CauseGraph()
    eg = EffectGraph(cg)

    # Link: HighMemory -> Throttling -> LatencySpike -> FailedRequests
    cg.add_causal_link(CausalLink(cause_id="HighMemory", effect_id="Throttling", strength=0.9))
    cg.add_causal_link(CausalLink(cause_id="Throttling", effect_id="LatencySpike", strength=0.8))
    cg.add_causal_link(CausalLink(cause_id="LatencySpike", effect_id="FailedRequests", strength=0.7))

    effects = eg.trace_effects("HighMemory", max_depth=4)
    assert "Throttling" in effects
    assert "LatencySpike" in effects
    assert "FailedRequests" in effects
    assert effects["Throttling"]["depth"] == 1
    assert effects["FailedRequests"]["depth"] == 3


def test_dependency_graph_topological_sort_and_critical_path():
    """Verify dependency DAG ordering, critical path, and SPOF detection."""
    dg = DependencyGraph()
    discovery = DependencyDiscovery()

    # Step1 -> Step2 -> Step3; Step1 -> Step4
    dg.add_dependency("Step2", "Step1")
    dg.add_dependency("Step3", "Step2")
    dg.add_dependency("Step4", "Step1")

    order = dg.topological_order()
    assert order.index("Step1") < order.index("Step2")
    assert order.index("Step2") < order.index("Step3")

    crit_path = discovery.find_critical_path(dg)
    assert crit_path == ["Step1", "Step2", "Step3"]

    spofs = discovery.find_single_points_of_failure(dg)
    assert "Step1" in spofs  # Step1 has 2 dependents


def test_cause_detection_from_event_stream():
    """Verify detecting candidate causes from temporal event sequences."""
    detector = CauseDetector()

    events = [
        {"timestamp": 10.0, "event_type": "DbConnectionSpike"},
        {"timestamp": 12.0, "event_type": "TimeoutError"},
        {"timestamp": 30.0, "event_type": "DbConnectionSpike"},
        {"timestamp": 33.0, "event_type": "TimeoutError"},
        {"timestamp": 50.0, "event_type": "CacheEviction"},
        {"timestamp": 55.0, "event_type": "TimeoutError"},
    ]

    candidates = detector.detect_candidate_causes(events, target_event_type="TimeoutError", max_time_window_seconds=10.0)
    assert len(candidates) > 0
    top = candidates[0]
    assert top["cause_event_type"] == "DbConnectionSpike"
    assert top["correlation_ratio"] >= 0.6


def test_counterfactual_analysis():
    """Verify Pearl-style counterfactual analysis: do(not X) -> Y?"""
    cg = CauseGraph()
    analyzer = CounterfactualAnalyzer(cg)

    # CauseA -> EffectB
    cg.add_causal_link(CausalLink(cause_id="CauseA", effect_id="EffectB", strength=1.0))

    res = analyzer.simulate_counterfactual("CauseA", "EffectB")
    assert res["effect_occurs"] is False
    assert res["causal_necessity"] == "necessary"


def test_root_cause_analysis():
    """Verify backward diagnostic tracing from symptoms to root origins."""
    cg = CauseGraph()
    rca = RootCauseAnalyzer(cg)

    # RootOrigin -> IntermediateService -> SymptomFailure
    cg.add_causal_link(CausalLink(cause_id="RootOrigin", effect_id="IntermediateService", strength=0.9))
    cg.add_causal_link(CausalLink(cause_id="IntermediateService", effect_id="SymptomFailure", strength=0.9))

    roots = rca.find_root_causes("SymptomFailure")
    assert len(roots) >= 1
    assert roots[0]["node_id"] == "RootOrigin"
    assert roots[0]["distance"] == 2


def test_impact_prediction():
    """Verify forward cascade calculation of downstream ripple effects and blast radius."""
    cg = CauseGraph()
    predictor = ImpactPredictor(cg)

    cg.add_causal_link(CausalLink(cause_id="CoreModule", effect_id="ServiceA", strength=0.8))
    cg.add_causal_link(CausalLink(cause_id="ServiceA", effect_id="ClientUI", strength=0.7))

    impact = predictor.predict_impact("CoreModule", severity=1.0)
    assert impact["blast_radius"] == 2
    assert len(impact["affected_nodes"]) == 2
    assert impact["affected_nodes"][0]["node_id"] == "ServiceA"
