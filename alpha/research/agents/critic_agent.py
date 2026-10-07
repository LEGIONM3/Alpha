"""Critic Agent: Adversarial scientific peer reviewer hunting for flaws, confounds, and biases."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from alpha.research.agents.base import ScientificAgentBase
from alpha.research.entities import Hypothesis, Finding, Experiment, Evidence


class CriticAgent(ScientificAgentBase):
    """Adversarial scientist performing stress tests and counterargument analysis."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id=agent_id, role_name="CriticAgent")

    def critique_hypothesis(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """Subject hypothesis to adversarial counterarguments."""
        counterarguments = [
            f"Confounding Risk: {hypothesis.analogy_source or 'Mechanism'} may be an epiphenomenon of unmeasured latent variables.",
            "Boundary Fragility: Hypothesis may fail catastrophically under out-of-distribution extremes.",
            "Parsimony Challenge: Simpler non-causal statistical regularities could explain observed trends."
        ]
        self.log_action("critique_hypothesis", target_id=hypothesis.hypothesis_id)
        return {
            "hypothesis_id": hypothesis.hypothesis_id,
            "adversarial_score": 0.85,
            "counterarguments": counterarguments,
            "falsification_vector": "Test extreme noise perturbation exceeding 3 standard deviations."
        }

    def stress_test_finding(self, finding: Finding, evidence_list: List[Evidence]) -> Dict[str, Any]:
        """Perform adversarial stress-testing on an empirical finding."""
        weaknesses = []
        for ev in evidence_list:
            if ev.p_value > 0.03:
                weaknesses.append(f"Marginal p-value ({ev.p_value}) in evidence {ev.evidence_id}.")
            if abs(ev.effect_size) < 0.3:
                weaknesses.append(f"Low effect size ({ev.effect_size}) in evidence {ev.evidence_id}.")

        passed = len(weaknesses) == 0
        finding.adversarial_tested = True
        if not passed:
            finding.counterarguments.extend(weaknesses)

        self.log_action("stress_test_finding", target_id=finding.finding_id, passed=passed)
        return {
            "finding_id": finding.finding_id,
            "passed_adversarial_audit": passed,
            "weaknesses_identified": weaknesses
        }
