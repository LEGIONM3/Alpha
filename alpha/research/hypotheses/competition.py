"""Hypothesis Competition Engine: Scientific arena where rival hypotheses compete."""

from __future__ import annotations

import math
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Hypothesis, Evidence, EvidencePolarity, ResearchStatus


class HypothesisMatchup(BaseModel):
    primary_hypothesis_id: str
    rival_hypothesis_id: str
    primary_support_score: float = 0.0
    rival_support_score: float = 0.0
    winner_id: Optional[str] = None
    margin: float = 0.0
    settled: bool = False


class HypothesisCompetitionManager:
    """Orchestrates adversarial scientific competition between rival hypotheses."""

    def __init__(self):
        self.matchups: Dict[str, HypothesisMatchup] = {}

    def register_competition(self, hyp_a: Hypothesis, hyp_b: Hypothesis) -> HypothesisMatchup:
        match_id = f"{hyp_a.hypothesis_id}_vs_{hyp_b.hypothesis_id}"
        match = HypothesisMatchup(
            primary_hypothesis_id=hyp_a.hypothesis_id,
            rival_hypothesis_id=hyp_b.hypothesis_id
        )
        self.matchups[match_id] = match
        return match

    def evaluate_evidence_for_match(
        self,
        match_id: str,
        hyp_a: Hypothesis,
        hyp_b: Hypothesis,
        evidence_list: List[Evidence]
    ) -> HypothesisMatchup:
        match = self.matchups.get(match_id)
        if not match:
            match = self.register_competition(hyp_a, hyp_b)

        score_a = 0.0
        score_b = 0.0

        for ev in evidence_list:
            weight = ev.confidence * (1.0 - ev.p_value)
            if ev.hypothesis_id == hyp_a.hypothesis_id:
                if ev.polarity == EvidencePolarity.SUPPORT:
                    score_a += weight
                elif ev.polarity == EvidencePolarity.REFUTE:
                    score_a -= weight
            elif ev.hypothesis_id == hyp_b.hypothesis_id:
                if ev.polarity == EvidencePolarity.SUPPORT:
                    score_b += weight
                elif ev.polarity == EvidencePolarity.REFUTE:
                    score_b -= weight

        match.primary_support_score = round(score_a, 4)
        match.rival_support_score = round(score_b, 4)

        diff = score_a - score_b
        match.margin = round(abs(diff), 4)

        # Require significant evidence margin to declare victory
        if diff >= 0.5:
            match.winner_id = hyp_a.hypothesis_id
            hyp_a.status = ResearchStatus.SUPPORTED
            hyp_b.status = ResearchStatus.REFUTED
            match.settled = True
        elif diff <= -0.5:
            match.winner_id = hyp_b.hypothesis_id
            hyp_b.status = ResearchStatus.SUPPORTED
            hyp_a.status = ResearchStatus.REFUTED
            match.settled = True
        else:
            match.settled = False

        return match
