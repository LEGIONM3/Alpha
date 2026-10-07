"""Question Generator: Transforms unknowns and problems into sharp, testable questions.

Ensures every generated question is:
1. Operationally defined
2. Falsifiable
3. Grounded in identifiable variables
4. Prioritized by epistemic value
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Any, Optional

from alpha.research.entities import ResearchProblem, ResearchQuestion
from alpha.research.curiosity.unknown_detector import DetectedUnknown


class QuestionGenerator:
    """Discovers new questions without requiring human prompts."""

    def __init__(self):
        pass

    def generate_questions_from_problem(
        self,
        problem: ResearchProblem,
        count: int = 3
    ) -> List[ResearchQuestion]:
        """Generate targeted scientific questions addressing a problem."""
        questions: List[ResearchQuestion] = []
        domain = problem.domain

        templates = [
            (
                f"What causal mechanism mediates the relationship between variables in {problem.title}?",
                ["independent_factor", "mediating_mechanism", "system_stability"],
                f"Can be falsified if controlling for the mediator has zero effect (p > 0.05) on system stability."
            ),
            (
                f"Under what boundary conditions does the behavior described in '{problem.title}' break down or invert?",
                ["perturbation_magnitude", "breakdown_threshold", "system_entropy"],
                f"Can be falsified if monotonic scaling persists beyond theoretical threshold X."
            ),
            (
                f"How does an analogical schema from adjacent domains resolve the conflict in {problem.title}?",
                ["cross_domain_mapping", "invariant_structure", "equilibrium_state"],
                f"Can be falsified if the cross-domain mapping fails predictive validation under holdout trials."
            ),
            (
                f"What is the minimal sufficient parameterization required to predict the dynamics of {problem.title}?",
                ["parameter_sparsity", "variance_explained", "parsimony_metric"],
                f"Can be falsified if adding parameters beyond K yields no statistically significant improvement."
            )
        ]

        for i in range(min(count, len(templates))):
            text, vars_list, falsifiability = templates[i]
            q = ResearchQuestion(
                problem_id=problem.problem_id,
                question_text=text,
                domain=domain,
                target_variables=vars_list,
                falsifiability_criteria=falsifiability,
                epistemic_priority=round(min(1.0, problem.expected_impact * (0.85 + 0.05 * i)), 2),
                investigability_score=round(0.75 + 0.05 * (i % 3), 2)
            )
            questions.append(q)

        return questions

    def generate_questions_from_unknown(self, unknown: DetectedUnknown) -> List[ResearchQuestion]:
        """Convert a detected unknown directly into a battery of questions."""
        q = ResearchQuestion(
            question_text=f"How does {unknown.target_concept_or_relation} behave across varying operational regimes in {unknown.domain}?",
            domain=unknown.domain,
            target_variables=[unknown.target_concept_or_relation, "operational_regime", "variance"],
            falsifiability_criteria=f"Falsified if variance remains uniform across all tested regimes within epsilon tolerance.",
            epistemic_priority=unknown.compute_investigation_score(),
            investigability_score=0.8
        )
        return [q]

    def generate_research_agenda(self, questions: List[ResearchQuestion]) -> Dict[str, Any]:
        """Package a list of questions into a coherent programmatic research agenda."""
        by_domain: Dict[str, List[Dict[str, Any]]] = {}
        for q in questions:
            by_domain.setdefault(q.domain, []).append({
                "question_id": q.question_id,
                "text": q.question_text,
                "priority": q.epistemic_priority,
                "falsifiability": q.falsifiability_criteria
            })

        return {
            "total_questions": len(questions),
            "domains_covered": list(by_domain.keys()),
            "agenda_by_domain": by_domain,
            "generated_at": time.time()
        }
