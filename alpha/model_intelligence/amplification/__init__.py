"""Cognitive Amplification Package."""

from alpha.model_intelligence.amplification.models import (
    AugmentationType,
    AmplificationConfig,
    AmplificationResult,
)
from alpha.model_intelligence.amplification.engine import CognitiveAmplificationEngine

__all__ = [
    "AugmentationType",
    "AmplificationConfig",
    "AmplificationResult",
    "CognitiveAmplificationEngine",
]
