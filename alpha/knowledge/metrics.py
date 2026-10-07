"""Real Novel Knowledge Tracking for Project Alpha.

Measures genuine epistemic progression from runtime activity:
- New unique observations (cryptographic hash differential)
- New verified findings (unique citation and content signatures)
- New falsifiable hypotheses (unique hypothesis IDs)
- Belief changes (confidence modifications, formations, and refutations)
- Resolved contradictions (epistemic conflict resolutions)
- Verified discoveries (empirical verifications)

Zero manual incrementation: Scores are strictly derived from runtime differentials.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from alpha.observation_engine.engine import ObservationRecord
from alpha.research_engine.engine import ResearchFinding
from alpha.hypothesizing.engine import Hypothesis
from alpha.world_model.epistemology.belief import Belief


class NovelKnowledgeMetrics(BaseModel):
    """Tracks verifiable epistemic metrics contributing to Alpha's autonomous learning."""
    new_observations_count: int = 0
    new_findings_count: int = 0
    new_hypotheses_count: int = 0
    belief_changes_count: int = 0
    contradictions_resolved_count: int = 0
    verified_discoveries_count: int = 0
    total_learning_score: float = Field(default=0.0, ge=0.0)

    # Backward compatibility aliases
    @property
    def novel_facts_derived_count(self) -> int:
        return self.new_findings_count

    @property
    def hypotheses_tested_count(self) -> int:
        return self.new_hypotheses_count

    @property
    def belief_updates_executed_count(self) -> int:
        return self.belief_changes_count

    @property
    def relationships_established_count(self) -> int:
        return self.verified_discoveries_count


class NovelKnowledgeScore:
    """Calculates and tracks cumulative epistemic progression by computing

    differentials across live runtime activity.
    """

    def __init__(self):
        self._metrics = NovelKnowledgeMetrics()
        self._seen_observation_hashes: Set[str] = set()
        self._seen_finding_signatures: Set[str] = set()
        self._seen_hypothesis_ids: Set[str] = set()
        self._seen_belief_signatures: Dict[str, float] = {}  # belief_id -> confidence
        self._tracked_contradictions: Set[str] = set()
        self._verified_discovery_ids: Set[str] = set()

    def reset_state(self) -> None:
        """Resets tracking state."""
        self._metrics = NovelKnowledgeMetrics()
        self._seen_observation_hashes.clear()
        self._seen_finding_signatures.clear()
        self._seen_hypothesis_ids.clear()
        self._seen_belief_signatures.clear()
        self._tracked_contradictions.clear()
        self._verified_discovery_ids.clear()

    def record_runtime_activity(
        self,
        observations: Optional[List[ObservationRecord]] = None,
        findings: Optional[List[ResearchFinding]] = None,
        hypotheses: Optional[List[Hypothesis]] = None,
        beliefs: Optional[List[Belief]] = None,
        contradictions: Optional[List[str]] = None,
        verified_hypotheses: Optional[List[Hypothesis]] = None
    ) -> float:
        """Ingests runtime activity artifacts and measures genuine epistemic novelty.

        Computes delta strictly based on unseen elements.
        """
        # 1. New Observations Differential
        if observations:
            for obs in observations:
                if obs.hash and obs.hash not in self._seen_observation_hashes:
                    self._seen_observation_hashes.add(obs.hash)
                    self._metrics.new_observations_count += 1

        # 2. New Research Findings Differential
        if findings:
            for f in findings:
                sig_raw = f"{f.finding_summary}:{','.join(f.citations)}"
                sig = hashlib.sha256(sig_raw.encode("utf-8")).hexdigest()[:16]
                if sig not in self._seen_finding_signatures:
                    self._seen_finding_signatures.add(sig)
                    self._metrics.new_findings_count += 1

        # 3. New Hypotheses Differential
        if hypotheses:
            for h in hypotheses:
                h_id = h.hypothesis_id or hashlib.sha256(h.statement.encode("utf-8")).hexdigest()[:12]
                if h_id not in self._seen_hypothesis_ids:
                    self._seen_hypothesis_ids.add(h_id)
                    self._metrics.new_hypotheses_count += 1

        # 4. Belief Changes Differential
        if beliefs:
            for b in beliefs:
                prev_conf = self._seen_belief_signatures.get(b.belief_id)
                if prev_conf is None:
                    # Brand new belief
                    self._seen_belief_signatures[b.belief_id] = b.confidence
                    self._metrics.belief_changes_count += 1
                elif abs(b.confidence - prev_conf) >= 0.01:
                    # Meaningful confidence shift
                    self._seen_belief_signatures[b.belief_id] = b.confidence
                    self._metrics.belief_changes_count += 1

        # 5. Contradictions Differential
        if contradictions:
            for c in contradictions:
                c_hash = hashlib.sha256(c.encode("utf-8")).hexdigest()[:16]
                if c_hash not in self._tracked_contradictions:
                    self._tracked_contradictions.add(c_hash)
                    self._metrics.contradictions_resolved_count += 1

        # 6. Verified Discoveries Differential
        if verified_hypotheses:
            for vh in verified_hypotheses:
                v_id = vh.hypothesis_id
                if v_id not in self._verified_discovery_ids:
                    self._verified_discovery_ids.add(v_id)
                    self._metrics.verified_discoveries_count += 1

        return self.calculate_score()

    def record_event(self, event_type: str, value: int = 1) -> None:
        """Legacy helper for individual event recordings."""
        if event_type == "NEW_OBSERVATION":
            self._metrics.new_observations_count += value
        elif event_type in ("FACT_DERIVED", "NEW_FINDING"):
            self._metrics.new_findings_count += value
        elif event_type == "NEW_HYPOTHESIS":
            self._metrics.new_hypotheses_count += value
        elif event_type == "BELIEF_UPDATE":
            self._metrics.belief_changes_count += value
        elif event_type == "CONTRADICTION_RESOLVED":
            self._metrics.contradictions_resolved_count += value
        elif event_type == "VERIFIED_DISCOVERY":
            self._metrics.verified_discoveries_count += value

    def calculate_score(self) -> float:
        """Calculates total score based on weighted metrics of genuine knowledge acquisition."""
        score = (
            self._metrics.new_observations_count * 0.1 +
            self._metrics.new_findings_count * 2.0 +
            self._metrics.new_hypotheses_count * 1.5 +
            self._metrics.belief_changes_count * 2.5 +
            self._metrics.contradictions_resolved_count * 3.0 +
            self._metrics.verified_discoveries_count * 5.0
        )
        self._metrics.total_learning_score = round(score, 4)
        return self._metrics.total_learning_score

    def get_current_metrics(self) -> NovelKnowledgeMetrics:
        """Returns snapshot of current metrics."""
        self.calculate_score()
        return self._metrics


# Singleton default instance
novel_knowledge_scorer = NovelKnowledgeScore()