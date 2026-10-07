"""Evidence Conflict Resolution: Resolves contradictory empirical findings."""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Evidence, EvidencePolarity, STRENGTH_WEIGHTS
from alpha.research.evidence.ranking import EvidenceRankingEngine


class ConflictResolutionVerdict(BaseModel):
    hypothesis_id: str
    resolved: bool
    dominant_polarity: EvidencePolarity
    net_confidence: float
    support_mass: float
    refute_mass: float
    margin: float
    recommendation: str  # ADOPT, REJECT, RUN_TIEBREAKER_EXPERIMENT


class EvidenceConflictResolver:
    """Adjudicates contradictory empirical observations via Bayesian meta-analysis."""

    def __init__(self, significance_margin: float = 0.15):
        self.significance_margin = significance_margin

    def resolve_conflicts(self, hypothesis_id: str, evidence_list: List[Evidence]) -> ConflictResolutionVerdict:
        support_mass = 0.0
        refute_mass = 0.0

        for ev in evidence_list:
            weight = EvidenceRankingEngine.calculate_score(ev)
            if ev.polarity == EvidencePolarity.SUPPORT:
                support_mass += weight
            elif ev.polarity == EvidencePolarity.REFUTE:
                refute_mass += weight

        total_mass = support_mass + refute_mass
        if total_mass == 0.0:
            return ConflictResolutionVerdict(
                hypothesis_id=hypothesis_id,
                resolved=False,
                dominant_polarity=EvidencePolarity.INCONCLUSIVE,
                net_confidence=0.0,
                support_mass=0.0,
                refute_mass=0.0,
                margin=0.0,
                recommendation="RUN_TIEBREAKER_EXPERIMENT"
            )

        margin = abs(support_mass - refute_mass) / total_mass
        net_conf = round(abs(support_mass - refute_mass) / max(1.0, total_mass), 3)

        if margin < self.significance_margin:
            # Contradictory evidence is in genuine tension
            return ConflictResolutionVerdict(
                hypothesis_id=hypothesis_id,
                resolved=False,
                dominant_polarity=EvidencePolarity.INCONCLUSIVE,
                net_confidence=net_conf,
                support_mass=round(support_mass, 3),
                refute_mass=round(refute_mass, 3),
                margin=round(margin, 3),
                recommendation="RUN_TIEBREAKER_EXPERIMENT"
            )

        dominant = EvidencePolarity.SUPPORT if support_mass > refute_mass else EvidencePolarity.REFUTE
        rec = "ADOPT" if dominant == EvidencePolarity.SUPPORT else "REJECT"

        return ConflictResolutionVerdict(
            hypothesis_id=hypothesis_id,
            resolved=True,
            dominant_polarity=dominant,
            net_confidence=net_conf,
            support_mass=round(support_mass, 3),
            refute_mass=round(refute_mass, 3),
            margin=round(margin, 3),
            recommendation=rec
        )
