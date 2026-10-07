"""Evidence Engine: Evidence Registry, Aggregator, Ranking, and Chains.

Part 4: Evidence Engine
Enforces: Every belief must trace back to evidence. No orphan beliefs allowed.
Supports: Supporting, Contradicting, Unknown, Weak, and Strong evidence.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class EvidencePolarity(str, Enum):
    """Polarity of evidence with respect to a hypothesis or belief."""
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    UNKNOWN = "unknown"


class EvidenceStrength(str, Enum):
    """Calibrated strength rating of empirical evidence."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


STRENGTH_WEIGHTS = {
    EvidenceStrength.WEAK: 0.15,
    EvidenceStrength.MODERATE: 0.35,
    EvidenceStrength.STRONG: 0.70,
}


class Evidence(BaseModel):
    """An empirical or logical evidence unit grounding beliefs in reality."""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_id: Optional[str] = None  # Belief or hypothesis this pertains to
    statement: str
    polarity: EvidencePolarity = EvidencePolarity.SUPPORTING
    strength: EvidenceStrength = EvidenceStrength.MODERATE
    source_type: str = "observation"  # e.g., tool_execution, code_test, benchmark, document
    source_id: str = "sensor"
    verifier_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def numeric_impact(self) -> float:
        """Calculate signed numeric impact on belief confidence."""
        base = STRENGTH_WEIGHTS[self.strength]
        if self.polarity == EvidencePolarity.SUPPORTING:
            return base
        elif self.polarity == EvidencePolarity.CONTRADICTING:
            return -base * 1.5  # Contradictions penalize more severely
        return 0.0


class EvidenceChain(BaseModel):
    """Ordered dependency chain of evidence items supporting a belief."""
    chain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_belief_id: str
    step_evidence_ids: List[str] = Field(default_factory=list)
    coherence_score: float = 1.0


class EvidenceRegistry:
    """Central store and indexing of all grounding evidence."""

    def __init__(self):
        self._evidence: Dict[str, Evidence] = {}
        self._by_claim: Dict[str, List[str]] = {}
        self._chains: Dict[str, EvidenceChain] = {}

    def register(self, evidence: Evidence) -> Evidence:
        """Store an evidence unit."""
        self._evidence[evidence.evidence_id] = evidence
        if evidence.claim_id:
            if evidence.claim_id not in self._by_claim:
                self._by_claim[evidence.claim_id] = []
            self._by_claim[evidence.claim_id].append(evidence.evidence_id)
        return evidence

    def get(self, evidence_id: str) -> Optional[Evidence]:
        return self._evidence.get(evidence_id)

    def get_for_claim(self, claim_id: str) -> List[Evidence]:
        """Return all evidence registered for a belief or claim."""
        eids = self._by_claim.get(claim_id, [])
        return [self._evidence[eid] for eid in eids if eid in self._evidence]

    def register_chain(self, target_belief_id: str, evidence_ids: List[str]) -> EvidenceChain:
        """Form a verifiable evidence chain for a belief."""
        chain = EvidenceChain(
            target_belief_id=target_belief_id,
            step_evidence_ids=evidence_ids
        )
        self._chains[chain.chain_id] = chain
        return chain

    def get_chain(self, chain_id: str) -> Optional[EvidenceChain]:
        return self._chains.get(chain_id)


class EvidenceRankingSystem:
    """Ranks evidence based on strength, freshness, and source reliability."""

    def rank(self, items: List[Evidence]) -> List[Evidence]:
        now = time.time()
        def score(e: Evidence) -> float:
            strength_val = STRENGTH_WEIGHTS[e.strength]
            # Freshness decay over 30 days
            age_days = (now - e.created_at) / 86400.0
            freshness = max(0.2, 1.0 - (age_days * 0.03))
            authority = 1.0 if e.source_type in ("code_test", "benchmark", "formal_proof") else 0.8
            return strength_val * freshness * authority

        return sorted(items, key=score, reverse=True)


class EvidenceAggregator:
    """Aggregates multiple evidence pieces into net confidence and contradiction metrics."""

    def __init__(self, ranker: Optional[EvidenceRankingSystem] = None):
        self.ranker = ranker or EvidenceRankingSystem()

    def aggregate(self, evidence_list: List[Evidence]) -> Dict[str, Any]:
        if not evidence_list:
            return {
                "net_score": 0.0,
                "support_count": 0,
                "contradict_count": 0,
                "unknown_count": 0,
                "has_strong_contradiction": False,
                "recommended_confidence": 0.5
            }

        support = [e for e in evidence_list if e.polarity == EvidencePolarity.SUPPORTING]
        contradict = [e for e in evidence_list if e.polarity == EvidencePolarity.CONTRADICTING]
        unknown = [e for e in evidence_list if e.polarity == EvidencePolarity.UNKNOWN]

        total_support_impact = sum(e.numeric_impact() for e in support)
        total_contradict_impact = sum(abs(e.numeric_impact()) for e in contradict)

        has_strong_contradict = any(
            e.polarity == EvidencePolarity.CONTRADICTING and e.strength == EvidenceStrength.STRONG
            for e in contradict
        )

        # Baseline confidence starts at 0.5, adjusted asymptotically by evidence
        diff = total_support_impact - total_contradict_impact
        # Sigmoid-like scaling
        import math
        calibrated = 1.0 / (1.0 + math.exp(-diff * 2.0))
        if has_strong_contradict:
            calibrated = min(calibrated, 0.25)

        return {
            "net_score": round(diff, 3),
            "support_count": len(support),
            "contradict_count": len(contradict),
            "unknown_count": len(unknown),
            "has_strong_contradiction": has_strong_contradict,
            "recommended_confidence": round(calibrated, 3)
        }
