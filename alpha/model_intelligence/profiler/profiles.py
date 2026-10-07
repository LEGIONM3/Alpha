"""Model Profiling data models and metrics.

Part 2: Model Profiling Framework
Measures:
- Accuracy
- Consistency
- Reasoning Depth
- Latency
- Context Utilization
- Hallucination Rate
- Instruction Following
- Planning Ability
- Tool Selection Quality
- Memory Usage
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ModelBenchmarkMetrics(BaseModel):
    accuracy: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    reasoning_depth: float = Field(ge=0.0, le=1.0)
    avg_latency_ms: float = 0.0
    context_utilization: float = Field(ge=0.0, le=1.0)
    hallucination_rate: float = Field(ge=0.0, le=1.0)
    instruction_following: float = Field(ge=0.0, le=1.0)
    planning_ability: float = Field(ge=0.0, le=1.0)
    tool_selection_quality: float = Field(ge=0.0, le=1.0)
    memory_usage_efficiency: float = Field(ge=0.0, le=1.0)


class WeaknessProfile(BaseModel):
    model_id: str
    primary_weaknesses: List[str] = Field(default_factory=list)
    vulnerable_contexts: List[str] = Field(default_factory=list)
    failure_probability_thresholds: Dict[str, float] = Field(default_factory=dict)
    mitigation_recommendations: List[str] = Field(default_factory=list)


class FailureProfile(BaseModel):
    model_id: str
    observed_failure_modes: Dict[str, int] = Field(default_factory=dict)
    hallucination_triggers: List[str] = Field(default_factory=list)
    logic_breakdown_points: List[str] = Field(default_factory=list)
    instruction_drift_rate: float = 0.0


class CapabilityProfile(BaseModel):
    model_id: str
    timestamp: float = Field(default_factory=time.time)
    sample_size: int = 0
    metrics: ModelBenchmarkMetrics
    weakness_profile: WeaknessProfile
    failure_profile: FailureProfile
    domain_scores: Dict[str, float] = Field(default_factory=dict)

    def overall_fitness(self) -> float:
        m = self.metrics
        positive = (
            m.accuracy * 0.25 +
            m.consistency * 0.15 +
            m.reasoning_depth * 0.15 +
            m.instruction_following * 0.15 +
            m.planning_ability * 0.10 +
            m.tool_selection_quality * 0.10 +
            m.context_utilization * 0.10
        )
        negative = m.hallucination_rate * 0.30
        return round(max(0.0, min(1.0, positive - negative)), 3)
