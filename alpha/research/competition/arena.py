"""Scientific Arena: Multi-agent adversarial and competitive scientific discovery."""

from __future__ import annotations

import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Theory, Hypothesis, Experiment, Evidence, ResearchStatus
from alpha.research.evidence.ranking import EvidenceRankingEngine


class CompetitionTournamentResult(BaseModel):
    category: str  # THEORIES, HYPOTHESES, EXPERIMENTS
    winner_id: str
    winner_name: str
    runner_ups: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    rationale: str


class ScientificArena:
    """Orchestrates competition where best evidence wins."""

    def __init__(self):
        self._lock = threading.RLock()

    def compete_hypotheses(
        self,
        hypotheses: List[Hypothesis],
        evidence_by_hyp: Dict[str, List[Evidence]]
    ) -> CompetitionTournamentResult:
        """Tournament selection among rival hypotheses. Best evidence wins."""
        with self._lock:
            scores: Dict[str, float] = {}
            for hyp in hypotheses:
                ev_list = evidence_by_hyp.get(hyp.hypothesis_id, [])
                score = sum(EvidenceRankingEngine.calculate_score(ev) for ev in ev_list)
                scores[hyp.hypothesis_id] = round(score + hyp.confidence * 0.2, 4)

            sorted_hyps = sorted(hypotheses, key=lambda h: scores[h.hypothesis_id], reverse=True)
            winner = sorted_hyps[0]
            winner.status = ResearchStatus.SUPPORTED

            for rival in sorted_hyps[1:]:
                rival.status = ResearchStatus.REFUTED

            return CompetitionTournamentResult(
                category="HYPOTHESES",
                winner_id=winner.hypothesis_id,
                winner_name=winner.statement[:50],
                runner_ups=[h.hypothesis_id for h in sorted_hyps[1:]],
                scores=scores,
                rationale=f"Winner {winner.hypothesis_id} accumulated highest evidence weight ({scores[winner.hypothesis_id]})."
            )

    def compete_theories(
        self,
        theories: List[Theory],
        evidence_counts: Dict[str, int]
    ) -> CompetitionTournamentResult:
        """Tournament selection among rival overarching theories."""
        with self._lock:
            scores: Dict[str, float] = {}
            for thy in theories:
                # Score combines explanatory power, parsimony, and evidence mass
                ev_mass = min(1.0, evidence_counts.get(thy.theory_id, 1) * 0.1)
                comp_score = round(
                    0.40 * thy.explanatory_power +
                    0.35 * thy.parsimony_score +
                    0.25 * ev_mass,
                    4
                )
                scores[thy.theory_id] = comp_score

            sorted_theories = sorted(theories, key=lambda t: scores[t.theory_id], reverse=True)
            winner = sorted_theories[0]
            winner.status = ResearchStatus.SUPPORTED

            return CompetitionTournamentResult(
                category="THEORIES",
                winner_id=winner.theory_id,
                winner_name=winner.name,
                runner_ups=[t.theory_id for t in sorted_theories[1:]],
                scores=scores,
                rationale=f"Dominant theory '{winner.name}' won with composite score {scores[winner.theory_id]}."
            )
