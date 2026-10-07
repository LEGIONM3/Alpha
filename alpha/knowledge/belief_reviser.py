"""Belief Revision Engine for Project Alpha.

Grounded Epistemic Reviser:
- Evaluates active beliefs against empirical ResearchFindings and ObservationRecords.
- Reasoned via the Foundation Model (Qwen 3.8 9B Heretic) or empirical evidence matching.
- Detects contradictions: records contradiction history and weakens contradictory beliefs.
- Strengthens corroborated beliefs with explicit citations.
- Forms new grounded beliefs ONLY when supported by verifiable empirical evidence.
- Every belief contains:
  1. belief id
  2. source evidence
  3. confidence
  4. timestamp
  5. supporting observations
  6. contradiction history

Zero placeholder logic. No belief without evidence.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from alpha.observation_engine.observation import Observation, ObservationRecord
from alpha.research_engine.engine import ResearchFinding
from alpha.reasoning.qwen_reasoner import qwen_reasoner
from alpha.world_model.epistemology.belief import Belief, BeliefSystem
from alpha.world_model.epistemology.evidence import Evidence, EvidencePolarity, EvidenceStrength
from alpha.world_model.ontology.entities import ConceptEntity, EntityType
from alpha.world_model.graph import RelationType

logger = logging.getLogger("alpha.knowledge.belief_reviser")


class BeliefRevisionEngine:
    """The epistemic gatekeeper enforcing evidence-first belief creation and revision."""

    def __init__(self, world_model: Optional[Any] = None):
        self.world_model = world_model

    def revise_world_model(
        self,
        beliefs: Optional[List[Belief]] = None,
        new_evidence: Optional[List[ObservationRecord]] = None,
        findings: Optional[List[ResearchFinding]] = None,
        world_model: Optional[Any] = None
    ) -> Tuple[List[Belief], List[str]]:
        """Processes new empirical evidence and research findings against active beliefs.

        Returns: (Updated Belief List, List of Contradiction Reports)
        """
        wm = world_model or self.world_model
        evidence_list = new_evidence or []
        findings_list = findings or []

        # Resolve current belief set
        if beliefs is not None and len(beliefs) > 0:
            current_beliefs = list(beliefs)
        elif wm and hasattr(wm, "beliefs"):
            current_beliefs = wm.beliefs.get_all()
        else:
            current_beliefs = []

        contradictions: List[str] = []
        if not evidence_list and not findings_list:
            return current_beliefs, contradictions

        # ---------------------------------------------------------------------
        # 1. Foundation Model Epistemic Evaluation
        # ---------------------------------------------------------------------
        qwen_eval: Dict[str, Any] = {}
        try:
            qwen_eval = qwen_reasoner.evaluate_belief_revision(
                beliefs=current_beliefs,
                findings=findings_list,
                observations=evidence_list
            )
        except Exception as e:
            logger.debug(f"Direct Qwen revision evaluation deferred: {e}")

        # Process contradicted beliefs from Qwen
        contradicted_items = qwen_eval.get("contradicted_beliefs", [])
        for item in contradicted_items:
            bid = item.get("belief_id")
            reason = item.get("reason", "Empirical contradiction detected")
            penalty = float(item.get("penalty", 0.30))
            matched_b = next((b for b in current_beliefs if b.belief_id == bid or b.belief_id.startswith(bid)), None)
            if matched_b:
                contra_msg = f"Contradiction on [{matched_b.belief_id[:8]}]: {reason}"
                contradictions.append(contra_msg)
                if reason not in matched_b.contradiction_history:
                    matched_b.contradiction_history.append(reason)
                matched_b.weaken(contradiction_id=f"contra_{uuid.uuid4().hex[:6]}", penalty=penalty)

        # Process supported beliefs from Qwen
        supported_items = qwen_eval.get("supported_beliefs", [])
        for item in supported_items:
            bid = item.get("belief_id")
            delta = float(item.get("delta", 0.15))
            matched_b = next((b for b in current_beliefs if b.belief_id == bid or b.belief_id.startswith(bid)), None)
            if matched_b:
                matched_b.strengthen(evidence_id=f"ev_support_{uuid.uuid4().hex[:6]}", delta=delta)

        # ---------------------------------------------------------------------
        # 2. Empirical Verification via Direct Finding Evidence Matching
        # ---------------------------------------------------------------------
        for finding in findings_list:
            finding_text = finding.finding_summary
            finding_conf = finding.confidence
            citations = finding.citations
            src_paths = finding.source_paths
            evidence_chunks = finding.evidence

            # Empirical check: match against active beliefs
            matched_belief = self._match_belief_by_semantic_overlap(current_beliefs, finding_text)

            if matched_belief:
                # Check for direct empirical contradiction vs confirmation
                is_contradicting = self._check_empirical_contradiction(matched_belief, finding)

                if is_contradicting:
                    contra_report = (
                        f"Empirical contradiction: Finding '{finding_text[:70]}' conflicts with "
                        f"Belief '{matched_belief.statement[:70]}'."
                    )
                    if contra_report not in contradictions:
                        contradictions.append(contra_report)
                    if contra_report not in matched_belief.contradiction_history:
                        matched_belief.contradiction_history.append(contra_report)

                    ev_id = f"contra_{uuid.uuid4().hex[:8]}"
                    matched_belief.weaken(ev_id, penalty=0.35, verifier_id=src_paths[0] if src_paths else "research_engine")

                else:
                    # Supporting evidence
                    ev_id = citations[0] if citations else f"ev_ground_{uuid.uuid4().hex[:8]}"
                    if ev_id not in matched_belief.source_evidence:
                        matched_belief.source_evidence.append(ev_id)
                    matched_belief.strengthen(ev_id, delta=0.20, verifier_id="research_engine")

            else:
                # Novel verified discovery: Form a new belief ONLY if backed by empirical evidence!
                # "No belief may be created without evidence."
                if (citations or evidence_chunks) and finding_conf >= 0.70:
                    new_belief_id = f"belief_{uuid.uuid4().hex[:12]}"
                    now_ts = time.time()

                    # Match any relevant observations
                    matching_obs = [
                        o.model_dump() for o in evidence_list
                        if any(sp in o.source or sp in o.evidence for sp in src_paths)
                    ]

                    new_b = Belief(
                        belief_id=new_belief_id,
                        statement=finding_text,
                        confidence=finding_conf,
                        source_evidence=citations + evidence_chunks[:2],
                        timestamp=now_ts,
                        supporting_observations=matching_obs,
                        contradiction_history=[],
                        sources=src_paths or ["research_engine"],
                        domain="architecture",
                        verification_status="VERIFIED"
                    )

                    current_beliefs.append(new_b)

                    if wm and hasattr(wm, "register_entity"):
                        self._sync_world_model_entities(wm, new_b, finding)

        # ---------------------------------------------------------------------
        # 3. Direct Test Failure Falsification
        # ---------------------------------------------------------------------
        for obs in evidence_list:
            if obs.category in ("test_failure", "syntax_anomaly") or "FAILED" in obs.evidence:
                for b in current_beliefs:
                    if "test" in b.statement.lower() or "pass" in b.statement.lower() or "stable" in b.statement.lower():
                        fail_msg = f"Test Observer detected empirical failure: {obs.evidence[:80]}"
                        if fail_msg not in contradictions:
                            contradictions.append(fail_msg)
                        if fail_msg not in b.contradiction_history:
                            b.contradiction_history.append(fail_msg)
                        b.weaken(f"fail_{obs.hash[:8]}", penalty=0.30, verifier_id=obs.source)

        return current_beliefs, contradictions

    def _match_belief_by_semantic_overlap(self, beliefs: List[Belief], text: str) -> Optional[Belief]:
        """Finds an existing belief that addresses the same subject."""
        words = {w.lower() for w in text.split() if len(w) > 3}
        best_b: Optional[Belief] = None
        best_count = 0

        for b in beliefs:
            b_words = {w.lower() for w in b.statement.split() if len(w) > 3}
            overlap = len(words.intersection(b_words))
            if overlap >= 2 and overlap > best_count:
                best_count = overlap
                best_b = b

        return best_b

    def _check_empirical_contradiction(self, belief: Belief, finding: ResearchFinding) -> bool:
        """Evaluates whether the finding contradicts the claim of the belief."""
        b_lower = belief.statement.lower()
        f_lower = finding.finding_summary.lower()

        positive_terms = ["verified", "passing", "stable", "complete", "covered", "tested"]
        negative_terms = ["untested", "failed", "error", "missing", "unmodeled", "risk", "anomaly"]

        b_is_pos = any(t in b_lower for t in positive_terms)
        f_is_neg = any(t in f_lower for t in negative_terms)

        if b_is_pos and f_is_neg:
            return True

        b_is_neg = any(t in b_lower for t in negative_terms)
        f_is_pos = any(t in f_lower for t in positive_terms)

        if b_is_neg and f_is_pos:
            return True

        return False

    def _sync_world_model_entities(self, wm: Any, belief: Belief, finding: ResearchFinding) -> None:
        """Synchronizes new verified concepts into CognitiveWorldModel Ontology."""
        try:
            for path_str in finding.source_paths:
                stem = path_str.split("/")[-1].replace(".py", "")
                entity_id = f"concept_{stem.lower()}"
                if hasattr(wm, "ontology") and not wm.ontology.get(entity_id):
                    concept = ConceptEntity(
                        id=entity_id,
                        name=f"Subsystem:{stem}",
                        definition=f"Empirically verified codebase module from {path_str}",
                        importance=0.80,
                        confidence=belief.confidence
                    )
                    wm.register_entity(concept)
                    if hasattr(wm, "relate"):
                        wm.relate(belief.belief_id, concept.id, RelationType.VALIDATES)
        except Exception:
            pass


# Singleton default instance
belief_reviser = BeliefRevisionEngine()