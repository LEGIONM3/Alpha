"""Causal Analysis Capabilities: Detection, Dependencies, Temporal Correlation, Counterfactuals, Root Cause, Impact Prediction."""

from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx

from alpha.world_model.causal.graphs import CauseGraph, CausalLink, DependencyGraph, InfluenceNetwork


class CauseDetector:
    """Discovers potential causal mechanisms from event logs, precedence, and covariations."""

    def detect_candidate_causes(
        self,
        event_sequence: List[Dict[str, Any]],
        target_event_type: str,
        max_time_window_seconds: float = 60.0
    ) -> List[Dict[str, Any]]:
        """Identify event types that precede target events with high statistical consistency."""
        preceding_counts: Dict[str, int] = {}
        target_occurrences = 0

        # Sort events by timestamp
        sorted_events = sorted(event_sequence, key=lambda x: x.get("timestamp", 0.0))

        for i, ev in enumerate(sorted_events):
            if ev.get("event_type") == target_event_type:
                target_occurrences += 1
                t_target = ev.get("timestamp", 0.0)
                # Look backwards in window
                for j in range(i - 1, -1, -1):
                    prior = sorted_events[j]
                    dt = t_target - prior.get("timestamp", 0.0)
                    if dt > max_time_window_seconds:
                        break
                    p_type = prior.get("event_type", "unknown")
                    preceding_counts[p_type] = preceding_counts.get(p_type, 0) + 1

        if target_occurrences == 0:
            return []

        candidates = []
        for p_type, count in preceding_counts.items():
            support_ratio = count / target_occurrences
            if support_ratio >= 0.5:
                candidates.append({
                    "cause_event_type": p_type,
                    "target_event_type": target_event_type,
                    "correlation_ratio": round(support_ratio, 3),
                    "confidence": min(0.95, round(support_ratio * 0.9, 2))
                })
        return sorted(candidates, key=lambda x: x["correlation_ratio"], reverse=True)


class DependencyDiscovery:
    """Discovers critical paths, single points of failure, and transitive dependencies."""

    def find_critical_path(self, dependency_graph: DependencyGraph) -> List[str]:
        """Compute the longest dependency chain in the DAG."""
        g = dependency_graph.to_networkx()
        if not nx.is_directed_acyclic_graph(g) or len(g) == 0:
            return []
        try:
            return nx.dag_longest_path(g)
        except Exception:
            return []

    def find_single_points_of_failure(self, dependency_graph: DependencyGraph) -> List[str]:
        """Identify nodes whose removal disconnects critical paths or impacts multiple dependents."""
        spofs = []
        for prereq, dependents in dependency_graph._dependents.items():
            if len(dependents) >= 2:
                spofs.append(prereq)
        return spofs


class TemporalCorrelationAnalyzer:
    """Analyzes temporal precedence and delay distributions between events A and B."""

    def compute_correlation(
        self,
        event_a_timestamps: List[float],
        event_b_timestamps: List[float],
        tolerance_seconds: float = 30.0
    ) -> Dict[str, Any]:
        if not event_a_timestamps or not event_b_timestamps:
            return {"correlation": 0.0, "avg_delay": 0.0, "sample_size": 0}

        matches = 0
        delays = []
        for ta in event_a_timestamps:
            # Check if an event B occurred shortly after A
            for tb in event_b_timestamps:
                if 0.0 <= (tb - ta) <= tolerance_seconds:
                    matches += 1
                    delays.append(tb - ta)
                    break

        correlation = matches / len(event_a_timestamps)
        avg_delay = sum(delays) / max(1, len(delays))

        return {
            "correlation": round(correlation, 3),
            "avg_delay": round(avg_delay, 3),
            "sample_size": len(delays)
        }


class CounterfactualAnalyzer:
    """Evaluates Pearl-style counterfactual interventions: do(not X) -> does Y still happen?"""

    def __init__(self, cause_graph: CauseGraph):
        self.cause_graph = cause_graph

    def simulate_counterfactual(
        self,
        intervened_cause_id: str,
        target_effect_id: str
    ) -> Dict[str, Any]:
        """Simulate removing/suppressing a cause to determine whether effect would still occur."""
        g = self.cause_graph.to_networkx()
        if not g.has_node(intervened_cause_id) or not g.has_node(target_effect_id):
            return {
                "intervention": f"do(not {intervened_cause_id})",
                "effect_occurs": True,
                "counterfactual_probability": 0.5,
                "notes": "Nodes not in causal graph"
            }

        # Check if there are alternative paths to target_effect_id from other original root causes
        g_intervened = g.copy()
        g_intervened.remove_node(intervened_cause_id)

        # Roots in the original causal graph excluding the intervened cause
        original_roots = [n for n, d in g.in_degree() if d == 0 and n != intervened_cause_id and n != target_effect_id]
        alternative_path_exists = False
        for r in original_roots:
            if g_intervened.has_node(r) and nx.has_path(g_intervened, r, target_effect_id):
                alternative_path_exists = True
                break

        if not alternative_path_exists:
            # Without cause X, effect Y does NOT occur
            return {
                "intervention": f"do(not {intervened_cause_id})",
                "effect_occurs": False,
                "counterfactual_probability": 0.05,
                "causal_necessity": "necessary",
                "explanation": f"{intervened_cause_id} was strictly necessary for {target_effect_id}."
            }
        else:
            return {
                "intervention": f"do(not {intervened_cause_id})",
                "effect_occurs": True,
                "counterfactual_probability": 0.75,
                "causal_necessity": "contingent",
                "explanation": f"Alternative causal paths exist leading to {target_effect_id}."
            }


class RootCauseAnalyzer:
    """Traces upstream backwards from an adverse symptom to root causal origins."""

    def __init__(self, cause_graph: CauseGraph):
        self.cause_graph = cause_graph

    def find_root_causes(self, symptom_id: str) -> List[Dict[str, Any]]:
        g = self.cause_graph.to_networkx()
        if not g.has_node(symptom_id):
            return []

        # Find all ancestor nodes
        ancestors = nx.ancestors(g, symptom_id)
        if not ancestors:
            return [{"node_id": symptom_id, "is_direct_origin": True, "depth": 0}]

        # Roots are ancestors with in-degree 0 in the subgraph
        root_nodes = []
        for anc in ancestors:
            if g.in_degree(anc) == 0:
                try:
                    shortest_p = nx.shortest_path(g, anc, symptom_id)
                    root_nodes.append({
                        "node_id": anc,
                        "path_to_symptom": shortest_p,
                        "distance": len(shortest_p) - 1,
                        "significance": 1.0 / max(1, len(shortest_p) - 1)
                    })
                except nx.NetworkXNoPath:
                    pass

        return sorted(root_nodes, key=lambda x: x["distance"])


class ImpactPredictor:
    """Predicts forward blast radius and ripple severity of changes or failures."""

    def __init__(self, cause_graph: CauseGraph, influence_net: Optional[InfluenceNetwork] = None):
        self.cause_graph = cause_graph
        self.influence_net = influence_net or InfluenceNetwork()

    def predict_impact(self, trigger_node_id: str, severity: float = 1.0) -> Dict[str, Any]:
        g = self.cause_graph.to_networkx()
        if not g.has_node(trigger_node_id):
            return {
                "trigger": trigger_node_id,
                "affected_nodes": [],
                "total_impact_score": 0.0,
                "blast_radius": 0
            }

        descendants = nx.descendants(g, trigger_node_id)
        affected = []
        total_impact = severity

        for desc in descendants:
            paths = list(nx.all_simple_paths(g, trigger_node_id, desc, cutoff=4))
            max_attenuation = 0.0
            for path in paths:
                atten = severity
                for u, v in zip(path[:-1], path[1:]):
                    atten *= g[u][v].get("strength", 0.8)
                max_attenuation = max(max_attenuation, atten)

            affected.append({
                "node_id": desc,
                "predicted_severity": round(max_attenuation, 3),
                "shortest_distance": nx.shortest_path_length(g, trigger_node_id, desc)
            })
            total_impact += max_attenuation

        return {
            "trigger": trigger_node_id,
            "affected_nodes": sorted(affected, key=lambda x: x["predicted_severity"], reverse=True),
            "total_impact_score": round(total_impact, 3),
            "blast_radius": len(descendants)
        }
