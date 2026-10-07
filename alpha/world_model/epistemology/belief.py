"""Belief System: Epistemological foundation of Project Alpha.

Part 3: Belief System
Alpha stops storing facts; it stores confidence-weighted beliefs grounded in evidence.
Beliefs strengthen, weaken, decay over time, and die when refuted or abandoned.
"""

from __future__ import annotations

import math
import time
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator

from alpha.world_model.ontology.entities import LifecycleState
from alpha.world_model.epistemology.evidence import Evidence, EvidenceRegistry, EvidencePolarity, EvidenceStrength
from alpha.world_model.epistemology.uncertainty import UncertaintyEngine, UncertaintyLevel


class VerificationRecord(BaseModel):
    """Historical audit entry for a validation attempt on a belief."""
    timestamp: float = Field(default_factory=time.time)
    verifier_id: str = "system"
    method: str = "empirical_check"
    passed: bool = True
    new_confidence: float
    notes: Optional[str] = None


class Belief(BaseModel):
    """A confidence-weighted proposition grounded in verifiable evidence."""
    belief_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)          # Evidence IDs
    supporting_evidence: List[str] = Field(default_factory=list) # Phase 8 traceable evidence IDs
    source_evidence: List[str] = Field(default_factory=list)     # Grounded empirical evidence citations/IDs
    sources: List[str] = Field(default_factory=list)           # Originating agent or sensor IDs
    source_documents: List[str] = Field(default_factory=list)  # Phase 8 source file/doc URIs
    observations: List[Dict[str, Any]] = Field(default_factory=list) # Phase 8 empirical observations
    supporting_observations: List[Dict[str, Any]] = Field(default_factory=list) # Live observations supporting belief
    contradictions: List[str] = Field(default_factory=list)    # Refuting evidence or belief IDs
    contradicting_evidence: List[str] = Field(default_factory=list) # Phase 8 refuting evidence IDs
    contradiction_history: List[str] = Field(default_factory=list) # Historical record of empirical contradictions
    verification_status: str = Field(default="UNVERIFIED")     # UNVERIFIED, VERIFIED, CONTRADICTED, QUARANTINED, FALSIFIED
    last_verified_timestamp: float = Field(default_factory=time.time)
    timestamp: float = Field(default_factory=time.time)        # Observation/revision timestamp
    verification_history: List[VerificationRecord] = Field(default_factory=list)
    decay_rate: float = Field(default=0.005, ge=0.0)           # Per-second or per-tick decay rate
    last_validation: float = Field(default_factory=time.time)
    lifecycle_state: LifecycleState = LifecycleState.ACTIVE
    domain: str = "general"
    provenance_chain: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def sync_pre_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync confidence <-> confidence_score
            if "confidence_score" in data and "confidence" not in data:
                data["confidence"] = data["confidence_score"]
            elif "confidence" in data and "confidence_score" not in data:
                data["confidence_score"] = data["confidence"]
            elif "confidence" in data and "confidence_score" in data:
                data["confidence_score"] = data["confidence"]

            # Sync evidence <-> supporting_evidence <-> source_evidence
            ev = data.get("source_evidence") or data.get("supporting_evidence") or data.get("evidence") or []
            data["evidence"] = list(ev)
            data["supporting_evidence"] = list(ev)
            data["source_evidence"] = list(ev)

            # Sync observations <-> supporting_observations
            obs = data.get("supporting_observations") or data.get("observations") or []
            data["observations"] = list(obs)
            data["supporting_observations"] = list(obs)

            # Sync contradictions <-> contradicting_evidence <-> contradiction_history
            contra = data.get("contradiction_history") or data.get("contradicting_evidence") or data.get("contradictions") or []
            data["contradictions"] = list(contra)
            data["contradicting_evidence"] = list(contra)
            data["contradiction_history"] = list(contra)

            # Sync timestamps
            ts = data.get("timestamp") or data.get("last_verified_timestamp") or data.get("last_validation") or time.time()
            data["timestamp"] = ts
            data["last_verified_timestamp"] = ts
            data["last_validation"] = ts
        return data

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name == "confidence":
            super().__setattr__("confidence_score", value)
        elif name == "confidence_score":
            super().__setattr__("confidence", value)
        elif name in ("evidence", "supporting_evidence", "source_evidence"):
            super().__setattr__("evidence", value)
            super().__setattr__("supporting_evidence", value)
            super().__setattr__("source_evidence", value)
        elif name in ("observations", "supporting_observations"):
            super().__setattr__("observations", value)
            super().__setattr__("supporting_observations", value)
        elif name in ("contradictions", "contradicting_evidence", "contradiction_history"):
            super().__setattr__("contradictions", value)
            super().__setattr__("contradicting_evidence", value)
            super().__setattr__("contradiction_history", value)
        elif name in ("last_validation", "last_verified_timestamp", "timestamp"):
            super().__setattr__("last_validation", value)
            super().__setattr__("last_verified_timestamp", value)
            super().__setattr__("timestamp", value)

    def is_alive(self) -> bool:
        return self.lifecycle_state == LifecycleState.ACTIVE and self.confidence > 0.05 and self.verification_status != "QUARANTINED"

    def strengthen(self, evidence_id: str, delta: float = 0.15, verifier_id: str = "system") -> float:
        """Increase confidence asymptotically towards 1.0 upon supporting verification."""
        if evidence_id not in self.evidence:
            self.evidence.append(evidence_id)
        if evidence_id not in self.supporting_evidence:
            self.supporting_evidence.append(evidence_id)
        # Asymptotic approach: delta scales with remaining headroom
        gain = delta * (1.0 - self.confidence)
        new_conf = round(min(1.0, self.confidence + gain), 4)
        self.confidence = new_conf
        self.confidence_score = new_conf
        self.last_validation = time.time()
        self.last_verified_timestamp = self.last_validation
        if self.verification_status == "UNVERIFIED" and new_conf >= 0.7:
            self.verification_status = "VERIFIED"
        self.verification_history.append(
            VerificationRecord(
                verifier_id=verifier_id,
                passed=True,
                new_confidence=self.confidence,
                notes=f"Strengthened via evidence {evidence_id}"
            )
        )
        return self.confidence

    def weaken(self, contradiction_id: str, penalty: float = 0.25, verifier_id: str = "system") -> float:
        """Decrease confidence upon contradicting evidence or failed verification."""
        if contradiction_id not in self.contradictions:
            self.contradictions.append(contradiction_id)
        if contradiction_id not in self.contradicting_evidence:
            self.contradicting_evidence.append(contradiction_id)
        new_conf = round(max(0.0, self.confidence - penalty), 4)
        self.confidence = new_conf
        self.confidence_score = new_conf
        self.last_validation = time.time()
        self.last_verified_timestamp = self.last_validation
        if len(self.contradicting_evidence) > 0:
            self.verification_status = "CONTRADICTED"
        self.verification_history.append(
            VerificationRecord(
                verifier_id=verifier_id,
                passed=False,
                new_confidence=self.confidence,
                notes=f"Weakened via contradiction {contradiction_id}"
            )
        )
        if self.confidence <= 0.05:
            self.die(reason=f"Confidence dropped to {self.confidence} due to contradictions.")
        return self.confidence

    def apply_decay(self, elapsed_seconds: float) -> float:
        """Gradually decay unverified belief confidence toward uncertainty (0.5 or lower)."""
        if self.lifecycle_state != LifecycleState.ACTIVE:
            return self.confidence
        # Exponential decay factor
        factor = math.exp(-self.decay_rate * (elapsed_seconds / 60.0))
        # Decay pulls confidence towards 0.0
        new_conf = round(max(0.0, self.confidence * factor), 4)
        self.confidence = new_conf
        self.confidence_score = new_conf
        if self.confidence <= 0.05:
            self.die(reason="Confidence decayed below survival threshold.")
        return self.confidence

    def die(self, reason: str = "refuted") -> None:
        """Terminate an untenable belief."""
        self.lifecycle_state = LifecycleState.DEAD
        self.confidence = 0.0
        self.confidence_score = 0.0
        self.verification_status = "FALSIFIED"
        self.verification_history.append(
            VerificationRecord(
                verifier_id="system",
                passed=False,
                new_confidence=0.0,
                notes=f"Belief died: {reason}"
            )
        )


class BeliefSystem:
    """Manages the lifecycle, evaluation, and epistemic consistency of all beliefs."""

    def __init__(self, evidence_registry: EvidenceRegistry, uncertainty_engine: UncertaintyEngine):
        self.evidence_registry = evidence_registry
        self.uncertainty_engine = uncertainty_engine
        self._beliefs: Dict[str, Belief] = {}

    def form_belief(
        self,
        statement: str,
        initial_confidence: float = 0.5,
        evidence_ids: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        source_documents: Optional[List[str]] = None,
        observations: Optional[List[Dict[str, Any]]] = None,
        supporting_evidence: Optional[List[str]] = None,
        contradicting_evidence: Optional[List[str]] = None,
        domain: str = "general",
        decay_rate: float = 0.005,
        verification_status: str = "UNVERIFIED"
    ) -> Belief:
        """Create and ground a new belief. Strict: No orphan beliefs without evidence or source."""
        ev_list = list(supporting_evidence or evidence_ids or [])
        src_list = list(sources or [])
        doc_list = list(source_documents or [])
        obs_list = list(observations or [])
        contra_list = list(contradicting_evidence or [])

        if not ev_list and not src_list and not doc_list and not obs_list:
            raise ValueError("Epistemological constraint violated: No orphan beliefs allowed. Must provide evidence or source.")

        now = time.time()
        belief = Belief(
            statement=statement,
            confidence=max(0.0, min(1.0, initial_confidence)),
            confidence_score=max(0.0, min(1.0, initial_confidence)),
            evidence=ev_list,
            supporting_evidence=ev_list,
            sources=src_list,
            source_documents=doc_list,
            observations=obs_list,
            contradictions=contra_list,
            contradicting_evidence=contra_list,
            verification_status=verification_status,
            last_verified_timestamp=now,
            last_validation=now,
            domain=domain,
            decay_rate=decay_rate,
        )
        self._beliefs[belief.belief_id] = belief
        return belief

    def get_belief(self, belief_id: str) -> Optional[Belief]:
        return self._beliefs.get(belief_id)

    def get_all(self) -> List[Belief]:
        """Return all beliefs stored in the belief system."""
        return list(self._beliefs.values())

    def get_active_beliefs(self, min_confidence: float = 0.2) -> List[Belief]:
        return [b for b in self._beliefs.values() if b.is_alive() and b.confidence >= min_confidence]

    def update_with_evidence(self, belief_id: str, evidence: Evidence) -> Belief:
        """Ingest new empirical evidence, adjusting belief confidence accordingly."""
        belief = self.get_belief(belief_id)
        if not belief:
            raise KeyError(f"Belief {belief_id} not found.")

        self.evidence_registry.register(evidence)
        if evidence.polarity == EvidencePolarity.SUPPORTING:
            delta = 0.10 if evidence.strength == EvidenceStrength.WEAK else (0.25 if evidence.strength == EvidenceStrength.MODERATE else 0.45)
            belief.strengthen(evidence.evidence_id, delta=delta, verifier_id=evidence.source_id)
        elif evidence.polarity == EvidencePolarity.CONTRADICTING:
            penalty = 0.15 if evidence.strength == EvidenceStrength.WEAK else (0.35 if evidence.strength == EvidenceStrength.MODERATE else 0.60)
            belief.weaken(evidence.evidence_id, penalty=penalty, verifier_id=evidence.source_id)

        return belief

    def age_beliefs(self, elapsed_seconds: float) -> int:
        """Apply decay across all active beliefs; returns number of beliefs that died."""
        dead_count = 0
        for b in list(self._beliefs.values()):
            if b.is_alive():
                b.apply_decay(elapsed_seconds)
                if not b.is_alive():
                    dead_count += 1
        return dead_count

    def summarize_epistemic_state(self) -> Dict[str, Any]:
        """Generate high-level view of what Alpha currently believes, doubts, and rejects."""
        active = [b for b in self._beliefs.values() if b.is_alive()]
        dead = [b for b in self._beliefs.values() if not b.is_alive()]
        avg_conf = sum(b.confidence for b in active) / max(1, len(active))

        distribution = {lvl.value: 0 for lvl in UncertaintyLevel}
        for b in active:
            lvl = self.uncertainty_engine.classify_confidence(b.confidence)
            distribution[lvl.value] += 1

        return {
            "total_beliefs": len(self._beliefs),
            "active_beliefs": len(active),
            "dead_beliefs": len(dead),
            "average_confidence": round(avg_conf, 3),
            "certainty_distribution": distribution
        }
