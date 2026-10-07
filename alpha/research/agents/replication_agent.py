"""Replication Agent: Enforces mandatory scientific reproducibility.

Core Invariant: "Research without replication is forbidden."
Independently verifies experimental protocols and findings.
"""

from __future__ import annotations

import random
from typing import Dict, List, Any, Optional
from alpha.research.agents.base import ScientificAgentBase
from alpha.research.entities import Experiment, Finding, Replication
from alpha.research.experiments.simulator import ExperimentSimulator


class ReplicationAgent(ScientificAgentBase):
    """Independent replication auditor ensuring reproducibility across the civilization."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id=agent_id, role_name="ReplicationAgent")
        # Independent simulator with distinct seed
        self.simulator = ExperimentSimulator(random_seed=999)

    def replicate_study(
        self,
        experiment: Experiment,
        finding: Finding,
        tolerance_percent: float = 20.0
    ) -> Replication:
        """Independently execute replication trial under altered seeds and perturbations."""
        sim_outcome = self.simulator.simulate(experiment, trials=max(30, experiment.sample_size // 2), introduce_noise=0.08)

        # Check reproducibility
        original_expected = experiment.predicted_outcomes.get("expected_effect_size", 0.75)
        reproduced_effect = sim_outcome.mean_effect_size
        deviation = abs(reproduced_effect - original_expected) / max(0.01, original_expected) * 100.0

        is_reproduced = (deviation <= tolerance_percent) and sim_outcome.statistical_significance_achieved

        rep = Replication(
            original_experiment_id=experiment.experiment_id,
            finding_id=finding.finding_id,
            replicating_agent=self.agent_id,
            is_successful=is_reproduced,
            reproduced_metrics=sim_outcome.aggregated_metrics,
            deviation_percent=round(deviation, 2),
            notes=f"Replication {'CONFIRMED' if is_reproduced else 'FAILED'}: deviation={deviation:.1f}%, p={sim_outcome.p_value}"
        )

        if is_reproduced:
            finding.replicated = True
            finding.replication_count += 1
            finding.confidence = min(0.99, finding.confidence + 0.10)

        self.log_action(
            "replicate_study",
            target_id=finding.finding_id,
            is_successful=is_reproduced,
            deviation_percent=deviation
        )
        return rep
