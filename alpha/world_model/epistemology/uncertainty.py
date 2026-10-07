"""Uncertainty Engine: Epistemic quantification, confidence calibration, and interval estimation.

Part 12: Uncertainty Engine
Represents: Unknown, Partially Known, Likely, Unlikely, Certain, Impossible.
Enforces: Every answer must include confidence; every prediction must include uncertainty.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Tuple, Dict, Any
from pydantic import BaseModel, Field


class UncertaintyLevel(str, Enum):
    """Categorical classification of epistemic certainty."""
    IMPOSSIBLE = "impossible"        # confidence == 0.0 or refuted
    UNKNOWN = "unknown"              # confidence in [0.0, 0.15)
    UNLIKELY = "unlikely"            # confidence in [0.15, 0.40)
    PARTIALLY_KNOWN = "partially_known" # confidence in [0.40, 0.65)
    LIKELY = "likely"                # confidence in [0.65, 0.85)
    CERTAIN = "certain"              # confidence in [0.85, 1.0]


class CalibratedEstimate(BaseModel):
    """A quantity or statement paired with explicit confidence and uncertainty bounds."""
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty_level: UncertaintyLevel
    uncertainty_range: Tuple[float, float] = (0.0, 1.0)
    epistemic_variance: float = 0.0
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "confidence": self.confidence,
            "uncertainty_level": self.uncertainty_level.value,
            "uncertainty_range": self.uncertainty_range,
            "epistemic_variance": round(self.epistemic_variance, 4),
            "rationale": self.rationale,
        }


class UncertaintyEngine:
    """Calculates uncertainty bounds, categorizes confidence, and propagates variance."""

    @staticmethod
    def classify_confidence(confidence: float) -> UncertaintyLevel:
        """Map a numeric confidence [0.0, 1.0] to an UncertaintyLevel."""
        c = max(0.0, min(1.0, confidence))
        if c == 0.0:
            return UncertaintyLevel.IMPOSSIBLE
        elif c < 0.15:
            return UncertaintyLevel.UNKNOWN
        elif c < 0.40:
            return UncertaintyLevel.UNLIKELY
        elif c < 0.65:
            return UncertaintyLevel.PARTIALLY_KNOWN
        elif c < 0.85:
            return UncertaintyLevel.LIKELY
        else:
            return UncertaintyLevel.CERTAIN

    @staticmethod
    def compute_bounds(base_estimate: float, confidence: float) -> Tuple[float, float]:
        """Compute 95% epistemic confidence intervals around a base value."""
        # Lower confidence translates into broader uncertainty bounds
        c = max(0.01, min(0.99, confidence))
        margin = (1.0 - c) * max(1.0, abs(base_estimate))
        return (round(base_estimate - margin, 4), round(base_estimate + margin, 4))

    def evaluate_claim(self, statement: str, confidence: float, rationale: str = "") -> CalibratedEstimate:
        """Create a calibrated estimate for any cognitive statement."""
        level = self.classify_confidence(confidence)
        variance = (1.0 - confidence) ** 2
        return CalibratedEstimate(
            value=statement,
            confidence=round(confidence, 3),
            uncertainty_level=level,
            uncertainty_range=self.compute_bounds(confidence, confidence),
            epistemic_variance=round(variance, 4),
            rationale=rationale
        )

    def combine_independent_uncertainties(self, conf1: float, conf2: float) -> float:
        """Combine two independent probabilistic sources via soft conjunction."""
        return round(conf1 * conf2, 3)

    def combine_disjunctive_uncertainties(self, conf1: float, conf2: float) -> float:
        """Combine two alternative supporting sources via inclusion-exclusion."""
        return round(conf1 + conf2 - (conf1 * conf2), 3)
