"""Deliberation and Competitive Reasoning package."""

from alpha.agents.deliberation.council import CouncilDeliberationSystem, CouncilVerdict
from alpha.agents.deliberation.adversarial import (
    CompetitiveReasoningEngine,
    CompetitiveReasoningResult,
    AdversarialRound,
)

__all__ = [
    "CouncilDeliberationSystem",
    "CouncilVerdict",
    "CompetitiveReasoningEngine",
    "CompetitiveReasoningResult",
    "AdversarialRound",
]
