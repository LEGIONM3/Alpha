"""Publication Agent: Formats, documents, and prepares scientific discoveries for peer review."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from alpha.research.agents.base import ScientificAgentBase
from alpha.research.entities import Theory, Finding, Evidence, Publication


class PublicationAgent(ScientificAgentBase):
    """Specialized scientific publisher compiling verified discoveries into publication assets."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id=agent_id, role_name="PublicationAgent")

    def draft_publication(
        self,
        theory: Theory,
        findings: List[Finding],
        evidence_list: List[Evidence]
    ) -> Publication:
        """Create formal scientific publication entity."""
        abstract = (
            f"We present '{theory.name}', a comprehensive theory addressing dynamics in {theory.domain}. "
            f"Synthesizing {len(findings)} replicated empirical findings supported by {len(evidence_list)} "
            f"statistical evidence trails, this work demonstrates that {theory.principles[0] if theory.principles else 'empirical regularities hold'}. "
            f"Cross-domain implications span {', '.join(theory.cross_domains) if theory.cross_domains else 'adjacent fields'}."
        )

        pub = Publication(
            title=f"Theoretical and Empirical Foundations of {theory.name}",
            abstract=abstract,
            domain=theory.domain,
            author_agent=self.agent_id,
            theory_ids=[theory.theory_id],
            finding_ids=[f.finding_id for f in findings],
            evidence_ids=[ev.evidence_id for ev in evidence_list],
            novelty_score=0.88,
            impact_score=round(theory.explanatory_power * 0.95, 3),
            confidence=theory.confidence
        )

        self.log_action("draft_publication", target_id=pub.publication_id, title=pub.title)
        return pub
