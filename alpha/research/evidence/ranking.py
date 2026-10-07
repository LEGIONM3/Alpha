"""Evidence Ranking Engine: Multi-factorial epistemic evaluation of empirical evidence."""

from __future__ import annotations

from typing import Dict, List, Any
from alpha.research.entities import Evidence, STRENGTH_WEIGHTS


class EvidenceRankingEngine:
    """Computes objective epistemic weight for scientific evidence."""

    @staticmethod
    def calculate_score(evidence: Evidence, replication_count: int = 0) -> float:
        strength_val = STRENGTH_WEIGHTS.get(evidence.strength, 0.5)
        stat_sig = max(0.0, 1.0 - evidence.p_value)
        effect_term = min(1.0, max(0.1, abs(evidence.effect_size)))
        rep_bonus = min(0.20, replication_count * 0.05)

        # Composite score
        raw = (
            0.30 * evidence.confidence +
            0.25 * stat_sig +
            0.20 * effect_term +
            0.15 * strength_val +
            0.10 * rep_bonus
        )
        return round(min(1.0, max(0.0, raw)), 4)

    def rank_evidence(
        self,
        evidence_list: List[Evidence],
        replication_counts: Dict[str, int] = None
    ) -> List[Dict[str, Any]]:
        counts = replication_counts or {}
        scored = []
        for ev in evidence_list:
            reps = counts.get(ev.evidence_id, 0)
            score = self.calculate_score(ev, reps)
            scored.append({
                "evidence_id": ev.evidence_id,
                "evidence": ev,
                "score": score,
                "replications": reps
            })
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored
