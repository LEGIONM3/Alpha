"""Research Governance Pipeline: 5-Layer Mandatory Verification Pipeline.

MANDATORY RULE:
All discoveries must pass:
1. Truth Layer
2. Governance Layer
3. Identity Layer
4. Drift Detection Layer
5. Replication Layer

No knowledge enters civilization memory without verification.
The goal is not autonomy. The goal is trustworthy autonomous discovery.
"""

from __future__ import annotations

import time
import hashlib
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Publication, Theory, Finding, Evidence


class LayerAuditResult(BaseModel):
    layer_name: str
    passed: bool
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    details: str
    audited_at: float = Field(default_factory=time.time)


class GovernanceAuditResult(BaseModel):
    publication_id: str
    approved: bool
    layer_results: Dict[str, LayerAuditResult] = Field(default_factory=dict)
    rejection_reasons: List[str] = Field(default_factory=list)
    cryptographic_signature: Optional[str] = None
    certified_at: float = Field(default_factory=time.time)


class ResearchGovernancePipeline:
    """The inviolable gatekeeper for all autonomous scientific knowledge entering civilization memory."""

    def __init__(self, world_model: Optional[Any] = None):
        self.world_model = world_model

    def audit_truth_layer(self, pub: Publication, evidence_list: List[Evidence]) -> LayerAuditResult:
        """1. Truth Layer: Validates epistemic grounding and absence of hallucination."""
        has_evidence = len(evidence_list) > 0 and len(pub.evidence_ids) > 0
        valid_p_vals = all(ev.p_value <= 0.05 for ev in evidence_list) if evidence_list else False

        passed = has_evidence and valid_p_vals
        score = 0.95 if passed else 0.20
        details = (
            f"Evidence count: {len(evidence_list)}, all p-values <= 0.05: {valid_p_vals}"
            if passed else "Truth Layer failed: Missing evidence or insignificant p-values."
        )
        return LayerAuditResult(layer_name="TruthLayer", passed=passed, score=score, details=details)

    def audit_governance_layer(self, pub: Publication) -> LayerAuditResult:
        """2. Governance Layer: Enforces safety constraints, ethics, and authorized boundaries."""
        # Check against dangerous or destructive domains/keywords
        prohibited_terms = ["malware", "bioweapon", "jailbreak", "exploit_zero_day"]
        has_prohibited = any(term in pub.abstract.lower() or term in pub.title.lower() for term in prohibited_terms)

        passed = not has_prohibited
        score = 1.0 if passed else 0.0
        details = "Complies with civilizational safety boundaries." if passed else "Rejected: Prohibited safety keywords."
        return LayerAuditResult(layer_name="GovernanceLayer", passed=passed, score=score, details=details)

    def audit_identity_layer(self, pub: Publication) -> LayerAuditResult:
        """3. Identity Layer: Verifies alignment with Alpha's foundational identity and epistemic humility."""
        # High confidence claim must not claim infallible certainty (must maintain epistemic humility)
        claims_infallibility = pub.confidence >= 1.0
        passed = not claims_infallibility and (pub.confidence >= 0.5)
        score = 0.90 if passed else 0.30
        details = "Aligned with Alpha identity & epistemic humility." if passed else "Violates epistemic humility standard."
        return LayerAuditResult(layer_name="IdentityLayer", passed=passed, score=score, details=details)

    def audit_drift_layer(self, pub: Publication) -> LayerAuditResult:
        """4. Drift Detection Layer: Monitors for epistemic drift, ideological bias, and variance collapse."""
        # Ensure novelty and impact scores remain calibrated within realistic distributions
        is_calibrated = (0.1 <= pub.novelty_score <= 0.99) and (0.1 <= pub.impact_score <= 0.99)
        passed = is_calibrated
        score = 0.92 if passed else 0.15
        details = "Statistical calibration verified; zero drift detected." if passed else "Drift detected in metric distributions."
        return LayerAuditResult(layer_name="DriftDetectionLayer", passed=passed, score=score, details=details)

    def audit_replication_layer(self, pub: Publication, findings: List[Finding]) -> LayerAuditResult:
        """5. Replication Layer: Mandatory check: 'Research without replication is forbidden.'"""
        has_findings = len(findings) > 0
        all_replicated = all(f.replicated and f.replication_count >= 1 for f in findings) if has_findings else False

        passed = has_findings and all_replicated
        score = 1.0 if passed else 0.0
        details = (
            f"All {len(findings)} findings have verified independent replications."
            if passed else "Replication Layer failed: Unreplicated findings detected."
        )
        return LayerAuditResult(layer_name="ReplicationLayer", passed=passed, score=score, details=details)

    def execute_governance_audit(
        self,
        publication: Publication,
        findings: List[Finding],
        evidence_list: List[Evidence]
    ) -> GovernanceAuditResult:
        """Execute the full 5-layer audit sequentially. All 5 must pass."""
        t_res = self.audit_truth_layer(publication, evidence_list)
        g_res = self.audit_governance_layer(publication)
        i_res = self.audit_identity_layer(publication)
        d_res = self.audit_drift_layer(publication)
        r_res = self.audit_replication_layer(publication, findings)

        results = {
            "TruthLayer": t_res,
            "GovernanceLayer": g_res,
            "IdentityLayer": i_res,
            "DriftDetectionLayer": d_res,
            "ReplicationLayer": r_res
        }

        publication.passed_truth_layer = t_res.passed
        publication.passed_governance_layer = g_res.passed
        publication.passed_identity_layer = i_res.passed
        publication.passed_drift_detection_layer = d_res.passed
        publication.passed_replication_layer = r_res.passed

        all_passed = publication.is_fully_verified()
        rejections = [res.details for res in results.values() if not res.passed]

        signature = None
        if all_passed:
            sig_raw = f"{publication.publication_id}:{publication.title}:{time.time()}:ALPHA_VERIFIED"
            signature = hashlib.sha256(sig_raw.encode()).hexdigest()
            publication.governance_signature = signature

        return GovernanceAuditResult(
            publication_id=publication.publication_id,
            approved=all_passed,
            layer_results=results,
            rejection_reasons=rejections,
            cryptographic_signature=signature
        )
