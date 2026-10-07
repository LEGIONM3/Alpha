"""Epistemic Health Dashboard: Real-time Health Telemetry for Project Alpha (Phase 8).

Tracks and serializes the cognitive truth and epistemic integrity metrics of Alpha:
- Total Beliefs
- Verified Beliefs
- Contradicted Beliefs
- Unverified Beliefs
- Quarantined Beliefs
- Average Confidence
- Grounding Score
- Reality Index
- Causal Integrity
- Drift Risk

Persists to EPISTEMIC_HEALTH.json.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.world_model.ontology.entities import LifecycleState
from alpha.world_model.epistemology.belief import Belief, BeliefSystem

logger = logging.getLogger("alpha.verification.epistemic_health")


class EpistemicHealthMetrics(BaseModel):
    """Schema for EPISTEMIC_HEALTH.json."""
    timestamp: float = Field(default_factory=time.time)
    last_updated_iso: str = ""
    status: str = "HEALTHY"  # HEALTHY, WARNING, DEGRADED, CRITICAL
    total_beliefs: int = 0
    verified_beliefs: int = 0
    contradicted_beliefs: int = 0
    unverified_beliefs: int = 0
    quarantined_beliefs: int = 0
    average_confidence: float = 0.5
    grounding_score: float = 1.0
    reality_index: float = 1.0
    reality_distance_score: float = 0.0
    causal_integrity: float = 1.0
    drift_risk: str = "LOW"  # LOW, MODERATE, HIGH, CRITICAL
    drift_score: float = 0.0
    active_contradictions: int = 0
    quarantine_count: int = 0
    immune_system_status: str = "VIGILANT"
    details: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""


class EpistemicHealthDashboard:
    """Aggregates epistemic health across all Phase 8 subsystems and outputs EPISTEMIC_HEALTH.json."""

    def __init__(
        self,
        world_model: Optional[Any] = None,
        workspace_root: Optional[Path] = None,
        external_grounding: Optional[Any] = None,
        contradiction_engine: Optional[Any] = None,
        causal_validator: Optional[Any] = None,
        immune_system: Optional[Any] = None,
    ):
        self.world_model = world_model
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.external_grounding = external_grounding
        self.contradiction_engine = contradiction_engine
        self.causal_validator = causal_validator
        self.immune_system = immune_system

    def compute_health_metrics(self) -> EpistemicHealthMetrics:
        """Collect metrics across all truth and verification components."""
        bs = getattr(self.world_model, "beliefs", None) if self.world_model else None

        # 1. Beliefs metrics
        beliefs = bs.get_all() if bs else []
        total_beliefs = len(beliefs)
        active_beliefs = [b for b in beliefs if b.lifecycle_state == LifecycleState.ACTIVE]

        verified_count = sum(1 for b in active_beliefs if b.verification_status == "VERIFIED")
        contradicted_count = sum(1 for b in active_beliefs if b.verification_status == "CONTRADICTED" or len(b.contradicting_evidence) > 0)
        quarantined_count = sum(1 for b in beliefs if b.verification_status == "QUARANTINED")
        unverified_count = sum(1 for b in active_beliefs if b.verification_status == "UNVERIFIED" and len(b.contradicting_evidence) == 0)

        avg_conf = (
            round(sum(b.confidence_score for b in active_beliefs) / max(1, len(active_beliefs)), 3)
            if active_beliefs
            else 0.5
        )

        # 2. External Grounding & Reality
        grounding_score = 1.0
        reality_distance = 0.0
        drift_score = 0.0
        drift_risk = "LOW"

        if self.external_grounding and hasattr(self.external_grounding, "audit_grounding"):
            g_report = self.external_grounding.audit_grounding()
            grounding_score = g_report.grounding_score
            reality_distance = g_report.reality_distance_score
            drift_score = g_report.drift_score
            if drift_score >= 0.3 or reality_distance >= 0.25:
                drift_risk = "CRITICAL"
            elif drift_score >= 0.15 or reality_distance >= 0.15 or grounding_score < 0.70:
                drift_risk = "MODERATE"

        reality_index = round(max(0.0, 1.0 - reality_distance), 3)

        # 3. Causal Integrity
        causal_integrity = 1.0
        if self.causal_validator and hasattr(self.causal_validator, "validate_graph"):
            c_report = self.causal_validator.validate_graph()
            causal_integrity = c_report.causal_integrity_score
        elif self.world_model and hasattr(self.world_model, "causal"):
            cg = getattr(self.world_model.causal, "cause_graph", None)
            if cg:
                from alpha.world_model.causal.validation import CauseGraphValidator
                val = CauseGraphValidator(cg)
                causal_integrity = val.validate_graph().causal_integrity_score

        # 4. Contradictions
        active_contradictions = 0
        if self.contradiction_engine and hasattr(self.contradiction_engine, "scan_all"):
            c_rep = self.contradiction_engine.scan_all()
            active_contradictions = c_rep.unresolved_count

        # 5. Immune System
        immune_status = "VIGILANT"
        active_quarantines = quarantined_count
        if self.immune_system and hasattr(self.immune_system, "get_immune_health"):
            imm_data = self.immune_system.get_immune_health()
            immune_status = imm_data.get("status", "VIGILANT")
            active_quarantines = max(active_quarantines, imm_data.get("active_quarantines", 0))

        # Overall Status
        if drift_risk == "CRITICAL" or contradicted_count > 3 or causal_integrity < 0.6:
            system_status = "CRITICAL"
        elif drift_risk == "MODERATE" or active_contradictions > 0 or quarantined_count > 0 or causal_integrity < 0.85:
            system_status = "WARNING"
        elif unverified_count > total_beliefs * 0.5:
            system_status = "DEGRADED"
        else:
            system_status = "HEALTHY"

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        summary = (
            f"Epistemic Health [{system_status}]: {verified_count}/{total_beliefs} verified beliefs. "
            f"Reality Index: {reality_index} | Grounding: {grounding_score} | Causal Integrity: {causal_integrity} | "
            f"Active Contradictions: {active_contradictions} | Quarantined: {active_quarantines}."
        )

        return EpistemicHealthMetrics(
            last_updated_iso=now_iso,
            status=system_status,
            total_beliefs=total_beliefs,
            verified_beliefs=verified_count,
            contradicted_beliefs=contradicted_count,
            unverified_beliefs=unverified_count,
            quarantined_beliefs=active_quarantines,
            average_confidence=avg_conf,
            grounding_score=grounding_score,
            reality_index=reality_index,
            reality_distance_score=reality_distance,
            causal_integrity=causal_integrity,
            drift_risk=drift_risk,
            drift_score=drift_score,
            active_contradictions=active_contradictions,
            quarantine_count=active_quarantines,
            immune_system_status=immune_status,
            details={
                "active_beliefs": len(active_beliefs),
                "dead_beliefs": len(beliefs) - len(active_beliefs),
            },
            summary=summary,
        )

    def save_to_file(self, target_path: Optional[Path] = None) -> Path:
        """Write EPISTEMIC_HEALTH.json to file."""
        out_path = target_path or (self.workspace_root / "EPISTEMIC_HEALTH.json")
        metrics = self.compute_health_metrics()
        out_path.write_text(json.dumps(metrics.model_dump(), indent=2), encoding="utf-8")
        logger.info("EPISTEMIC_HEALTH.json updated at %s", out_path)
        return out_path
