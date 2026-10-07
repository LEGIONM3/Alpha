"""Epistemic Auditor Agent: Permanent Adversarial Socratic Critic for Project Alpha (Phase 8).

Permanent Role: Question Everything.

Responsibilities:
- Challenge assumptions: Questions unstated premises and boundary limits.
- Attack weak evidence: Probes provenance, sample sizes, and empirical quality.
- Attack weak reasoning: Exposes fallacies (post hoc, affirming the consequent, confirmation bias).
- Search for alternative explanations: Formulates rival hypotheses to prevent delusion.
- Reject unsupported beliefs: Triggers immune quarantine or demotion for beliefs failing scrutiny.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.world_model.ontology.entities import LifecycleState
from alpha.world_model.epistemology.belief import Belief, BeliefSystem
from alpha.world_model.epistemology.evidence_chain import EvidenceChainEngine
from alpha.world_model.epistemology.immune_system import WorldModelImmuneSystem, ThreatType

logger = logging.getLogger("alpha.agents.epistemic_auditor")


class AuditFinding(BaseModel):
    """Detailed finding produced when the Epistemic Auditor attacks a belief."""
    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    belief_id: str
    statement: str
    challenge_type: str  # ASSUMPTION_CHALLENGE, EVIDENCE_ATTACK, REASONING_ATTACK, ALTERNATIVE_EXPLANATION, REJECTION
    severity: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    critique: str
    recommended_action: str
    alternative_hypotheses: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class EpistemicAuditReport(BaseModel):
    """Full system audit report compiling all challenges and interventions."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    findings: List[AuditFinding] = Field(default_factory=list)
    total_beliefs_audited: int = 0
    challenges_issued: int = 0
    beliefs_demoted: int = 0
    beliefs_quarantined: int = 0
    summary: str = ""


class EpistemicAuditorAgent:
    """The uncompromising Socratic prosecutor of Alpha's World Model."""

    def __init__(
        self,
        name: str = "EpistemicAuditor",
        belief_system: Optional[BeliefSystem] = None,
        evidence_chain_engine: Optional[EvidenceChainEngine] = None,
        immune_system: Optional[WorldModelImmuneSystem] = None,
    ):
        self.name = name
        self.belief_system = belief_system
        self.evidence_chain_engine = evidence_chain_engine
        self.immune_system = immune_system
        self._audit_history: List[EpistemicAuditReport] = []

    def challenge_assumptions(self, belief: Belief) -> Optional[AuditFinding]:
        """Scrutinize unstated premises and presuppositions behind the belief."""
        text = belief.statement.lower()

        # Check for universal generalizations ("always", "never", "all", "impossible")
        universals = ["always", "never", "all ", "impossible", "guaranteed", "perfect"]
        matched_univ = [u for u in universals if u in text]
        if matched_univ:
            return AuditFinding(
                belief_id=belief.belief_id,
                statement=belief.statement,
                challenge_type="ASSUMPTION_CHALLENGE",
                severity="HIGH",
                critique=(
                    f"Belief relies on unverified universal quantifier ({matched_univ}). "
                    f"Assumes invariance across unseen edge cases or non-stationary domains."
                ),
                recommended_action="Qualify scope with explicit operational boundary conditions.",
                alternative_hypotheses=[
                    f"Claim holds only under nominal conditions, failing under edge regimes.",
                    f"Negative evidence exists in unobserved stress partitions.",
                ],
            )

        # Check for unstated environmental assumptions
        if "fast" in text or "scalable" in text or "stable" in text:
            if not any("benchmark" in s or "latency" in s for s in belief.sources):
                return AuditFinding(
                    belief_id=belief.belief_id,
                    statement=belief.statement,
                    challenge_type="ASSUMPTION_CHALLENGE",
                    severity="MEDIUM",
                    critique="Subjective performance assertion lacks quantitative threshold or baseline definition.",
                    recommended_action="Replace qualitative claim with verifiable metric bounds.",
                )

        return None

    def attack_weak_evidence(self, belief: Belief) -> Optional[AuditFinding]:
        """Probe for evidentiary vulnerabilities, small samples, and stale data."""
        # 1. Zero evidence with high confidence
        total_evidence = len(belief.supporting_evidence) + len(belief.observations) + len(belief.source_documents)
        if total_evidence == 0 and belief.confidence_score > 0.4:
            return AuditFinding(
                belief_id=belief.belief_id,
                statement=belief.statement,
                challenge_type="EVIDENCE_ATTACK",
                severity="CRITICAL",
                critique=f"Belief asserts confidence {belief.confidence_score} with zero grounding evidence.",
                recommended_action="Demote confidence immediately to 0.1 or quarantine.",
                alternative_hypotheses=["The claim is an ungrounded hallucination or legacy remnant."],
            )

        # 2. Single source vulnerability
        if len(belief.sources) == 1 and total_evidence <= 1 and belief.confidence_score > 0.8:
            return AuditFinding(
                belief_id=belief.belief_id,
                statement=belief.statement,
                challenge_type="EVIDENCE_ATTACK",
                severity="HIGH",
                critique=f"Single point of evidentiary failure: Relies solely on 1 source ({belief.sources[0]}) with high confidence {belief.confidence_score}.",
                recommended_action="Gather independent corroboration before treating as established truth.",
            )

        # 3. Chain validation if engine available
        if self.evidence_chain_engine:
            val = self.evidence_chain_engine.validate_chain(belief)
            if not val.is_valid:
                return AuditFinding(
                    belief_id=belief.belief_id,
                    statement=belief.statement,
                    challenge_type="EVIDENCE_ATTACK",
                    severity="HIGH",
                    critique=f"Evidence chain invalid: {', '.join(val.warnings)}",
                    recommended_action="Repair evidence chain or demote verification status.",
                )

        return None

    def attack_weak_reasoning(self, belief: Belief) -> Optional[AuditFinding]:
        """Detect cognitive fallacies, post hoc errors, and confirmation bias."""
        # If contradictory evidence exists but confidence was not penalized
        if len(belief.contradicting_evidence) > 0 and belief.confidence_score > 0.75:
            return AuditFinding(
                belief_id=belief.belief_id,
                statement=belief.statement,
                challenge_type="REASONING_ATTACK",
                severity="CRITICAL",
                critique=(
                    f"Confirmation bias detected: Belief maintains confidence {belief.confidence_score} "
                    f"despite {len(belief.contradicting_evidence)} active contradicting evidence records."
                ),
                recommended_action="Apply penalization and recalculate posterior uncertainty.",
                alternative_hypotheses=["The contradicting evidence refutes the core proposition."],
            )

        # Detect correlation assumed to be causation in statement text
        text = belief.statement.lower()
        if ("causes" in text or "leads to" in text) and not any("causal" in s or "experiment" in s for s in belief.sources):
            return AuditFinding(
                belief_id=belief.belief_id,
                statement=belief.statement,
                challenge_type="REASONING_ATTACK",
                severity="HIGH",
                critique="Causal claim made without documented intervention experiment or causal graph validation.",
                recommended_action="Downgrade claim from causal mechanism to observational correlation.",
                alternative_hypotheses=[
                    "Observed relation is mediated by an unmeasured confounder.",
                    "Reverse causation accounts for the empirical covariation.",
                ],
            )

        return None

    def search_alternative_explanations(self, belief: Belief) -> List[str]:
        """Proactively generate plausible competing explanations."""
        return [
            f"The phenomenon observed in '{belief.statement[:30]}' is an artifact of measurement noise.",
            f"An external unmonitored system variable caused the observed behavior.",
            f"The behavior is transient and will not reproduce under different load conditions.",
        ]

    def audit_belief(self, belief: Belief) -> List[AuditFinding]:
        """Subject a single belief to full adversarial interrogation."""
        findings: List[AuditFinding] = []

        # 1. Challenge Assumptions
        f_assump = self.challenge_assumptions(belief)
        if f_assump:
            findings.append(f_assump)

        # 2. Attack Evidence
        f_ev = self.attack_weak_evidence(belief)
        if f_ev:
            findings.append(f_ev)

        # 3. Attack Reasoning
        f_reas = self.attack_weak_reasoning(belief)
        if f_reas:
            findings.append(f_reas)

        # Enforcement: Act on critical findings
        for f in findings:
            if f.severity == "CRITICAL":
                if self.immune_system:
                    self.immune_system.quarantine_belief(
                        belief_id=belief.belief_id,
                        threat_type=ThreatType.EPISTEMIC_POISONING,
                        reason=f"Epistemic Auditor rejection: {f.critique}",
                        threat_level="CRITICAL",
                        remediation=f.recommended_action,
                    )
                else:
                    belief.weaken(contradiction_id="epistemic_auditor", penalty=0.4)

        return findings

    def audit_entire_system(self, world_model: Optional[Any] = None) -> EpistemicAuditReport:
        """Run system-wide audit across all beliefs in the world model."""
        bs = self.belief_system or (getattr(world_model, "beliefs", None) if world_model else None)
        if not bs:
            return EpistemicAuditReport(summary="No BeliefSystem available for audit.")

        all_beliefs = [b for b in bs.get_all() if b.lifecycle_state == LifecycleState.ACTIVE]
        all_findings: List[AuditFinding] = []
        demoted = 0
        quarantined = 0

        for b in all_beliefs:
            prev_status = b.verification_status
            prev_conf = b.confidence_score
            findings = self.audit_belief(b)
            if findings:
                all_findings.extend(findings)
                if b.verification_status == "QUARANTINED" and prev_status != "QUARANTINED":
                    quarantined += 1
                elif b.confidence_score < prev_conf:
                    demoted += 1

        report = EpistemicAuditReport(
            findings=all_findings,
            total_beliefs_audited=len(all_beliefs),
            challenges_issued=len(all_findings),
            beliefs_demoted=demoted,
            beliefs_quarantined=quarantined,
            summary=(
                f"Epistemic Auditor evaluated {len(all_beliefs)} beliefs. Issued {len(all_findings)} challenges. "
                f"Quarantined {quarantined} beliefs, demoted {demoted} beliefs."
            ),
        )
        self._audit_history.append(report)
        return report
