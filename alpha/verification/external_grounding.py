"""External Grounding Monitor: Empirical Anchoring & Drift Mitigation for Project Alpha (Phase 8).

Prevents Alpha from becoming internally consistent but objectively wrong by anchoring
its beliefs to external physical reality:
- Verified repositories (file system, source code syntax, git status)
- Reference datasets (benchmarks, telemetry metrics, verified data files)
- Validation corpora (canonical specifications, test outputs)
- Architectural invariants (identity hashes, process isolation rules, constitutional constraints)

Computes:
- Reality Distance Score: How far beliefs diverge from actual ground-truth reality.
- Grounding Score: Fraction of beliefs backed by external physical/verified sources.
- Drift Score: Rate of drift away from architectural invariants.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from alpha.world_model.ontology.entities import LifecycleState
from alpha.world_model.epistemology.belief import Belief, BeliefSystem

logger = logging.getLogger("alpha.verification.external_grounding")


class GroundingAuditReport(BaseModel):
    """Metrics and verification findings regarding Alpha's empirical grounding."""
    timestamp: float = Field(default_factory=time.time)
    reality_distance_score: float = 0.0  # [0.0, 1.0], 0.0 is perfect alignment
    grounding_score: float = 1.0         # [0.0, 1.0], fraction anchored to external reality
    drift_score: float = 0.0             # [0.0, 1.0], drift away from invariant baselines
    status: str = "NOMINAL"              # NOMINAL, EPISTEMIC_DRIFT_WARNING, CRITICAL_DRIFT
    total_beliefs_audited: int = 0
    anchored_beliefs_count: int = 0
    unanchored_beliefs_count: int = 0
    verified_files_checked: int = 0
    failed_file_checks: List[str] = Field(default_factory=list)
    invariant_violations: List[str] = Field(default_factory=list)
    divergent_beliefs: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


class ExternalGroundingMonitor:
    """Rigorous empirical watchdog tying cognitive representations to ground-truth reality."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        world_model: Optional[Any] = None,
        belief_system: Optional[BeliefSystem] = None,
        baseline_invariants: Optional[Dict[str, Any]] = None,
    ):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.world_model = world_model
        self.belief_system = belief_system or (getattr(world_model, "beliefs", None) if world_model else None)
        self.baseline_invariants = baseline_invariants or self._load_default_invariants()
        self._history: List[GroundingAuditReport] = []

    def _load_default_invariants(self) -> Dict[str, Any]:
        """Baseline constitutional and system invariants that must never drift."""
        return {
            "root_directory_exists": True,
            "core_modules": [
                "alpha/core",
                "alpha/world_model",
                "alpha/verification",
                "alpha/agents",
            ],
            "max_tolerated_drift": 0.15,
            "min_required_grounding": 0.70,
        }

    def audit_grounding(self) -> GroundingAuditReport:
        """Run complete external grounding audit."""
        failed_files: List[str] = []
        invariant_violations: List[str] = []
        divergent_beliefs: List[Dict[str, Any]] = []

        # 1. Audit Verified Repositories (Code files on disk)
        core_dirs = self.baseline_invariants.get("core_modules", [])
        files_checked = 0
        for rel_dir in core_dirs:
            p = self.workspace_root / rel_dir
            if not p.exists() or not p.is_dir():
                invariant_violations.append(f"Core directory missing on disk: {rel_dir}")
            else:
                for py_file in p.glob("*.py"):
                    files_checked += 1
                    try:
                        # Verify physical existence and valid python AST
                        content = py_file.read_text(encoding="utf-8")
                        ast.parse(content)
                    except Exception as e:
                        failed_files.append(f"{py_file.name}: {str(e)}")

        # 2. Audit Beliefs against External Reality
        beliefs = self.belief_system.get_all() if self.belief_system else []
        total_beliefs = len(beliefs)
        anchored_count = 0
        distance_accum = 0.0

        for b in beliefs:
            if b.lifecycle_state != LifecycleState.ACTIVE:
                continue

            has_doc = len(b.source_documents) > 0
            has_obs = len(b.observations) > 0
            has_ev = len(b.supporting_evidence) > 0
            has_ext_source = len(b.sources) > 0

            if has_doc or has_obs or has_ev or has_ext_source:
                anchored_count += 1
            else:
                # If belief has no external grounding anchors
                divergent_beliefs.append({
                    "belief_id": b.belief_id,
                    "statement": b.statement,
                    "reason": "Lacks external physical/repository anchor",
                })
                distance_accum += 1.0

            # Check validity of referenced source documents
            for doc in b.source_documents:
                doc_path = Path(doc)
                if not doc_path.is_absolute():
                    doc_path = (self.workspace_root / doc_path).resolve()
                if not doc_path.exists():
                    divergent_beliefs.append({
                        "belief_id": b.belief_id,
                        "statement": b.statement,
                        "reason": f"Referenced source document does not exist: {doc}",
                    })
                    distance_accum += 1.0

        # Calculate Scores
        active_count = sum(1 for b in beliefs if b.lifecycle_state == LifecycleState.ACTIVE)
        grounding_score = round(anchored_count / max(1, active_count), 3) if active_count > 0 else 1.0
        reality_distance_score = round(min(1.0, distance_accum / max(1, active_count)), 3) if active_count > 0 else 0.0

        # Drift Score: combination of invariant violations and reality distance
        drift_score = round(
            min(1.0, (len(invariant_violations) * 0.3) + (len(failed_files) * 0.1) + (reality_distance_score * 0.5)),
            3,
        )

        status = "NOMINAL"
        if drift_score >= 0.3 or reality_distance_score >= 0.25:
            status = "CRITICAL_DRIFT"
        elif drift_score >= 0.15 or reality_distance_score >= 0.15 or grounding_score < 0.70:
            status = "EPISTEMIC_DRIFT_WARNING"

        summary = (
            f"Grounding Audit: Status {status} | Reality Distance: {reality_distance_score} | "
            f"Grounding Score: {grounding_score} | Drift Score: {drift_score} | "
            f"Audited {active_count} active beliefs, {files_checked} verified files."
        )

        report = GroundingAuditReport(
            reality_distance_score=reality_distance_score,
            grounding_score=grounding_score,
            drift_score=drift_score,
            status=status,
            total_beliefs_audited=active_count,
            anchored_beliefs_count=anchored_count,
            unanchored_beliefs_count=max(0, active_count - anchored_count),
            verified_files_checked=files_checked,
            failed_file_checks=failed_files,
            invariant_violations=invariant_violations,
            divergent_beliefs=divergent_beliefs,
            summary=summary,
        )

        self._history.append(report)
        return report
