"""Theory Retirement: Orderly scientific paradigm shifts and deprecation of falsified models."""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional
from alpha.research.entities import Theory, Refutation, ResearchStatus


class TheoryRetirement:
    """Retires refuted theories while preserving intellectual history in research archives."""

    def __init__(self):
        self.retired_theories: Dict[str, Dict[str, Any]] = {}

    def retire_theory(
        self,
        theory: Theory,
        reason: str,
        counter_evidence_ids: Optional[List[str]] = None,
        refuting_agent: str = "CriticAgent",
        superseded_by_theory_id: Optional[str] = None
    ) -> Refutation:
        """Formally falsify and archive a theory."""
        refutation = Refutation(
            target_entity_id=theory.theory_id,
            target_type="Theory",
            author_agent=refuting_agent,
            counter_evidence_ids=counter_evidence_ids or [],
            argumentation=reason,
            falsification_metric=0.95
        )

        theory.status = ResearchStatus.RETIRED
        theory.retirement_reason = reason
        theory.updated_at = time.time()

        self.retired_theories[theory.theory_id] = {
            "theory": theory,
            "refutation": refutation,
            "superseded_by": superseded_by_theory_id,
            "retired_at": time.time()
        }

        return refutation
