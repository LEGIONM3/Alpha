"""Digital Twin Predictions: Performance forecast schema."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PredictedPerformance(BaseModel):
    task_domain: str
    model_name: str
    expected_accuracy: float = Field(..., ge=0.0, le=1.0)
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    expected_latency_ms: float = Field(..., ge=0.0)
    hallucination_risk: float = Field(..., ge=0.0, le=1.0)
    expected_context_tokens: int = Field(..., ge=0)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    recommended_augmentations: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
