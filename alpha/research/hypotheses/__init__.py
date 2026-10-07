"""Hypotheses Package Exports."""

from alpha.research.hypotheses.generator import (
    HypothesisGenerator,
    PatternDetector,
    AnalogyEngine,
    ConceptBlender,
    AnomalyDetector,
)
from alpha.research.hypotheses.competition import (
    HypothesisCompetitionManager,
    HypothesisMatchup,
)

__all__ = [
    "HypothesisGenerator",
    "PatternDetector",
    "AnalogyEngine",
    "ConceptBlender",
    "AnomalyDetector",
    "HypothesisCompetitionManager",
    "HypothesisMatchup",
]
