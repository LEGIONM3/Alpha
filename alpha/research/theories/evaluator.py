"""Theory Evaluator: Rigorous epistemic audit of scientific theories.

Enforces:
- MANDATORY INVARIANT: "Research without replication is forbidden."
- Explanatory power vs parsimony trade-offs
- Counterargument and adversarial stress testing
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Theory, Finding, ResearchStatus


class TheoryAuditReport(BaseModel):
    theory_id: str
    approved: bool
    status: ResearchStatus
    explanatory_score: float
    parsimony_score: float
    replication_audit_passed: bool
    adversarial_audit_passed: bool
    critique_notes: List[str] = Field(default_factory=list)


class TheoryEvaluator:
    """Rigorous gatekeeper assessing theoretical validity, replication, and parsimony."""

    def __init__(self, min_replication_threshold: int = 1):
        self.min_replication_threshold = min_replication_threshold

    def evaluate(self, theory: Theory, findings: List[Finding]) -> TheoryAuditReport:
        critiques = []

        # 1. Replication check: "Research without replication is forbidden"
        replicated_count = sum(1 for f in findings if f.replicated and f.replication_count >= self.min_replication_threshold)
        replication_passed = (replicated_count == len(findings)) and (len(findings) > 0)

        if not replication_passed:
            critiques.append(
                f"REPLICATION FORBIDDEN VIOLATION: {len(findings) - replicated_count} "
                f"findings lack verified replication (threshold={self.min_replication_threshold})."
            )

        # 2. Adversarial evaluation & counterargument testing
        adversarial_passed = all(f.adversarial_tested for f in findings)
        if not adversarial_passed:
            critiques.append("Counterargument testing incomplete for one or more underlying findings.")

        # 3. Parsimony vs Explanatory Power
        # High explanatory power with high parsimony is ideal
        composite_score = round(0.55 * theory.explanatory_power + 0.45 * theory.parsimony_score, 3)
        if composite_score < 0.65:
            critiques.append(f"Theory lacks sufficient parsimonious explanatory power ({composite_score} < 0.65).")

        is_approved = replication_passed and adversarial_passed and (composite_score >= 0.65)

        new_status = ResearchStatus.SUPPORTED if is_approved else ResearchStatus.PROPOSED
        theory.status = new_status

        return TheoryAuditReport(
            theory_id=theory.theory_id,
            approved=is_approved,
            status=new_status,
            explanatory_score=theory.explanatory_power,
            parsimony_score=theory.parsimony_score,
            replication_audit_passed=replication_passed,
            adversarial_audit_passed=adversarial_passed,
            critique_notes=critiques
        )
