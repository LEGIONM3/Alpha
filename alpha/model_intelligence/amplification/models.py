"""Cognitive Amplification Models: Data structures for measuring model amplification."""

from enum import Enum
from typing import List, Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field


class AugmentationType(str, Enum):
    MEMORY = "memory"
    RETRIEVAL = "retrieval"
    PLANNING = "planning"
    REFLECTION = "reflection"
    VERIFICATION = "verification"
    SIMULATION = "simulation"
    TOOL = "tool"


class AmplificationConfig(BaseModel):
    enabled_augmentations: List[AugmentationType] = Field(
        default_factory=lambda: [
            AugmentationType.MEMORY,
            AugmentationType.RETRIEVAL,
            AugmentationType.PLANNING,
            AugmentationType.REFLECTION,
            AugmentationType.VERIFICATION,
            AugmentationType.TOOL,
        ]
    )
    max_reflections: int = 2
    run_verification: bool = True
    run_simulation: bool = False


class AmplificationResult(BaseModel):
    task_id: str = Field(default_factory=lambda: f"amp_{uuid.uuid4().hex[:8]}")
    standalone_output: str
    standalone_score: float
    standalone_latency_ms: float
    amplified_output: str
    amplified_score: float
    amplified_latency_ms: float
    active_augmentations: List[str]
    amplification_factor: float
    verification_passed: bool
    reflection_count: int
    details: Dict[str, Any] = Field(default_factory=dict)
