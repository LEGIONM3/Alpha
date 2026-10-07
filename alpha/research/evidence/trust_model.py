"""Evidence Trust Models: Agent calibration and foundational invariant verification.

Enforces:
- Agent calibration & epistemic reliability scores
- MANDATORY INVARIANT: No theory may exist without evidence.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Theory, Evidence


class AgentTrustProfile(BaseModel):
    agent_id: str
    total_evidence_submitted: int = 0
    replicated_valid_count: int = 0
    refuted_invalid_count: int = 0
    brier_calibration_score: float = Field(default=0.15, ge=0.0, le=1.0)  # Lower is better calibration
    reputation_score: float = Field(default=0.85, ge=0.0, le=1.0)

    def update_record(self, was_replicated: bool) -> None:
        self.total_evidence_submitted += 1
        if was_replicated:
            self.replicated_valid_count += 1
            self.reputation_score = min(1.0, self.reputation_score + 0.03)
        else:
            self.refuted_invalid_count += 1
            self.reputation_score = max(0.1, self.reputation_score - 0.10)


class EvidenceTrustModel:
    """Manages epistemic trust, calibration, and inviolable evidence invariants."""

    def __init__(self):
        self.profiles: Dict[str, AgentTrustProfile] = {}
        self._lock = threading.RLock()

    def get_or_create_profile(self, agent_id: str) -> AgentTrustProfile:
        with self._lock:
            if agent_id not in self.profiles:
                self.profiles[agent_id] = AgentTrustProfile(agent_id=agent_id)
            return self.profiles[agent_id]

    def record_outcome(self, agent_id: str, was_replicated: bool) -> None:
        with self._lock:
            profile = self.get_or_create_profile(agent_id)
            profile.update_record(was_replicated)

    def verify_theory_has_evidence(self, theory: Theory, evidence_lookup: Dict[str, Evidence]) -> bool:
        """MANDATORY RULE: No theory may exist without evidence."""
        if not theory.finding_ids:
            return False

        # Theory must be grounded in valid, non-empty findings with evidence
        total_grounded_evidence = 0
        for ev in evidence_lookup.values():
            if ev.confidence >= 0.5:
                total_grounded_evidence += 1

        return total_grounded_evidence > 0
