"""System-Wide Drift Detection Suite: Identity, Goal, Belief, and Governance Invariance Auditing."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from alpha.core.identity import IdentityState, IdentityLoader, IdentityHashGenerator, IdentityDriftDetector
from alpha.world_model import CognitiveWorldModel, GoalEntity

logger = logging.getLogger(__name__)


class DriftBaseline(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    identity_hash: str
    governance_hash: str
    goal_hash: str
    belief_hash: str
    goals_manifest: List[Dict[str, Any]] = Field(default_factory=list)
    beliefs_manifest: List[Dict[str, Any]] = Field(default_factory=list)


class SystemDriftAuditResult(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    has_drift: bool = False
    drift_score: float = 0.0  # 0.0 to 1.0
    identity_drift: bool = False
    governance_drift: bool = False
    goal_drift: bool = False
    belief_drift: bool = False
    drift_details: List[str] = Field(default_factory=list)


class SystemDriftEngine:
    """Computes cryptographic baseline digests and detects runtime semantic drift."""

    def __init__(self, baseline_file: str = "data/drift_baselines.json"):
        self.baseline_file = Path(baseline_file)
        self.baseline: Optional[DriftBaseline] = None
        self._load_or_create_baseline()

    def _load_or_create_baseline(self) -> None:
        if self.baseline_file.exists():
            try:
                data = json.loads(self.baseline_file.read_text(encoding="utf-8"))
                self.baseline = DriftBaseline(**data)
            except Exception:
                pass

    def establish_baseline(
        self,
        identity: IdentityState,
        world_model: CognitiveWorldModel
    ) -> DriftBaseline:
        """Create and persist a formal cryptographic snapshot of current invariants."""
        # 1. Identity hash
        id_hash = identity.identity_hash

        # 2. Governance hash (constitution + constraints + non-negotiables)
        gov_dict = {
            "constitution": sorted(identity.constitution),
            "constraints": sorted(identity.constraints),
            "non_negotiables": sorted(identity.non_negotiables)
        }
        gov_hash = hashlib.sha256(json.dumps(gov_dict, sort_keys=True).encode("utf-8")).hexdigest()

        # 3. Goal hash
        from alpha.world_model.ontology.entities import EntityType
        goals = world_model.ontology.get_by_type(EntityType.GOAL)
        goal_manifest = [{"id": g.id, "name": g.name, "objective": getattr(g, "objective", g.name)} for g in goals]
        goal_hash = hashlib.sha256(json.dumps(goal_manifest, sort_keys=True).encode("utf-8")).hexdigest()

        # 4. Belief hash
        beliefs = world_model.beliefs.get_active_beliefs(min_confidence=0.5)
        belief_manifest = [{"id": b.belief_id, "statement": b.statement, "confidence": b.confidence} for b in beliefs]
        belief_hash = hashlib.sha256(json.dumps(belief_manifest, sort_keys=True).encode("utf-8")).hexdigest()

        baseline = DriftBaseline(
            identity_hash=id_hash,
            governance_hash=gov_hash,
            goal_hash=goal_hash,
            belief_hash=belief_hash,
            goals_manifest=goal_manifest,
            beliefs_manifest=belief_manifest
        )

        self.baseline = baseline
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self.baseline_file.write_text(baseline.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Established and persisted DRIFT BASELINE to {self.baseline_file}")
        return baseline

    def audit_drift(
        self,
        current_identity: IdentityState,
        current_world_model: CognitiveWorldModel
    ) -> SystemDriftAuditResult:
        """Evaluate active system state against the persisted baseline."""
        if not self.baseline:
            self.establish_baseline(current_identity, current_world_model)

        details: List[str] = []
        id_drift = False
        gov_drift = False
        goal_drift = False
        belief_drift = False

        # 1. Audit Identity
        current_id_hash = current_identity.identity_hash
        if current_id_hash != self.baseline.identity_hash:
            id_drift = True
            details.append(f"Identity Hash Mutation: expected {self.baseline.identity_hash[:12]}, got {current_id_hash[:12]}")

        # 2. Audit Governance
        gov_dict = {
            "constitution": sorted(current_identity.constitution),
            "constraints": sorted(current_identity.constraints),
            "non_negotiables": sorted(current_identity.non_negotiables)
        }
        current_gov_hash = hashlib.sha256(json.dumps(gov_dict, sort_keys=True).encode("utf-8")).hexdigest()
        if current_gov_hash != self.baseline.governance_hash:
            gov_drift = True
            details.append("Governance Invariant Mutation: constitutional rules altered")

        # 3. Audit Goals
        from alpha.world_model.ontology.entities import EntityType
        goals = current_world_model.ontology.get_by_type(EntityType.GOAL)
        current_goal_manifest = [{"id": g.id, "name": g.name, "objective": getattr(g, "objective", g.name)} for g in goals]
        current_goal_hash = hashlib.sha256(json.dumps(current_goal_manifest, sort_keys=True).encode("utf-8")).hexdigest()
        if current_goal_hash != self.baseline.goal_hash:
            goal_drift = True
            details.append("Goal Hierarchy Drift: active operational goals mutated or displaced")

        # 4. Audit Beliefs (significant confidence drop or removal)
        active_beliefs = current_world_model.beliefs.get_active_beliefs(min_confidence=0.5)
        current_belief_manifest = [{"id": b.belief_id, "statement": b.statement, "confidence": b.confidence} for b in active_beliefs]
        current_belief_hash = hashlib.sha256(json.dumps(current_belief_manifest, sort_keys=True).encode("utf-8")).hexdigest()
        if current_belief_hash != self.baseline.belief_hash:
            belief_drift = True
            details.append("Belief Graph Drift: active grounded beliefs updated or retired")

        has_drift = id_drift or gov_drift or goal_drift or belief_drift
        drift_score = (0.4 * int(id_drift)) + (0.3 * int(gov_drift)) + (0.15 * int(goal_drift)) + (0.15 * int(belief_drift))

        return SystemDriftAuditResult(
            has_drift=has_drift,
            drift_score=round(drift_score, 2),
            identity_drift=id_drift,
            governance_drift=gov_drift,
            goal_drift=goal_drift,
            belief_drift=belief_drift,
            drift_details=details
        )
