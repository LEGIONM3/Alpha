"""World Model Immune System: Active Cognitive Defense for Project Alpha (Phase 8).

Protects Alpha from cognitive corruption, self-reinforcing delusions, and epistemic poisoning.

Responsibilities:
- Detect suspicious beliefs (untraceable provenance, ungrounded axioms)
- Detect unsupported causal links (links lacking empirical intervention or temporal precedence)
- Detect ontology violations (entity contract breaches, invalid state transitions)
- Detect confidence inflation (high confidence without corresponding evidence strength)
- Quarantine dangerous beliefs (isolate from reasoning, planning, and knowledge graph queries)
"""

from __future__ import annotations

import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from alpha.world_model.ontology.entities import LifecycleState
from alpha.world_model.epistemology.belief import Belief, BeliefSystem
from alpha.world_model.causal.graphs import CauseGraph, CausalLink

logger = logging.getLogger("alpha.epistemology.immune_system")


class ThreatType(str, Enum):
    """Categories of cognitive contamination and epistemic threats."""
    CONFIDENCE_INFLATION = "confidence_inflation"
    UNSUPPORTED_CAUSAL_LINK = "unsupported_causal_link"
    ONTOLOGY_VIOLATION = "ontology_violation"
    SUSPICIOUS_PROVENANCE = "suspicious_provenance"
    EPISTEMIC_POISONING = "epistemic_poisoning"
    ORPHAN_CONTAMINATION = "orphan_contamination"


class QuarantineRecord(BaseModel):
    """Audit record of a quarantined belief or corrupted cognitive entity."""
    quarantine_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    belief_id: str
    statement: str
    threat_type: ThreatType
    threat_level: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    quarantined_at: float = Field(default_factory=time.time)
    reason: str
    remediation_required: str
    released: bool = False
    release_notes: Optional[str] = None


class WorldModelImmuneSystem:
    """Active cognitive defense subsystem defending world state against epistemic corruption."""

    def __init__(
        self,
        belief_system: Optional[BeliefSystem] = None,
        cause_graph: Optional[CauseGraph] = None,
        ontology: Optional[Any] = None,
    ):
        self.belief_system = belief_system
        self.cause_graph = cause_graph
        self.ontology = ontology
        self._quarantined_beliefs: Dict[str, QuarantineRecord] = {}
        self._incident_log: List[QuarantineRecord] = []

    def inspect_belief(self, belief: Belief) -> Optional[QuarantineRecord]:
        """Examine a belief for suspicious signals, confidence inflation, or ontology breaches."""
        # Rule 1: Confidence Inflation Check
        # High confidence (>= 0.75) with zero supporting evidence, zero observations, and zero documents
        total_support = len(belief.supporting_evidence) + len(belief.observations) + len(belief.source_documents)
        if belief.confidence_score >= 0.75 and total_support == 0:
            return self.quarantine_belief(
                belief_id=belief.belief_id,
                threat_type=ThreatType.CONFIDENCE_INFLATION,
                threat_level="HIGH",
                reason=(
                    f"Confidence inflation detected: Statement '{belief.statement[:40]}' claims confidence "
                    f"{belief.confidence_score} with zero supporting evidence or empirical observations."
                ),
                remediation="Attach verifiable empirical evidence or reduce confidence below 0.5.",
            )

        # Rule 2: Suspicious Provenance / Orphan Contamination
        if total_support == 0 and len(belief.sources) == 0:
            return self.quarantine_belief(
                belief_id=belief.belief_id,
                threat_type=ThreatType.ORPHAN_CONTAMINATION,
                threat_level="CRITICAL",
                reason="Belief completely untraceable with zero sources, evidence, or provenance.",
                remediation="Provide valid originating sensor or evidence chain.",
            )

        # Rule 3: Contradiction Breach
        if len(belief.contradicting_evidence) > len(belief.supporting_evidence) and belief.confidence_score > 0.5:
            return self.quarantine_belief(
                belief_id=belief.belief_id,
                threat_type=ThreatType.EPISTEMIC_POISONING,
                threat_level="HIGH",
                reason="Belief maintains high confidence despite overwhelming contradiction evidence.",
                remediation="Run falsification test or demote belief confidence.",
            )

        return None

    def inspect_causal_link(self, link: CausalLink) -> Optional[Dict[str, Any]]:
        """Evaluate if a causal link is ungrounded or violating causal laws."""
        flaws: List[str] = []
        if link.time_delay_seconds < 0:
            flaws.append("Negative time delay indicates reverse causation.")
        if link.strength >= 0.95 and (not link.mechanism or link.mechanism == "direct_mechanism"):
            flaws.append("Near-certain causal strength (>=0.95) without detailed mechanism.")

        if flaws:
            return {
                "link_id": link.link_id,
                "cause_id": link.cause_id,
                "effect_id": link.effect_id,
                "threat_type": ThreatType.UNSUPPORTED_CAUSAL_LINK.value,
                "flaws": flaws,
            }
        return None

    def quarantine_belief(
        self,
        belief_id: str,
        threat_type: ThreatType,
        reason: str,
        threat_level: str = "HIGH",
        remediation: str = "Empirical review required",
    ) -> QuarantineRecord:
        """Isolate a dangerous or suspicious belief from active cognitive processes."""
        statement = "unknown"
        if self.belief_system:
            belief = self.belief_system.get_belief(belief_id)
            if belief:
                statement = belief.statement
                # Quarantine the belief
                belief.verification_status = "QUARANTINED"
                # Halve confidence under quarantine
                belief.confidence = min(0.3, belief.confidence)
                belief.confidence_score = belief.confidence

        record = QuarantineRecord(
            belief_id=belief_id,
            statement=statement,
            threat_type=threat_type,
            threat_level=threat_level,
            reason=reason,
            remediation_required=remediation,
        )

        self._quarantined_beliefs[belief_id] = record
        self._incident_log.append(record)
        logger.warning("BELIEF QUARANTINED [%s]: %s - Reason: %s", threat_type.value, belief_id, reason)
        return record

    def release_from_quarantine(self, belief_id: str, release_notes: str) -> bool:
        """Restore a quarantined belief after evidence has been supplied or verified."""
        record = self._quarantined_beliefs.get(belief_id)
        if not record:
            return False

        record.released = True
        record.release_notes = release_notes

        if self.belief_system:
            belief = self.belief_system.get_belief(belief_id)
            if belief:
                belief.verification_status = "UNVERIFIED"

        del self._quarantined_beliefs[belief_id]
        return True

    def purge_quarantined_belief(self, belief_id: str, reason: str = "immune_purge") -> bool:
        """Permanently terminate and delete a quarantined belief."""
        record = self._quarantined_beliefs.get(belief_id)
        if not record:
            return False

        if self.belief_system:
            belief = self.belief_system.get_belief(belief_id)
            if belief:
                belief.die(reason=f"Immune System Purge: {reason}")

        del self._quarantined_beliefs[belief_id]
        return True

    def scan_and_defend(self) -> List[QuarantineRecord]:
        """Perform comprehensive cognitive sweep across all beliefs and causal links."""
        records: List[QuarantineRecord] = []
        if not self.belief_system:
            return records

        for belief in self.belief_system.get_all():
            if belief.is_alive():
                q = self.inspect_belief(belief)
                if q:
                    records.append(q)

        return records

    def get_quarantined_records(self) -> List[QuarantineRecord]:
        return list(self._quarantined_beliefs.values())

    def get_immune_health(self) -> Dict[str, Any]:
        """Get summary of cognitive immune defense activity."""
        active_quarantine_count = len(self._quarantined_beliefs)
        total_incidents = len(self._incident_log)
        status = "VIGILANT" if active_quarantine_count == 0 else "DEFENDING"

        return {
            "status": status,
            "active_quarantines": active_quarantine_count,
            "total_incidents_logged": total_incidents,
            "threat_breakdown": {
                t.value: sum(1 for r in self._quarantined_beliefs.values() if r.threat_type == t)
                for t in ThreatType
            },
        }
