"""Research Entity Types for Project Alpha: Phase 5 Research Civilization.

All scientific research artifacts are modeled as formal, typed graph entities:
- ResearchProblem
- ResearchQuestion
- Hypothesis
- Experiment
- Observation
- Evidence
- Finding
- Theory
- Prediction
- Publication
- Replication
- Refutation
"""

from __future__ import annotations

import time
import uuid
import hashlib
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ResearchStatus(str, Enum):
    PROPOSED = "PROPOSED"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATING = "VALIDATING"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    RETIRED = "RETIRED"
    SUPERSEDED = "SUPERSEDED"


class EvidencePolarity(str, Enum):
    SUPPORT = "SUPPORT"
    REFUTE = "REFUTE"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvidenceStrength(str, Enum):
    ANECDOTAL = "ANECDOTAL"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    DEFINITIVE = "DEFINITIVE"


STRENGTH_WEIGHTS = {
    EvidenceStrength.ANECDOTAL: 0.15,
    EvidenceStrength.WEAK: 0.35,
    EvidenceStrength.MODERATE: 0.65,
    EvidenceStrength.STRONG: 0.85,
    EvidenceStrength.DEFINITIVE: 1.0,
}


class ResearchProblem(BaseModel):
    """A fundamental unknown or challenge requiring structured scientific inquiry."""
    problem_id: str = Field(default_factory=lambda: f"prob_{uuid.uuid4().hex[:10]}")
    title: str
    description: str
    domain: str
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    epistemic_uncertainty: float = Field(default=0.8, ge=0.0, le=1.0)
    expected_impact: float = Field(default=0.7, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    resolved: bool = False


class ResearchQuestion(BaseModel):
    """A sharp, falsifiable research question generated from an unknown or problem."""
    question_id: str = Field(default_factory=lambda: f"q_{uuid.uuid4().hex[:10]}")
    problem_id: Optional[str] = None
    question_text: str
    domain: str
    target_variables: List[str] = Field(default_factory=list)
    falsifiability_criteria: str = ""
    epistemic_priority: float = Field(default=0.7, ge=0.0, le=1.0)
    investigability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    created_at: float = Field(default_factory=time.time)


class Hypothesis(BaseModel):
    """A testable, falsifiable scientific proposition proposing a causal or relational model."""
    hypothesis_id: str = Field(default_factory=lambda: f"hyp_{uuid.uuid4().hex[:10]}")
    question_id: Optional[str] = None
    statement: str
    rationale: str = Field(default="")
    domain: str
    cross_domains: List[str] = Field(default_factory=list)
    analogy_source: Optional[str] = None
    competing_hypotheses: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    status: ResearchStatus = ResearchStatus.PROPOSED
    novelty_score: float = Field(default=0.7, ge=0.0, le=1.0)
    proposer_agent: str = "HypothesisAgent"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class Experiment(BaseModel):
    """An empirical or simulated protocol designed to test one or more hypotheses."""
    experiment_id: str = Field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:10]}")
    hypothesis_id: str
    title: str
    protocol: Dict[str, Any]
    independent_variables: List[str] = Field(default_factory=list)
    dependent_variables: List[str] = Field(default_factory=list)
    control_conditions: Dict[str, Any] = Field(default_factory=dict)
    sample_size: int = 100
    estimated_cost: float = 10.0
    estimated_risk: float = 0.1
    predicted_outcomes: Dict[str, Any] = Field(default_factory=dict)
    status: str = "DESIGNED"  # DESIGNED, SIMULATED, VALIDATED, EXECUTED, ABORTED
    executed_by: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class Observation(BaseModel):
    """Empirical telemetry or simulated output collected during an experiment."""
    observation_id: str = Field(default_factory=lambda: f"obs_{uuid.uuid4().hex[:10]}")
    experiment_id: str
    trial_index: int = 0
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    anomalies_detected: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    observer: str = "ExperimentAgent"


class Evidence(BaseModel):
    """A verified, structured inference linking observations to a hypothesis."""
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:10]}")
    hypothesis_id: str
    experiment_id: str
    observation_ids: List[str] = Field(default_factory=list)
    polarity: EvidencePolarity = EvidencePolarity.SUPPORT
    strength: EvidenceStrength = EvidenceStrength.STRONG
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    p_value: float = Field(default=0.01, ge=0.0, le=1.0)
    effect_size: float = Field(default=0.75)
    provenance_hash: str = Field(default="")
    verifier_agent: Optional[str] = None
    created_at: float = Field(default_factory=time.time)

    def model_post_init(self, __context: Any) -> None:
        if not self.provenance_hash:
            payload = f"{self.hypothesis_id}:{self.experiment_id}:{self.polarity}:{self.confidence}:{self.p_value}"
            self.provenance_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]


class Finding(BaseModel):
    """An epistemically grounded conclusion derived from structured evidence."""
    finding_id: str = Field(default_factory=lambda: f"fnd_{uuid.uuid4().hex[:10]}")
    hypothesis_id: str
    claim: str
    evidence_ids: List[str] = Field(default_factory=list)
    replicated: bool = False
    replication_count: int = 0
    adversarial_tested: bool = False
    counterarguments: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    created_at: float = Field(default_factory=time.time)


class Prediction(BaseModel):
    """A concrete empirical prediction deduced from a theory or hypothesis."""
    prediction_id: str = Field(default_factory=lambda: f"pred_{uuid.uuid4().hex[:10]}")
    source_entity_id: str
    forecast_statement: str
    expected_value: Any
    tolerance: float = 0.05
    target_horizon_seconds: float = 3600.0
    evaluated: bool = False
    accuracy_score: Optional[float] = None
    created_at: float = Field(default_factory=time.time)


class Theory(BaseModel):
    """An overarching explanatory and causal framework uniting multiple findings."""
    theory_id: str = Field(default_factory=lambda: f"thy_{uuid.uuid4().hex[:10]}")
    name: str
    description: str
    domain: str
    cross_domains: List[str] = Field(default_factory=list)
    principles: List[str] = Field(default_factory=list)
    causal_mechanisms: Dict[str, str] = Field(default_factory=dict)
    finding_ids: List[str] = Field(default_factory=list)
    explanatory_power: float = Field(default=0.8, ge=0.0, le=1.0)
    parsimony_score: float = Field(default=0.85, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    status: ResearchStatus = ResearchStatus.SUPPORTED
    retirement_reason: Optional[str] = None
    version: int = 1
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class Replication(BaseModel):
    """An independent replication study attempting to reproduce an empirical finding."""
    replication_id: str = Field(default_factory=lambda: f"rep_{uuid.uuid4().hex[:10]}")
    original_experiment_id: str
    finding_id: str
    replicating_agent: str
    is_successful: bool
    reproduced_metrics: Dict[str, float] = Field(default_factory=dict)
    deviation_percent: float = 0.0
    notes: str = ""
    timestamp: float = Field(default_factory=time.time)


class Refutation(BaseModel):
    """A formal scientific refutation challenging a hypothesis, finding, or theory."""
    refutation_id: str = Field(default_factory=lambda: f"ref_{uuid.uuid4().hex[:10]}")
    target_entity_id: str
    target_type: str  # Hypothesis, Finding, Theory
    author_agent: str
    counter_evidence_ids: List[str] = Field(default_factory=list)
    argumentation: str
    falsification_metric: float = Field(default=0.9, ge=0.0, le=1.0)
    timestamp: float = Field(default_factory=time.time)


class Publication(BaseModel):
    """A fully certified and peer-reviewed scientific knowledge artifact."""
    publication_id: str = Field(default_factory=lambda: f"pub_{uuid.uuid4().hex[:10]}")
    title: str
    abstract: str
    domain: str
    author_agent: str
    theory_ids: List[str] = Field(default_factory=list)
    finding_ids: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    novelty_score: float = Field(default=0.8, ge=0.0, le=1.0)
    impact_score: float = Field(default=0.85, ge=0.0, le=1.0)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    # 5-Layer Mandatory Pass
    passed_truth_layer: bool = False
    passed_governance_layer: bool = False
    passed_identity_layer: bool = False
    passed_drift_detection_layer: bool = False
    passed_replication_layer: bool = False
    governance_signature: Optional[str] = None
    created_at: float = Field(default_factory=time.time)

    def is_fully_verified(self) -> bool:
        """Mandatory Rule: all 5 governance layers must approve."""
        return (
            self.passed_truth_layer
            and self.passed_governance_layer
            and self.passed_identity_layer
            and self.passed_drift_detection_layer
            and self.passed_replication_layer
        )
