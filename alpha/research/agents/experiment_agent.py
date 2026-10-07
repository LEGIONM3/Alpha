"""Experiment Agent: Autonomous experimental scientist designing and executing empirical trials."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from alpha.research.agents.base import ScientificAgentBase
from alpha.research.entities import Hypothesis, Experiment, Observation, Evidence, EvidencePolarity, EvidenceStrength
from alpha.research.experiments.planner import ExperimentPlanner
from alpha.research.experiments.simulator import ExperimentSimulator
from alpha.research.experiments.validator import ExperimentValidator


class ExperimentAgent(ScientificAgentBase):
    """Specialized empirical discovery agent responsible for experimental trials."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id=agent_id, role_name="ExperimentAgent")
        self.planner = ExperimentPlanner()
        self.simulator = ExperimentSimulator()
        self.validator = ExperimentValidator()

    def run_experimental_campaign(
        self,
        hypothesis: Hypothesis,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """Execute complete cycle: Plan -> Validate -> Simulate -> Generate Evidence."""
        # 1. Design test
        exp = self.planner.design_test(hypothesis, sample_size=sample_size)
        exp.executed_by = self.agent_id

        # 2. Validate methodology
        val_report = self.validator.validate(exp)
        if not val_report.is_valid:
            self.log_action("validation_failed", target_id=exp.experiment_id)
            return {"experiment": exp, "validation": val_report, "evidence": None, "observations": []}

        # 3. Simulate execution
        sim_outcome = self.simulator.simulate(exp)

        # 4. Generate structured evidence
        polarity = EvidencePolarity.SUPPORT if sim_outcome.statistical_significance_achieved else EvidencePolarity.REFUTE
        strength = EvidenceStrength.STRONG if sim_outcome.p_value < 0.01 else EvidenceStrength.MODERATE

        evidence = Evidence(
            hypothesis_id=hypothesis.hypothesis_id,
            experiment_id=exp.experiment_id,
            observation_ids=[obs.observation_id for obs in sim_outcome.observations],
            polarity=polarity,
            strength=strength,
            confidence=round(min(0.98, 0.70 + 0.25 * sim_outcome.mean_effect_size), 3),
            p_value=sim_outcome.p_value,
            effect_size=sim_outcome.mean_effect_size,
            verifier_agent=self.agent_id
        )

        self.log_action("campaign_completed", target_id=exp.experiment_id, evidence_id=evidence.evidence_id)

        return {
            "experiment": exp,
            "validation": val_report,
            "simulation": sim_outcome,
            "evidence": evidence,
            "observations": sim_outcome.observations
        }
