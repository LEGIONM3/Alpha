"""Causal Validation Engine: Empirical Verification of Mechanisms for Project Alpha (Phase 8).

Transforms correlation into rigorously validated causation.

Subsystems:
1. CauseGraphValidator: Checks acyclicity, temporal precedence, mechanistic grounding.
2. CounterfactualEngine: Formal Pearl-style counterfactuals (Necessity, Sufficiency, PNS).
3. ConfounderDetector: Detects false causation, reverse causation, confounders, and spurious correlations.
"""

from __future__ import annotations

import math
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

import networkx as nx

from alpha.world_model.causal.graphs import CauseGraph, CausalLink


class CausalValidationReport(BaseModel):
    """Formal audit report produced by the Causal Validation Engine."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    total_links_evaluated: int = 0
    valid_causal_links: int = 0
    causal_integrity_score: float = 1.0  # [0.0, 1.0]
    false_causations: List[Dict[str, Any]] = Field(default_factory=list)
    reverse_causations: List[Dict[str, Any]] = Field(default_factory=list)
    confounders_detected: List[Dict[str, Any]] = Field(default_factory=list)
    spurious_correlations: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class CauseGraphValidator:
    """Validates structural and temporal laws across the causal network."""

    def __init__(self, cause_graph: CauseGraph):
        self.cause_graph = cause_graph

    def validate_graph(
        self, temporal_timestamps: Optional[Dict[str, float]] = None
    ) -> CausalValidationReport:
        """Audit the cause graph for cycles, negative delays, and temporal ordering."""
        g = self.cause_graph.to_networkx()
        report = CausalValidationReport()
        report.total_links_evaluated = len(self.cause_graph._links)

        # 1. DAG Acyclicity
        if not nx.is_directed_acyclic_graph(g):
            try:
                cycles = list(nx.simple_cycles(g))
                for c in cycles:
                    report.false_causations.append({
                        "type": "CAUSAL_CYCLE",
                        "cycle": c,
                        "description": f"Cyclic causality detected: {' -> '.join(c)} -> {c[0]}",
                    })
                    report.warnings.append(f"Causal cycle detected: {c}")
            except Exception:
                report.warnings.append("Causal graph is cyclic.")

        # 2. Temporal Precedence Validation
        ts_map = temporal_timestamps or {}
        for link in self.cause_graph._links.values():
            # Check explicit link delay
            if link.time_delay_seconds < 0:
                report.reverse_causations.append({
                    "cause_id": link.cause_id,
                    "effect_id": link.effect_id,
                    "delay": link.time_delay_seconds,
                    "description": "Negative time delay indicates reverse causation.",
                })
                report.warnings.append(f"Negative delay in link {link.cause_id} -> {link.effect_id}")

            # Check timestamp ordering if available
            t_cause = ts_map.get(link.cause_id)
            t_effect = ts_map.get(link.effect_id)
            if t_cause is not None and t_effect is not None:
                if t_cause > t_effect:
                    report.reverse_causations.append({
                        "cause_id": link.cause_id,
                        "effect_id": link.effect_id,
                        "t_cause": t_cause,
                        "t_effect": t_effect,
                        "description": f"Temporal violation: Effect ({link.effect_id} at {t_effect}) preceded Cause ({link.cause_id} at {t_cause}).",
                    })
                    report.warnings.append(f"Reverse causation: {link.cause_id} occurred after {link.effect_id}")

            # Check mechanism presence
            if not link.mechanism or link.mechanism.strip() == "":
                report.warnings.append(f"Link {link.cause_id} -> {link.effect_id} lacks mechanistic grounding.")

        # Compute integrity score
        flawed_links = len(report.false_causations) + len(report.reverse_causations)
        valid_links = max(0, report.total_links_evaluated - flawed_links)
        report.valid_causal_links = valid_links
        report.causal_integrity_score = (
            round(valid_links / max(1, report.total_links_evaluated), 3)
            if report.total_links_evaluated > 0
            else 1.0
        )
        return report


class CounterfactualEngine:
    """Evaluates Pearl-style counterfactual queries: do(X = x) and Necessity/Sufficiency."""

    def __init__(self, cause_graph: CauseGraph):
        self.cause_graph = cause_graph

    def simulate_intervention(
        self,
        target_effect_id: str,
        interventions: Dict[str, Any],  # e.g. {"CauseA": 0} to suppress CauseA
    ) -> Dict[str, Any]:
        """Simulate intervention do(X = x) by mutilating the causal graph and propagating."""
        g = self.cause_graph.to_networkx()
        if not g.has_node(target_effect_id):
            return {
                "target_effect_id": target_effect_id,
                "effect_occurs": False,
                "probability": 0.0,
                "reason": "Target effect not found in causal network.",
            }

        # Pearlian graph mutilation: sever incoming edges to intervened nodes
        g_mutilated = g.copy()
        original_roots = [n for n, d in g.in_degree() if d == 0]

        for node, val in interventions.items():
            if g_mutilated.has_node(node):
                if val == 0:
                    # If suppressed, remove node and its downstream transmission
                    g_mutilated.remove_node(node)
                else:
                    in_edges = list(g_mutilated.in_edges(node))
                    g_mutilated.remove_edges_from(in_edges)

        # Active roots are original roots that were not suppressed
        active_roots = [r for r in original_roots if interventions.get(r, 1) != 0 and g_mutilated.has_node(r)]
        forced_active = [n for n, val in interventions.items() if val == 1 and g_mutilated.has_node(n)]
        effective_sources = list(set(active_roots + forced_active))

        has_active_path = (
            g_mutilated.has_node(target_effect_id)
            and any(nx.has_path(g_mutilated, src, target_effect_id) for src in effective_sources)
        )

        return {
            "target_effect_id": target_effect_id,
            "interventions": interventions,
            "effect_occurs": has_active_path,
            "counterfactual_probability": 0.95 if has_active_path else 0.05,
        }

    def evaluate_necessity_and_sufficiency(
        self,
        cause_id: str,
        effect_id: str,
        observations: Optional[List[Dict[str, int]]] = None,
    ) -> Dict[str, Any]:
        """Compute Probability of Necessity (PN), Probability of Sufficiency (PS), and PNS.

        Observations format: list of dicts with keys {cause_id: 0/1, effect_id: 0/1}
        """
        if not observations:
            # Fallback to structural analysis on graph
            g = self.cause_graph.to_networkx()
            if not g.has_node(cause_id) or not g.has_node(effect_id):
                return {
                    "cause_id": cause_id,
                    "effect_id": effect_id,
                    "pn": 0.0,
                    "ps": 0.0,
                    "pns": 0.0,
                    "classification": "NON_CAUSAL",
                }

            # If cause is the unique path to effect
            g_cut = g.copy()
            g_cut.remove_node(cause_id)
            roots = [n for n, d in g.in_degree() if d == 0 and n != cause_id]
            alt_path = any(nx.has_path(g_cut, r, effect_id) for r in roots if g_cut.has_node(r))
            pn = 0.95 if not alt_path else 0.40
            ps = 0.90
            pns = round(pn * ps, 3)
            classification = "NECESSARY_AND_SUFFICIENT" if pn > 0.8 and ps > 0.8 else "CONTINGENT"
            return {
                "cause_id": cause_id,
                "effect_id": effect_id,
                "pn": pn,
                "ps": ps,
                "pns": pns,
                "classification": classification,
            }

        # Empirical contingency table calculation
        n11 = sum(1 for o in observations if o.get(cause_id) == 1 and o.get(effect_id) == 1)
        n10 = sum(1 for o in observations if o.get(cause_id) == 1 and o.get(effect_id) == 0)
        n01 = sum(1 for o in observations if o.get(cause_id) == 0 and o.get(effect_id) == 1)
        n00 = sum(1 for o in observations if o.get(cause_id) == 0 and o.get(effect_id) == 0)

        total = len(observations)
        if total == 0:
            return {"pn": 0.0, "ps": 0.0, "pns": 0.0, "classification": "NO_DATA"}

        p_e_given_c = n11 / max(1, (n11 + n10))
        p_e_given_not_c = n01 / max(1, (n01 + n00))

        # Under monotonicity:
        # PN = (P(Y=1|X=1) - P(Y=1|X=0)) / P(Y=1|X=1)
        # PS = (P(Y=1|X=1) - P(Y=1|X=0)) / (1 - P(Y=1|X=0))
        # PNS = P(Y=1|X=1) - P(Y=1|X=0)
        risk_diff = max(0.0, p_e_given_c - p_e_given_not_c)
        pn = round(risk_diff / max(1e-4, p_e_given_c), 3) if p_e_given_c > 0 else 0.0
        ps = round(risk_diff / max(1e-4, (1.0 - p_e_given_not_c)), 3) if (1.0 - p_e_given_not_c) > 0 else 0.0
        pns = round(risk_diff, 3)

        pn = min(1.0, max(0.0, pn))
        ps = min(1.0, max(0.0, ps))

        if pn >= 0.75 and ps >= 0.75:
            classification = "NECESSARY_AND_SUFFICIENT"
        elif pn >= 0.75:
            classification = "NECESSARY_ONLY"
        elif ps >= 0.75:
            classification = "SUFFICIENT_ONLY"
        elif pns > 0.2:
            classification = "CONTINGENT"
        else:
            classification = "NON_CAUSAL"

        return {
            "cause_id": cause_id,
            "effect_id": effect_id,
            "sample_size": total,
            "pn": pn,
            "ps": ps,
            "pns": pns,
            "classification": classification,
        }


class ConfounderDetector:
    """Detects false causation, reverse causation, confounders, and spurious correlations."""

    @staticmethod
    def pearson_correlation(x: List[float], y: List[float]) -> float:
        """Compute Pearson correlation coefficient r between two series."""
        n = len(x)
        if n < 2 or len(y) != n:
            return 0.0
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        var_x = sum((xi - mean_x) ** 2 for xi in x)
        var_y = sum((yi - mean_y) ** 2 for yi in y)
        if var_x == 0 or var_y == 0:
            return 0.0
        cov_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        r = cov_xy / math.sqrt(var_x * var_y)
        return round(max(-1.0, min(1.0, r)), 4)

    @classmethod
    def partial_correlation(
        cls, x: List[float], y: List[float], z: List[float]
    ) -> float:
        """Compute partial correlation r(X, Y | Z) controlling for confounder Z."""
        r_xy = cls.pearson_correlation(x, y)
        r_xz = cls.pearson_correlation(x, z)
        r_yz = cls.pearson_correlation(y, z)

        denom = math.sqrt(max(1e-8, (1 - r_xz**2) * (1 - r_yz**2)))
        r_xy_z = (r_xy - (r_xz * r_yz)) / denom
        return round(max(-1.0, min(1.0, r_xy_z)), 4)

    def analyze_triplet(
        self,
        var_x_name: str,
        var_y_name: str,
        var_z_name: str,
        x_data: List[float],
        y_data: List[float],
        z_data: List[float],
    ) -> Dict[str, Any]:
        """Analyze if Z is a common cause / confounder creating a spurious correlation between X and Y."""
        r_xy = self.pearson_correlation(x_data, y_data)
        r_xz = self.pearson_correlation(x_data, z_data)
        r_yz = self.pearson_correlation(y_data, z_data)
        r_partial = self.partial_correlation(x_data, y_data, z_data)

        # Confounder criterion: High r_xy, high r_xz, high r_yz, but low r_partial
        is_confounded = False
        explanation = ""

        if abs(r_xy) >= 0.6 and abs(r_xz) >= 0.5 and abs(r_yz) >= 0.5:
            # Drop in correlation when conditioning on Z
            drop = abs(r_xy) - abs(r_partial)
            if drop >= 0.4 or abs(r_partial) < 0.25:
                is_confounded = True
                explanation = (
                    f"Confounder detected: Variable '{var_z_name}' accounts for the relationship between "
                    f"'{var_x_name}' and '{var_y_name}'. Raw r = {r_xy}, but conditioned on Z, partial r = {r_partial}."
                )

        return {
            "var_x": var_x_name,
            "var_y": var_y_name,
            "var_z": var_z_name,
            "raw_correlation": r_xy,
            "r_xz": r_xz,
            "r_yz": r_yz,
            "partial_correlation": r_partial,
            "is_confounded": is_confounded,
            "is_spurious": is_confounded,
            "explanation": explanation,
        }

    def detect_reverse_causation(
        self,
        var_x_name: str,
        var_y_name: str,
        timestamps_x: List[float],
        timestamps_y: List[float],
    ) -> Dict[str, Any]:
        """Determine whether purported Cause X actually occurs after Effect Y."""
        if not timestamps_x or not timestamps_y:
            return {"reverse_causation": False, "confidence": 0.0}

        avg_tx = sum(timestamps_x) / len(timestamps_x)
        avg_ty = sum(timestamps_y) / len(timestamps_y)

        if avg_tx > avg_ty:
            return {
                "purported_cause": var_x_name,
                "purported_effect": var_y_name,
                "reverse_causation": True,
                "mean_cause_time": round(avg_tx, 3),
                "mean_effect_time": round(avg_ty, 3),
                "time_difference": round(avg_tx - avg_ty, 3),
                "explanation": f"Reverse causation: '{var_y_name}' on average occurs {round(avg_tx - avg_ty, 2)}s before '{var_x_name}'.",
            }
        return {
            "purported_cause": var_x_name,
            "purported_effect": var_y_name,
            "reverse_causation": False,
            "time_difference": round(avg_ty - avg_tx, 3),
        }

    def detect_spurious_correlation(
        self,
        var_x_name: str,
        var_y_name: str,
        x_data: List[float],
        y_data: List[float],
        interventions_tested: bool = False,
        intervention_effect: float = 0.0,
    ) -> Dict[str, Any]:
        """Detect spurious correlation through intervention testing or small sample sizes."""
        r = self.pearson_correlation(x_data, y_data)
        is_spurious = False
        reason = ""

        # Test with small sample size
        if len(x_data) < 5 and abs(r) > 0.8:
            is_spurious = True
            reason = f"Small sample size (N={len(x_data)}) produces unreliable spurious correlation r={r}."

        # Test with empirical intervention: if correlation is high but intervention produces no delta
        if interventions_tested and abs(r) >= 0.7 and abs(intervention_effect) < 0.1:
            is_spurious = True
            reason = (
                f"Empirical intervention do({var_x_name}) failed to induce change in {var_y_name} "
                f"(effect size: {intervention_effect}) despite correlation r={r}."
            )

        return {
            "var_x": var_x_name,
            "var_y": var_y_name,
            "correlation": r,
            "is_spurious": is_spurious,
            "reason": reason,
        }
