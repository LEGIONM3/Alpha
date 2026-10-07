"""Self-Knowledge Engine: Epistemic Metacognition & Socratic Calibration for Project Alpha (Phase 8).

Explicitly partitions Alpha's epistemic horizon into four quadrants:
1. What I Know: Firmly grounded, empirically verified, high-confidence truths.
2. What I Think I Know: Active working hypotheses, provisional beliefs under evaluation.
3. What I Do Not Know: Acknowledged knowledge gaps and formulated open questions.
4. What I Cannot Yet Verify: Untestable propositions, missing sensors, undecidable bounds.

Persists epistemic metacognitive state to SELF_KNOWLEDGE_STATE.json.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.world_model.ontology.entities import LifecycleState
from alpha.world_model.epistemology.belief import Belief, BeliefSystem

logger = logging.getLogger("alpha.epistemology.self_knowledge")


class KnownTruth(BaseModel):
    belief_id: str
    statement: str
    confidence: float
    supporting_evidence_count: int
    source_documents: List[str] = Field(default_factory=list)
    last_verified: float


class WorkingHypothesis(BaseModel):
    belief_id: str
    statement: str
    confidence: float
    verification_status: str
    open_questions: List[str] = Field(default_factory=list)


class KnowledgeGap(BaseModel):
    gap_id: str
    domain: str
    question: str
    importance: float = 0.8
    suggested_investigation: str = ""


class UnverifiableProposition(BaseModel):
    proposition_id: str
    statement: str
    reason_unverifiable: str
    missing_sensor_or_capability: str


class SelfKnowledgeState(BaseModel):
    """Complete serialization model for SELF_KNOWLEDGE_STATE.json."""
    timestamp: float = Field(default_factory=time.time)
    last_updated_iso: str = ""
    epistemic_humility_index: float = 0.5  # [0.0, 1.0]
    calibration_accuracy: float = 0.9      # [0.0, 1.0]
    what_i_know: List[KnownTruth] = Field(default_factory=list)
    what_i_think_i_know: List[WorkingHypothesis] = Field(default_factory=list)
    what_i_do_not_know: List[KnowledgeGap] = Field(default_factory=list)
    what_i_cannot_yet_verify: List[UnverifiableProposition] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)
    summary: str = ""


class SelfKnowledgeEngine:
    """Computes, manages, and serializes Alpha's explicit boundaries of self-knowledge."""

    def __init__(
        self,
        belief_system: Optional[BeliefSystem] = None,
        workspace_root: Optional[Path] = None,
    ):
        self.belief_system = belief_system
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self._knowledge_gaps: Dict[str, KnowledgeGap] = {}
        self._unverifiable_propositions: Dict[str, UnverifiableProposition] = {}
        self._initialize_baseline_gaps_and_bounds()

    def _initialize_baseline_gaps_and_bounds(self) -> None:
        """Seed foundational known unknowns and unverifiable limits."""
        self.register_knowledge_gap(
            domain="runtime_scaling",
            question="What is the exact memory upper bound under 100 concurrent subagents?",
            importance=0.85,
            suggested_investigation="Run stress benchmark with varying agent pools up to 100.",
        )
        self.register_knowledge_gap(
            domain="causal_discovery",
            question="Can continuous sensory streams automatically infer hidden confounders without prior DAGs?",
            importance=0.90,
            suggested_investigation="Evaluate conditional independence algorithms on synthetic streaming data.",
        )
        self.register_unverifiable_proposition(
            statement="External foundation model weights are completely free of latent bias.",
            reason_unverifiable="Foundation model internal weights are proprietary/black-box or non-transparent.",
            missing_sensor_or_capability="Full white-box access to third-party model weights and training datasets.",
        )
        self.register_unverifiable_proposition(
            statement="Future operating system platform APIs will remain 100% backward compatible indefinitely.",
            reason_unverifiable="Future platform vendor roadmap changes are undetermined external events.",
            missing_sensor_or_capability="Predictive access to future upstream third-party API roadmaps.",
        )

    def register_knowledge_gap(
        self, domain: str, question: str, importance: float = 0.8, suggested_investigation: str = ""
    ) -> KnowledgeGap:
        gap = KnowledgeGap(
            gap_id=f"gap_{len(self._knowledge_gaps) + 1}",
            domain=domain,
            question=question,
            importance=importance,
            suggested_investigation=suggested_investigation,
        )
        self._knowledge_gaps[gap.gap_id] = gap
        return gap

    def register_unverifiable_proposition(
        self, statement: str, reason_unverifiable: str, missing_sensor_or_capability: str
    ) -> UnverifiableProposition:
        prop = UnverifiableProposition(
            proposition_id=f"unverifiable_{len(self._unverifiable_propositions) + 1}",
            statement=statement,
            reason_unverifiable=reason_unverifiable,
            missing_sensor_or_capability=missing_sensor_or_capability,
        )
        self._unverifiable_propositions[prop.proposition_id] = prop
        return prop

    def compile_state(self) -> SelfKnowledgeState:
        """Categorize all beliefs and compile the four quadrants of self-knowledge."""
        what_i_know: List[KnownTruth] = []
        what_i_think_i_know: List[WorkingHypothesis] = []

        if self.belief_system:
            for b in self.belief_system.get_all():
                if b.lifecycle_state != LifecycleState.ACTIVE or b.verification_status == "QUARANTINED":
                    continue

                # Quadrant 1: What I Know
                # High confidence (>=0.85) AND verified with empirical support
                if b.confidence_score >= 0.80 and (
                    b.verification_status == "VERIFIED"
                    or len(b.supporting_evidence) > 0
                    or len(b.source_documents) > 0
                ):
                    what_i_know.append(
                        KnownTruth(
                            belief_id=b.belief_id,
                            statement=b.statement,
                            confidence=b.confidence_score,
                            supporting_evidence_count=len(b.supporting_evidence),
                            source_documents=b.source_documents,
                            last_verified=b.last_verified_timestamp,
                        )
                    )
                else:
                    # Quadrant 2: What I Think I Know (Working hypotheses)
                    what_i_think_i_know.append(
                        WorkingHypothesis(
                            belief_id=b.belief_id,
                            statement=b.statement,
                            confidence=b.confidence_score,
                            verification_status=b.verification_status,
                            open_questions=[f"Requires empirical testing to advance from {b.confidence_score} confidence"],
                        )
                    )

        what_i_do_not_know = list(self._knowledge_gaps.values())
        what_i_cannot_yet_verify = list(self._unverifiable_propositions.values())

        # Epistemic Humility Index: ratio of acknowledged unknowns/unverifiables to total tracked
        total_tracked = len(what_i_know) + len(what_i_think_i_know) + len(what_i_do_not_know) + len(what_i_cannot_yet_verify)
        unknowns_count = len(what_i_do_not_know) + len(what_i_cannot_yet_verify)
        humility_index = round(unknowns_count / max(1, total_tracked), 3)

        # Calibration accuracy: high when high-confidence beliefs have evidence
        calibration = round(
            sum(k.confidence for k in what_i_know) / max(1, len(what_i_know)) if what_i_know else 0.85,
            3,
        )

        counts = {
            "what_i_know": len(what_i_know),
            "what_i_think_i_know": len(what_i_think_i_know),
            "what_i_do_not_know": len(what_i_do_not_know),
            "what_i_cannot_yet_verify": len(what_i_cannot_yet_verify),
            "total_tracked": total_tracked,
        }

        import datetime
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        summary = (
            f"Alpha Self-Knowledge: {len(what_i_know)} verified truths, "
            f"{len(what_i_think_i_know)} working hypotheses, {len(what_i_do_not_know)} acknowledged gaps, "
            f"{len(what_i_cannot_yet_verify)} unverifiable limits. Humility Index: {humility_index}."
        )

        return SelfKnowledgeState(
            last_updated_iso=now_iso,
            epistemic_humility_index=humility_index,
            calibration_accuracy=calibration,
            what_i_know=what_i_know,
            what_i_think_i_know=what_i_think_i_know,
            what_i_do_not_know=what_i_do_not_know,
            what_i_cannot_yet_verify=what_i_cannot_yet_verify,
            counts=counts,
            summary=summary,
        )

    def write_to_file(self, target_path: Optional[Path] = None) -> Path:
        """Write current self-knowledge state to SELF_KNOWLEDGE_STATE.json."""
        out_path = target_path or (self.workspace_root / "SELF_KNOWLEDGE_STATE.json")
        state = self.compile_state()
        out_path.write_text(json.dumps(state.model_dump(), indent=2), encoding="utf-8")
        logger.info("SELF_KNOWLEDGE_STATE.json updated: %s", out_path)
        return out_path
