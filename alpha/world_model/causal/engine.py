"""Causal Reasoning Engine: Master coordination of causal structures and analyses."""

from typing import Dict, Any, List, Optional
from alpha.world_model.causal.graphs import CauseGraph, EffectGraph, DependencyGraph, InfluenceNetwork, CausalLink
from alpha.world_model.causal.analysis import (
    CauseDetector,
    DependencyDiscovery,
    TemporalCorrelationAnalyzer,
    CounterfactualAnalyzer,
    RootCauseAnalyzer,
    ImpactPredictor,
)


class CausalReasoningEngine:
    """Provides high-level causal modeling, diagnosis, and prognostic inference."""

    def __init__(self):
        self.cause_graph = CauseGraph()
        self.effect_graph = EffectGraph(self.cause_graph)
        self.dependency_graph = DependencyGraph()
        self.influence_network = InfluenceNetwork()

        # Analysis sub-engines
        self.detector = CauseDetector()
        self.dependencies = DependencyDiscovery()
        self.temporal_analyzer = TemporalCorrelationAnalyzer()
        self.counterfactuals = CounterfactualAnalyzer(self.cause_graph)
        self.root_causes = RootCauseAnalyzer(self.cause_graph)
        self.impact = ImpactPredictor(self.cause_graph, self.influence_network)

    def register_causal_relation(
        self,
        cause_id: str,
        effect_id: str,
        strength: float = 1.0,
        mechanism: str = "direct",
        delay_seconds: float = 0.0,
        sign: int = 1
    ) -> CausalLink:
        """Register a verified causal mechanism."""
        link = CausalLink(
            cause_id=cause_id,
            effect_id=effect_id,
            strength=strength,
            mechanism=mechanism,
            time_delay_seconds=delay_seconds,
            sign=sign
        )
        return self.cause_graph.add_causal_link(link)

    def register_dependency(self, node_id: str, prerequisite_id: str) -> None:
        """Register a strict prerequisite relationship."""
        self.dependency_graph.add_dependency(node_id, prerequisite_id)

    def diagnose_root_causes(self, adverse_event_id: str) -> List[Dict[str, Any]]:
        """Run root cause analysis to identify initiating factors."""
        return self.root_causes.find_root_causes(adverse_event_id)

    def predict_change_impact(self, intervention_id: str, severity: float = 1.0) -> Dict[str, Any]:
        """Predict blast radius of intervening or mutating a system component."""
        return self.impact.predict_impact(intervention_id, severity=severity)

    def evaluate_counterfactual(self, cause_id: str, effect_id: str) -> Dict[str, Any]:
        """Test whether effect would occur without the specified cause."""
        return self.counterfactuals.simulate_counterfactual(cause_id, effect_id)
