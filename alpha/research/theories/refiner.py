"""Theory Refiner: Incrementally evolves theories as new discoveries emerge."""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional
from alpha.research.entities import Theory, Finding


class TheoryRefiner:
    """Updates theory parameters and boundary conditions without discarding empirical foundations."""

    def refine_theory(
        self,
        theory: Theory,
        new_findings: List[Finding],
        refinement_notes: str = ""
    ) -> Theory:
        """Incorporate new findings to update theory parameters and principles."""
        for f in new_findings:
            if f.finding_id not in theory.finding_ids:
                theory.finding_ids.append(f.finding_id)

        # Update explanatory scope
        theory.explanatory_power = round(min(0.99, theory.explanatory_power + 0.03 * len(new_findings)), 3)
        # Update parsimony with slight complexity dampener
        theory.parsimony_score = round(max(0.50, theory.parsimony_score - 0.01 * len(new_findings)), 3)

        theory.version += 1
        theory.principles.append(
            f"Refinement v{theory.version}: Extended boundary conditions to cover {new_findings[-1].claim if new_findings else 'new domains'}."
        )
        theory.updated_at = time.time()
        return theory
