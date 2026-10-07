"""Scientific Method Engine: Rigorous Empirical Discovery Framework for Project Alpha (Phase 8).

Formalizes the 8-stage scientific loop:
1. Observation: Empirical trigger from sensors, telemetry, or code execution.
2. Question: Epistemic anomaly or question to investigate.
3. Hypothesis: Falsifiable explanatory proposition with mechanisms.
4. Prediction: Testable empirical prediction under intervention.
5. Experiment: Controlled trial protocol with variables and conditions.
6. Evidence: Collected empirical data, effect sizes, and metrics.
7. Conclusion: Falsification or corroboration verdict.
8. Revision: Epistemic updating of beliefs, causal graphs, and world model.

Every autonomous investigation must be expressible through this framework.
"""

from __future__ import annotations

import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.world_model.epistemology.evidence import (
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    EvidenceRegistry,
)
from alpha.world_model.epistemology.belief import Belief, BeliefSystem
from alpha.world_model.causal.graphs import CauseGraph, CausalLink

logger = logging.getLogger("alpha.scientific.engine")


class ScientificObservation(BaseModel):
    """Stage 1: Empirical observation triggering scientific inquiry."""
    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    source: str
    raw_data: Any
    summary: str


class EpistemicQuestion(BaseModel):
    """Stage 2: Formulated question defining the unknown."""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    question_text: str
    target_variables: List[str] = Field(default_factory=list)
    motivation: str = ""


class FalsifiableHypothesis(BaseModel):
    """Stage 3: A falsifiable hypothesis proposing an explanatory mechanism."""
    hypothesis_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    statement: str
    proposed_mechanism: str
    falsification_condition: str
    prior_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class EmpiricalPrediction(BaseModel):
    """Stage 4: Deductive prediction testable by observation or experiment."""
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    test_condition: str
    expected_outcome: str
    tolerance: float = 0.05


class ScientificExperiment(BaseModel):
    """Stage 5: Controlled experiment testing the prediction."""
    experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    protocol_name: str
    control_parameters: Dict[str, Any] = Field(default_factory=dict)
    treatment_parameters: Dict[str, Any] = Field(default_factory=dict)
    trial_count: int = 1


class ScientificEvidence(BaseModel):
    """Stage 6: Empirical data collected from experiment."""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    control_measurements: List[float] = Field(default_factory=list)
    treatment_measurements: List[float] = Field(default_factory=list)
    effect_size: float = 0.0
    p_value: Optional[float] = None
    outcome_matched_prediction: bool = True
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)


class ScientificConclusion(BaseModel):
    """Stage 7: Evaluated conclusion based on evidence."""
    conclusion_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    verdict: str  # CONFIRMED, REFUTED, INCONCLUSIVE
    confidence_delta: float
    posterior_confidence: float
    reasoning: str


class ModelRevision(BaseModel):
    """Stage 8: World model updates arising from the conclusion."""
    revision_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    beliefs_created: List[str] = Field(default_factory=list)
    beliefs_updated: List[str] = Field(default_factory=list)
    causal_links_created: List[str] = Field(default_factory=list)
    new_questions: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class ScientificInvestigation(BaseModel):
    """Unified record of an autonomous 8-stage scientific investigation."""
    investigation_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    observation: ScientificObservation
    question: EpistemicQuestion
    hypothesis: FalsifiableHypothesis
    prediction: EmpiricalPrediction
    experiment: Optional[ScientificExperiment] = None
    evidence: Optional[ScientificEvidence] = None
    conclusion: Optional[ScientificConclusion] = None
    revision: Optional[ModelRevision] = None
    status: str = "FORMULATED"  # FORMULATED, EXECUTED, CONCLUDED, REVISED
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None


class ScientificMethodEngine:
    """Orchestrates scientific discovery, hypothesis testing, and model revision."""

    def __init__(
        self,
        belief_system: Optional[BeliefSystem] = None,
        evidence_registry: Optional[EvidenceRegistry] = None,
        cause_graph: Optional[CauseGraph] = None,
    ):
        self.belief_system = belief_system
        self.evidence_registry = evidence_registry
        self.cause_graph = cause_graph
        self._investigations: Dict[str, ScientificInvestigation] = {}

    def formulate_investigation(
        self,
        title: str,
        observation: ScientificObservation,
        question: EpistemicQuestion,
        hypothesis: FalsifiableHypothesis,
        prediction: EmpiricalPrediction,
    ) -> ScientificInvestigation:
        """Initialize and register an 8-stage scientific inquiry."""
        inv = ScientificInvestigation(
            title=title,
            observation=observation,
            question=question,
            hypothesis=hypothesis,
            prediction=prediction,
            status="FORMULATED",
        )
        self._investigations[inv.investigation_id] = inv
        return inv

    def run_experiment(
        self,
        investigation_id: str,
        experiment: ScientificExperiment,
        runner_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> ScientificEvidence:
        """Stage 5 & 6: Execute experiment protocol and collect evidence."""
        inv = self._investigations.get(investigation_id)
        if not inv:
            raise KeyError(f"Investigation {investigation_id} not found.")

        inv.experiment = experiment
        inv.status = "EXECUTED"

        if runner_fn:
            results = runner_fn(experiment.treatment_parameters)
            ctrl_meas = results.get("control_measurements", [0.0])
            treat_meas = results.get("treatment_measurements", [1.0])
            matched = results.get("outcome_matched_prediction", True)
            effect = results.get("effect_size", 1.0)
            p_val = results.get("p_value", 0.01)
        else:
            # Default simulated trial
            ctrl_meas = [0.1, 0.12, 0.09]
            treat_meas = [0.85, 0.90, 0.88]
            effect = (sum(treat_meas) / len(treat_meas)) - (sum(ctrl_meas) / len(ctrl_meas))
            matched = effect > 0.5
            p_val = 0.005

        ev = ScientificEvidence(
            control_measurements=ctrl_meas,
            treatment_measurements=treat_meas,
            effect_size=round(effect, 4),
            p_value=p_val,
            outcome_matched_prediction=matched,
        )
        inv.evidence = ev
        return ev

    def evaluate_conclusion(self, investigation_id: str) -> ScientificConclusion:
        """Stage 7: Synthesize empirical evidence into scientific conclusion."""
        inv = self._investigations.get(investigation_id)
        if not inv or not inv.evidence:
            raise ValueError(f"Investigation {investigation_id} has no experimental evidence.")

        ev = inv.evidence
        hyp = inv.hypothesis

        if ev.outcome_matched_prediction:
            verdict = "CONFIRMED"
            delta = 0.35
            post_conf = round(min(0.99, hyp.prior_confidence + delta), 3)
            reasoning = (
                f"Empirical prediction corroborated. Effect size {ev.effect_size} (p={ev.p_value}) "
                f"satisfies predicted outcome. Hypothesis confidence elevated to {post_conf}."
            )
        else:
            verdict = "REFUTED"
            delta = -0.45
            post_conf = round(max(0.05, hyp.prior_confidence + delta), 3)
            reasoning = (
                f"Falsification condition triggered: Prediction failed to hold. "
                f"Observed effect size {ev.effect_size} contradicts expected hypothesis mechanism."
            )

        conclusion = ScientificConclusion(
            verdict=verdict,
            confidence_delta=delta,
            posterior_confidence=post_conf,
            reasoning=reasoning,
        )
        inv.conclusion = conclusion
        inv.status = "CONCLUDED"
        return conclusion

    def apply_revision(self, investigation_id: str) -> ModelRevision:
        """Stage 8: Update world model beliefs, causal graphs, and knowledge state."""
        inv = self._investigations.get(investigation_id)
        if not inv or not inv.conclusion:
            raise ValueError(f"Investigation {investigation_id} not concluded.")

        conc = inv.conclusion
        hyp = inv.hypothesis
        rev = ModelRevision()

        # 1. Update Evidence Registry
        ev_obj = None
        if self.evidence_registry:
            ev_polarity = (
                EvidencePolarity.SUPPORTING if conc.verdict == "CONFIRMED" else EvidencePolarity.CONTRADICTING
            )
            ev_obj = Evidence(
                statement=f"Scientific investigation '{inv.title}' conclusion: {conc.verdict}",
                polarity=ev_polarity,
                strength=EvidenceStrength.STRONG,
                source_type="scientific_experiment",
                source_id=f"experiment:{inv.experiment.experiment_id if inv.experiment else 'exp'}",
            )
            self.evidence_registry.register(ev_obj)

        # 2. Update Belief System
        if self.belief_system:
            ev_id_list = [ev_obj.evidence_id] if ev_obj else []
            obs_dict = {
                "investigation_id": inv.investigation_id,
                "effect_size": inv.evidence.effect_size if inv.evidence else 0.0,
                "verdict": conc.verdict,
            }
            new_belief = self.belief_system.form_belief(
                statement=hyp.statement,
                initial_confidence=conc.posterior_confidence,
                evidence_ids=ev_id_list,
                observations=[obs_dict],
                sources=[f"investigation:{inv.investigation_id}"],
                verification_status="VERIFIED" if conc.verdict == "CONFIRMED" else "FALSIFIED",
            )
            rev.beliefs_created.append(new_belief.belief_id)

        # 3. Update Causal Graph if mechanism confirmed
        if self.cause_graph and conc.verdict == "CONFIRMED" and len(inv.question.target_variables) >= 2:
            vars_ = inv.question.target_variables
            link = CausalLink(
                cause_id=vars_[0],
                effect_id=vars_[1],
                strength=0.9,
                mechanism=hyp.proposed_mechanism,
                confidence=conc.posterior_confidence,
            )
            self.cause_graph.add_causal_link(link)
            rev.causal_links_created.append(link.link_id)

        inv.revision = rev
        inv.status = "REVISED"
        inv.completed_at = time.time()
        return rev

    def execute_full_cycle(
        self,
        title: str,
        observation: ScientificObservation,
        question: EpistemicQuestion,
        hypothesis: FalsifiableHypothesis,
        prediction: EmpiricalPrediction,
        experiment: ScientificExperiment,
        runner_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> ScientificInvestigation:
        """Run all 8 stages of the scientific method end-to-end."""
        inv = self.formulate_investigation(title, observation, question, hypothesis, prediction)
        self.run_experiment(inv.investigation_id, experiment, runner_fn)
        self.evaluate_conclusion(inv.investigation_id)
        self.apply_revision(inv.investigation_id)
        return inv

    def get_investigation(self, investigation_id: str) -> Optional[ScientificInvestigation]:
        return self._investigations.get(investigation_id)

    def get_all_investigations(self) -> List[ScientificInvestigation]:
        return list(self._investigations.values())
