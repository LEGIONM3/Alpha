"""Predictive Model Simulator: Digital twin forecasting model behavior before execution."""

from typing import List, Dict, Any, Optional
from alpha.model_intelligence.digital_twin.predictions import PredictedPerformance
from alpha.model_intelligence.capability_graph.graph import ModelCapabilityGraph
from alpha.model_intelligence.connector.registry import ModelRegistry
from alpha.model_intelligence.strategies.profiles import ReasoningProfile


class PredictiveModelSimulator:
    """Simulates and forecasts foundation model execution performance, latency, and failure vectors."""

    def __init__(
        self,
        capability_graph: Optional[ModelCapabilityGraph] = None,
        registry: Optional[ModelRegistry] = None
    ):
        self.capability_graph = capability_graph or ModelCapabilityGraph()
        self.registry = registry or ModelRegistry()
        self._history: List[Dict[str, Any]] = []

    def predict_performance(
        self,
        model_name: str,
        task_domain: str,
        prompt_tokens: int = 250,
        context_tokens: int = 500,
        strategy: Optional[ReasoningProfile] = None
    ) -> PredictedPerformance:
        # Retrieve capability node
        cap_node = self.capability_graph.get_capability(task_domain)
        base_score = cap_node.score if cap_node else 0.70
        sample_size = cap_node.sample_size if cap_node else 0

        # Retrieve model metadata
        meta = self.registry.get_model(model_name)
        ctx_limit = meta.context_window if meta else 8192

        total_tokens = prompt_tokens + context_tokens
        context_utilization = min(1.0, total_tokens / max(1, ctx_limit))

        # Latency estimation: base latency + per-token latency
        # Smaller models: ~15-20ms per token; larger models: ~35-50ms per token
        param_b = meta.parameters_b if meta and meta.parameters_b else 8.0
        ms_per_token = 10.0 + (param_b * 2.5)
        est_latency = 120.0 + (prompt_tokens * ms_per_token * 0.3) + (context_tokens * 1.5)

        # Hallucination risk calculation:
        # Higher when domain capability is low, or context window saturated, or high temperature
        temp = strategy.temperature if strategy else 0.3
        raw_hallucination = (1.0 - base_score) * 0.5 + (context_utilization * 0.25) + (temp * 0.25)

        # Modifiers based on strategy safeguards
        if strategy and strategy.verification_required:
            raw_hallucination *= 0.6  # verification reduces hallucination risk

        hallucination_risk = max(0.01, min(0.95, raw_hallucination))

        # Failure probability
        base_failure = 1.0 - base_score
        if context_utilization > 0.85:
            base_failure += 0.2
        if sample_size < 3:
            base_failure += 0.1  # uncertainty penalty
        failure_prob = max(0.02, min(0.98, base_failure))
        expected_accuracy = max(0.02, min(0.98, 1.0 - failure_prob))

        # Derive risks and recommendations
        risk_factors = []
        recommendations = []

        if hallucination_risk > 0.35:
            risk_factors.append(f"Elevated hallucination risk ({hallucination_risk:.1%}) in domain '{task_domain}'")
            recommendations.append("Apply ground-truth verification and structured evidence injection")

        if context_utilization > 0.75:
            risk_factors.append(f"High context load ({context_utilization:.1%} of {ctx_limit} max)")
            recommendations.append("Apply semantic compression and ranking before prompt inclusion")

        if base_score < 0.70:
            risk_factors.append(f"Model has observed weakness in '{task_domain}' (score={base_score:.2f})")
            recommendations.append("Engage multi-step planning and reflection retries")

        if not recommendations:
            recommendations.append("Standard direct execution recommended")

        pred = PredictedPerformance(
            task_domain=task_domain,
            model_name=model_name,
            expected_accuracy=round(expected_accuracy, 3),
            failure_probability=round(failure_prob, 3),
            expected_latency_ms=round(est_latency, 1),
            hallucination_risk=round(hallucination_risk, 3),
            expected_context_tokens=total_tokens,
            confidence=round(min(0.95, 0.5 + 0.1 * min(5, sample_size)), 2),
            recommended_augmentations=recommendations,
            risk_factors=risk_factors
        )

        self._history.append({
            "model_name": model_name,
            "task_domain": task_domain,
            "prediction": pred.model_dump()
        })
        return pred

    def record_actual_outcome(
        self,
        prediction: PredictedPerformance,
        actual_accuracy: float,
        actual_latency_ms: float,
        had_hallucination: bool
    ):
        """Calibrates digital twin accuracy over time."""
        self._history.append({
            "model_name": prediction.model_name,
            "task_domain": prediction.task_domain,
            "predicted_accuracy": prediction.expected_accuracy,
            "actual_accuracy": actual_accuracy,
            "predicted_latency_ms": prediction.expected_latency_ms,
            "actual_latency_ms": actual_latency_ms,
            "predicted_hallucination_risk": prediction.hallucination_risk,
            "had_hallucination": had_hallucination
        })
