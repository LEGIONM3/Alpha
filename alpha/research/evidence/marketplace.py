"""Evidence Marketplace: Decentralized epistemic exchange where empirical evidence is registered, traded, and staked."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Evidence, EvidencePolarity


class EvidenceStake(BaseModel):
    stake_id: str
    evidence_id: str
    agent_id: str
    amount_credits: float
    staked_at: float = Field(default_factory=time.time)
    settled: bool = False
    payout: float = 0.0


class EvidenceListing(BaseModel):
    evidence: Evidence
    seller_id: str
    asking_price: float = 10.0
    total_staked: float = 0.0
    stakes: List[EvidenceStake] = Field(default_factory=list)
    reputation_weight: float = 1.0


class EvidenceMarketplace:
    """Decentralized epistemic exchange for pricing and verifying empirical evidence."""

    def __init__(self):
        self.listings: Dict[str, EvidenceListing] = {}
        self.agent_balances: Dict[str, float] = {}
        self._lock = threading.RLock()

    def set_balance(self, agent_id: str, balance: float) -> None:
        with self._lock:
            self.agent_balances[agent_id] = balance

    def list_evidence(self, evidence: Evidence, seller_id: str, asking_price: float = 10.0) -> EvidenceListing:
        with self._lock:
            listing = EvidenceListing(
                evidence=evidence,
                seller_id=seller_id,
                asking_price=asking_price,
                reputation_weight=evidence.confidence
            )
            self.listings[evidence.evidence_id] = listing
            return listing

    def stake_on_evidence(self, evidence_id: str, agent_id: str, amount: float) -> Optional[EvidenceStake]:
        with self._lock:
            listing = self.listings.get(evidence_id)
            if not listing:
                return None
            balance = self.agent_balances.get(agent_id, 100.0)
            if balance < amount:
                return None

            self.agent_balances[agent_id] = balance - amount
            stake = EvidenceStake(
                stake_id=f"stk_{len(listing.stakes)+1}_{evidence_id[:6]}",
                evidence_id=evidence_id,
                agent_id=agent_id,
                amount_credits=amount
            )
            listing.stakes.append(stake)
            listing.total_staked += amount
            return stake

    def settle_market(self, evidence_id: str, replicated_valid: bool) -> Dict[str, Any]:
        """Settle stakes based on replication outcome: reward valid evidence, slash invalid."""
        with self._lock:
            listing = self.listings.get(evidence_id)
            if not listing:
                return {"error": "Listing not found"}

            payouts = {}
            for stake in listing.stakes:
                if not stake.settled:
                    if replicated_valid:
                        # 1.5x return on successful replication
                        reward = stake.amount_credits * 1.5
                        stake.payout = reward
                        self.agent_balances[stake.agent_id] = self.agent_balances.get(stake.agent_id, 0.0) + reward
                        payouts[stake.agent_id] = reward
                    else:
                        # Slashed on refutation
                        stake.payout = 0.0
                        payouts[stake.agent_id] = 0.0
                    stake.settled = True

            return {
                "evidence_id": evidence_id,
                "replicated_valid": replicated_valid,
                "payouts": payouts,
                "total_staked": listing.total_staked
            }
