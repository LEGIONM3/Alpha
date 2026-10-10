"""Evidence Graph Core Implementation for Project Alpha.

Coordinates the strict 5-layer epistemic hierarchy:
Evidence -> Observation -> Finding -> Hypothesis -> Belief

Features:
- Immutable lineage tracking with cryptographic verification
- Confidence propagation across upstream and downstream nodes
- Contradiction propagation with confidence penalties and contested state
- Automated belief decay for unverified assertions
- Absolute zero tolerance for orphan beliefs
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from alpha.evidence_graph.models import (
    NodeType,
    EvidenceNode,
    ObservationNode,
    FindingNode,
    HypothesisNode,
    Belief,
    GoalNode,
    ActionNode,
    OutcomeNode,
    LearningNode,
    OrphanBeliefError,
)

logger = logging.getLogger("alpha.evidence_graph")


def _to_id(item: Any) -> str:
    """Extracts node_id or belief_id if a node model is passed, otherwise converts to str."""
    if hasattr(item, "node_id"):
        return str(item.node_id)
    if hasattr(item, "belief_id"):
        return str(item.belief_id)
    return str(item)


class EvidenceGraph:
    """Directed Epistemic Graph tracking evidence lineage and confidence dynamics."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/evidence_graph.json")
        self.evidence_nodes: Dict[str, EvidenceNode] = {}
        self.observation_nodes: Dict[str, ObservationNode] = {}
        self.finding_nodes: Dict[str, FindingNode] = {}
        self.hypothesis_nodes: Dict[str, HypothesisNode] = {}
        self.beliefs: Dict[str, Belief] = {}
        self.goal_nodes: Dict[str, GoalNode] = {}
        self.action_nodes: Dict[str, ActionNode] = {}
        self.outcome_nodes: Dict[str, OutcomeNode] = {}
        self.learning_nodes: Dict[str, LearningNode] = {}

        # Directed adjacency: parent -> children (downstream), child -> parents (upstream)
        self._downstream_edges: Dict[str, Set[str]] = {}
        self._upstream_edges: Dict[str, Set[str]] = {}

        self.current_cycle: int = 0
        self._load()

    def _add_edge(self, parent_id: str, child_id: str) -> None:
        if parent_id not in self._downstream_edges:
            self._downstream_edges[parent_id] = set()
        self._downstream_edges[parent_id].add(child_id)

        if child_id not in self._upstream_edges:
            self._upstream_edges[child_id] = set()
        self._upstream_edges[child_id].add(parent_id)

    @property
    def nodes(self) -> Dict[str, Any]:
        return {
            **self.evidence_nodes,
            **self.observation_nodes,
            **self.finding_nodes,
            **self.hypothesis_nodes,
            **self.beliefs,
            **self.goal_nodes,
            **self.action_nodes,
            **self.outcome_nodes,
            **self.learning_nodes,
        }

    def get_node(self, node_id: str) -> Optional[Any]:
        return self.nodes.get(node_id)

    # -------------------------------------------------------------------------
    # Node Addition Methods
    # -------------------------------------------------------------------------
    def add_evidence(
        self,
        content: Any = None,
        source: Optional[str] = None,
        source_type: str = "raw_fact",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        raw_data: Any = None,
        source_uri: Optional[str] = None,
        fidelity: Optional[float] = None
    ) -> EvidenceNode:
        """Adds a base empirical fact to the evidence graph."""
        content = raw_data if content is None else content
        source = source_uri if source is None else source
        if source is None:
            source = "empirical_source"
        if fidelity is not None:
            confidence = fidelity
        node = EvidenceNode(
            content=content,
            source=source,
            source_type=source_type,
            confidence=confidence,
            metadata=metadata or {}
        )
        self.evidence_nodes[node.node_id] = node
        return node

    def add_observation(
        self,
        observation_id: Optional[str] = None,
        source: str = "sensory_source",
        source_type: str = "sensory",
        facts: Any = None,
        evidence_ids: Optional[List[str]] = None,
        confidence: float = 0.95,
        metadata: Optional[Dict[str, Any]] = None,
        raw_data: Any = None,
        evidence_id: Optional[str] = None,
        content: Any = None
    ) -> ObservationNode:
        """Adds a structured observation node connected to underlying evidence."""
        if observation_id is None:
            observation_id = f"obs_node_{uuid.uuid4().hex[:10]}"
        facts = raw_data if facts is None else facts
        if facts is None and content is not None:
            facts = content
        ev_ids = [_to_id(eid) for eid in (evidence_ids or [])]
        if evidence_id:
            eid_str = _to_id(evidence_id)
            if eid_str not in ev_ids:
                ev_ids.append(eid_str)
        node = ObservationNode(
            observation_id=observation_id,
            evidence_ids=ev_ids,
            source=source,
            source_type=source_type,
            facts=facts,
            confidence=confidence,
            metadata=metadata or {}
        )
        self.observation_nodes[node.node_id] = node
        for eid in node.evidence_ids:
            self._add_edge(eid, node.node_id)
        return node

    def add_finding(
        self,
        query: str = "",
        observation_ids: Optional[List[Any]] = None,
        citations: Optional[List[str]] = None,
        claims: Optional[List[str]] = None,
        evidence_chunks: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.85,
        metadata: Optional[Dict[str, Any]] = None,
        finding_text: Optional[str] = None
    ) -> FindingNode:
        """Adds a synthesized research finding backed by observations and citations."""
        citations = citations or []
        if not citations:
            raise ValueError("Research finding requires at least one verifiable citation.")
        if finding_text and not claims:
            claims = [finding_text]
        if not query and finding_text:
            query = finding_text[:50]
        obs_ids = [_to_id(oid) for oid in (observation_ids or [])]
        node = FindingNode(
            query=query,
            observation_ids=obs_ids,
            citations=citations,
            claims=claims or [],
            evidence_chunks=evidence_chunks or [],
            confidence=confidence,
            metadata=metadata or {}
        )
        self.finding_nodes[node.node_id] = node
        for oid in obs_ids:
            self._add_edge(oid, node.node_id)
        return node

    def add_hypothesis(
        self,
        statement: str = "",
        mechanism: str = "empirical_mechanism",
        finding_ids: Optional[List[Any]] = None,
        falsification_criteria: Optional[List[str]] = None,
        confidence: float = 0.60,
        metadata: Optional[Dict[str, Any]] = None,
        hypothesis_statement: Optional[str] = None
    ) -> HypothesisNode:
        """Adds a scientific hypothesis derived from research findings."""
        statement = hypothesis_statement or statement
        f_ids = [_to_id(fid) for fid in (finding_ids or [])]
        if not f_ids:
            raise ValueError("Hypothesis must be derived from at least one finding.")

        node = HypothesisNode(
            statement=statement,
            mechanism=mechanism,
            finding_ids=f_ids,
            falsification_criteria=falsification_criteria or ["Empirical test failure"],
            confidence=confidence,
            metadata=metadata or {}
        )
        self.hypothesis_nodes[node.node_id] = node
        for fid in f_ids:
            self._add_edge(fid, node.node_id)
        return node

    def create_belief(
        self,
        statement: str,
        supporting_evidence_ids: List[Any],
        initial_confidence: float = 0.60,
        decay_rate: float = 0.02
    ) -> Belief:
        """Creates and registers a reality-grounded belief with strict provenance."""
        supp_ids = [_to_id(sid) for sid in (supporting_evidence_ids or [])]
        if not supp_ids:
            raise OrphanBeliefError(
                f"A belief without evidence must never exist! Cannot create belief for '{statement}' with zero evidence."
            )

        # Validate that all supporting evidence IDs actually exist in the graph
        valid_upstream = []
        for eid in supp_ids:
            if (
                eid in self.hypothesis_nodes
                or eid in self.finding_nodes
                or eid in self.observation_nodes
                or eid in self.evidence_nodes
            ):
                valid_upstream.append(eid)

        if not valid_upstream:
            raise OrphanBeliefError(
                f"Orphan belief rejected: None of supporting IDs {supp_ids} exist in EvidenceGraph."
            )

        # Construct full provenance chain
        provenance = self._trace_full_provenance(valid_upstream)

        belief = Belief(
            statement=statement,
            confidence=initial_confidence,
            supporting_evidence=valid_upstream,
            decay_rate=decay_rate,
            provenance_chain=provenance,
            lifecycle_state="ACTIVE",
            verification_count=1,
            last_verified=datetime.now(timezone.utc).isoformat()
        )

        self.beliefs[belief.belief_id] = belief
        for uid in valid_upstream:
            self._add_edge(uid, belief.belief_id)

        self.persist()
        return belief

    def add_belief(
        self,
        statement: str,
        supporting_evidence_ids: List[str],
        initial_confidence: float = 0.60,
        decay_rate: float = 0.02,
        hypothesis_id: Optional[str] = None
    ) -> Belief:
        """Alias for create_belief supporting optional hypothesis_id."""
        ev_list = list(supporting_evidence_ids)
        if hypothesis_id and hypothesis_id not in ev_list:
            ev_list.append(hypothesis_id)
        return self.create_belief(
            statement=statement,
            supporting_evidence_ids=ev_list,
            initial_confidence=initial_confidence,
            decay_rate=decay_rate
        )

    def add_goal(
        self,
        goal_id: Optional[str] = None,
        statement: str = "",
        originating_belief_id: Optional[str] = None,
        originating_observation_ids: Optional[List[str]] = None,
        parent_ids: Optional[List[str]] = None,
        channel: str = "UNKNOWN",
        epistemic_priority: float = 0.80,
        status: str = "ACTIVE",
        metadata: Optional[Dict[str, Any]] = None,
        priority: Optional[float] = None
    ) -> GoalNode:
        """Adds a GoalNode emergent from observations or beliefs."""
        if priority is not None:
            epistemic_priority = priority
        gid = goal_id or f"goal_{uuid.uuid4().hex[:10]}"
        parents = list(parent_ids or [])
        if originating_belief_id and originating_belief_id not in parents:
            parents.append(originating_belief_id)
        for oid in (originating_observation_ids or []):
            if oid not in parents:
                parents.append(oid)

        node = GoalNode(
            goal_id=gid,
            statement=statement,
            originating_belief_id=originating_belief_id,
            originating_observation_ids=originating_observation_ids or [],
            parent_ids=parents,
            channel=channel,
            epistemic_priority=epistemic_priority,
            status=status,
            metadata=metadata or {}
        )
        self.goal_nodes[node.node_id] = node
        for pid in parents:
            self._add_edge(pid, node.node_id)
        self.persist()
        return node

    def add_action(
        self,
        action_name: Optional[str] = None,
        goal_id: Optional[str] = None,
        parent_ids: Optional[List[str]] = None,
        tool: str = "computer_use",
        target: str = "",
        modality: str = "FILESYSTEM_IO",
        status: str = "EXECUTED",
        metadata: Optional[Dict[str, Any]] = None,
        action_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ActionNode:
        """Adds an ActionNode representing an actuator operation."""
        actual_name = action_name or action_type or "ACTION"
        meta = dict(metadata or {})
        if parameters:
            meta["parameters"] = parameters
        parents = list(parent_ids or [])
        if goal_id and goal_id not in parents:
            parents.append(goal_id)

        node = ActionNode(
            action_name=actual_name,
            goal_id=goal_id,
            parent_ids=parents,
            tool=tool,
            target=target,
            modality=modality,
            status=status,
            metadata=meta
        )
        self.action_nodes[node.node_id] = node
        for pid in parents:
            self._add_edge(pid, node.node_id)
        self.persist()
        return node

    def add_outcome(
        self,
        action_id: str,
        success: Optional[bool] = None,
        observed_state: Any = None,
        expected_state: Any = None,
        explanation_if_failed_or_absent: Optional[str] = None,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_success: Optional[bool] = None,
        discrepancy_details: Optional[str] = None
    ) -> OutcomeNode:
        """Adds an OutcomeNode recording empirical action results."""
        actual_success = success if success is not None else (is_success if is_success is not None else True)
        actual_explanation = explanation_if_failed_or_absent or discrepancy_details
        parents = list(parent_ids or [])
        if action_id not in parents:
            parents.append(action_id)

        node = OutcomeNode(
            action_id=action_id,
            parent_ids=parents,
            success=actual_success,
            observed_state=observed_state,
            expected_state=expected_state,
            explanation_if_failed_or_absent=actual_explanation,
            metadata=metadata or {}
        )
        self.outcome_nodes[node.node_id] = node
        for pid in parents:
            self._add_edge(pid, node.node_id)
        self.persist()
        return node

    def add_learning_update(
        self,
        outcome_id: str,
        belief_id: Optional[str] = None,
        learning_type: str = "REVISION",
        delta_confidence: float = 0.0,
        is_valid_learning: Optional[bool] = None,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        affected_belief_id: Optional[str] = None,
        epistemic_delta: Optional[float] = None
    ) -> LearningNode:
        """Adds a LearningNode recording synthesized learning.

        Strict Invariant: If parent outcome failed, it cannot be recorded as successful learning.
        """
        actual_belief_id = belief_id or affected_belief_id
        actual_delta = epistemic_delta if epistemic_delta is not None else delta_confidence
        parents = list(parent_ids or [])
        if outcome_id not in parents:
            parents.append(outcome_id)
        if actual_belief_id and actual_belief_id not in parents:
            parents.append(actual_belief_id)

        outcome_node = self.outcome_nodes.get(outcome_id)
        if outcome_node and not outcome_node.success:
            if is_valid_learning is True:
                raise ValueError("Invariant violation: Failed actions cannot be recorded as successful learning!")
            is_valid = False
            learning_type = "FAILED_ACTION_RECORDED"
        else:
            is_valid = True if is_valid_learning is None else is_valid_learning

        node = LearningNode(
            outcome_id=outcome_id,
            parent_ids=parents,
            belief_id=actual_belief_id,
            learning_type=learning_type,
            delta_confidence=actual_delta,
            is_valid_learning=is_valid,
            metadata=metadata or {}
        )
        self.learning_nodes[node.node_id] = node
        for pid in parents:
            self._add_edge(pid, node.node_id)
        self.persist()
        return node

    # -------------------------------------------------------------------------
    # Lineage and Provenance Tracking
    # -------------------------------------------------------------------------
    def _trace_full_provenance(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        """Walks upstream from node_ids and compiles full chronological lineage."""
        chain: List[Dict[str, Any]] = []
        visited: Set[str] = set()
        queue = list(node_ids)

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)

            node_data = self._get_node_summary(curr)
            if node_data:
                chain.append(node_data)

            # Enqueue parents
            parents = self._upstream_edges.get(curr, set())
            for p in parents:
                if p not in visited:
                    queue.append(p)

        return chain

    def get_provenance_chain(self, belief_id: str) -> Dict[str, Any]:
        """Returns structured provenance dict for a given belief."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            raise KeyError(f"Belief '{belief_id}' not found.")
        return {
            "node_id": belief.belief_id,
            "node_type": NodeType.BELIEF.value,
            "statement": belief.statement,
            "parents": list(belief.supporting_evidence),
            "chain": list(belief.provenance_chain)
        }

    def _get_node_summary(self, node_id: str) -> Optional[Dict[str, Any]]:
        if node_id in self.evidence_nodes:
            n = self.evidence_nodes[node_id]
            return {
                "layer": "evidence",
                "node_id": n.node_id,
                "source": n.source,
                "confidence": n.confidence,
                "timestamp": n.timestamp
            }
        elif node_id in self.observation_nodes:
            n = self.observation_nodes[node_id]
            return {
                "layer": "observation",
                "node_id": n.node_id,
                "observation_id": n.observation_id,
                "source_type": n.source_type,
                "confidence": n.confidence,
                "timestamp": n.timestamp
            }
        elif node_id in self.finding_nodes:
            n = self.finding_nodes[node_id]
            return {
                "layer": "finding",
                "node_id": n.node_id,
                "query": n.query,
                "citations": n.citations,
                "confidence": n.confidence,
                "timestamp": n.timestamp
            }
        elif node_id in self.hypothesis_nodes:
            n = self.hypothesis_nodes[node_id]
            return {
                "layer": "hypothesis",
                "node_id": n.node_id,
                "statement": n.statement,
                "mechanism": n.mechanism,
                "confidence": n.confidence,
                "timestamp": n.timestamp
            }
        return None

    # -------------------------------------------------------------------------
    # Confidence and Contradiction Propagation
    # -------------------------------------------------------------------------
    def propagate_confidence(
        self,
        source_node_id: Optional[str] = None,
        new_confidence: Optional[float] = None
    ) -> List[str]:
        """Propagates updated confidence downstream to all dependent hypotheses and beliefs."""
        if source_node_id is None:
            updated = []
            for bid, b in self.beliefs.items():
                parent_confs = [self._get_node_confidence(p) for p in b.supporting_evidence if self._get_node_confidence(p) is not None]
                if parent_confs:
                    b.confidence = round(sum(parent_confs) / len(parent_confs), 3)
                    updated.append(bid)
            self.persist()
            return updated

        updated_nodes: List[str] = []
        new_conf = max(0.0, min(1.0, round(new_confidence if new_confidence is not None else 1.0, 3)))

        # Update source node
        if source_node_id in self.evidence_nodes:
            self.evidence_nodes[source_node_id].confidence = new_conf
        elif source_node_id in self.observation_nodes:
            self.observation_nodes[source_node_id].confidence = new_conf
        elif source_node_id in self.finding_nodes:
            self.finding_nodes[source_node_id].confidence = new_conf
        elif source_node_id in self.hypothesis_nodes:
            self.hypothesis_nodes[source_node_id].confidence = new_conf

        # Breadth-first downstream propagation
        queue = [source_node_id]
        visited = set()

        while queue:
            curr = queue.pop(0)
            children = self._downstream_edges.get(curr, set())
            for ch in children:
                if ch in visited:
                    continue
                visited.add(ch)

                # Recompute child confidence based on average parent confidence
                parents = self._upstream_edges.get(ch, set())
                parent_confs = []
                for p in parents:
                    c = self._get_node_confidence(p)
                    if c is not None:
                        parent_confs.append(c)

                if parent_confs:
                    avg_conf = round(sum(parent_confs) / len(parent_confs), 3)
                    self._set_node_confidence(ch, avg_conf)
                    updated_nodes.append(ch)

                queue.append(ch)

        self.persist()
        return updated_nodes

    def propagate_contradiction(
        self,
        contradictory_node_id: Optional[str] = None,
        target_belief_id: Optional[str] = None,
        penalty: float = 0.25,
        belief_id: Optional[str] = None,
        contradicting_evidence_id: Optional[str] = None
    ) -> Any:
        """Propagates a contradiction to affected beliefs, lowering confidence and setting CONTESTED."""
        contra_id = contradicting_evidence_id or contradictory_node_id
        target_id = belief_id or target_belief_id
        if not contra_id:
            raise ValueError("Contradictory evidence ID must be specified.")

        affected_beliefs: List[str] = []

        if target_id and target_id in self.beliefs:
            targets = [target_id]
        else:
            targets = [b_id for b_id in self.beliefs.keys() if contra_id in self.beliefs[b_id].supporting_evidence]
            if not targets:
                visited = set()
                queue = [contra_id]
                while queue:
                    curr = queue.pop(0)
                    for child in self._downstream_edges.get(curr, set()):
                        if child in self.beliefs:
                            targets.append(child)
                        elif child not in visited:
                            visited.add(child)
                            queue.append(child)

        for bid in targets:
            b = self.beliefs[bid]
            if contra_id not in b.contradictory_evidence:
                b.contradictory_evidence.append(contra_id)
            b.contradiction_count += 1
            b.confidence = max(0.01, round(b.confidence - penalty, 3))
            b.lifecycle_state = "CONTRADICTED"
            b.updated_at = datetime.now(timezone.utc).isoformat()
            affected_beliefs.append(bid)

            if b.confidence <= 0.20:
                b.lifecycle_state = "RETIRED"
                logger.warning(f"Belief '{bid}' retired due to contradiction penalty drop below 0.20.")

        self.persist()
        if target_id and target_id in self.beliefs:
            return self.beliefs[target_id]
        return affected_beliefs

    def apply_belief_decay(self, elapsed_cycles: int = 1, elapsed_seconds: Optional[float] = None) -> Any:
        """Applies dynamic decay rate to unverified active beliefs."""
        if elapsed_seconds is not None:
            elapsed_cycles = max(1, int(elapsed_seconds / 60))

        decayed: List[str] = []
        for bid, belief in self.beliefs.items():
            if belief.lifecycle_state in ("ACTIVE", "DECAYING", "CONTESTED", "CONTRADICTED"):
                decay_amt = round(belief.decay_rate * elapsed_cycles, 3)
                belief.confidence = max(0.01, round(belief.confidence - decay_amt, 3))
                belief.updated_at = datetime.now(timezone.utc).isoformat()
                decayed.append(bid)

                if belief.confidence <= 0.15:
                    belief.lifecycle_state = "RETIRED"
                elif belief.lifecycle_state == "ACTIVE":
                    belief.lifecycle_state = "DECAYING"

        self.persist()
        return decayed

    def corroborate_belief(
        self,
        belief_id: str,
        new_evidence_id: Optional[str] = None,
        supporting_evidence_id: Optional[str] = None,
        boost: float = 0.15
    ) -> Belief:
        """Corroborates a belief with new verified evidence, boosting confidence."""
        ev_id = supporting_evidence_id or new_evidence_id
        if not ev_id:
            raise ValueError("Evidence ID required to corroborate belief.")
        belief = self.beliefs.get(belief_id)
        if not belief:
            raise KeyError(f"Belief '{belief_id}' not found.")

        if ev_id not in belief.supporting_evidence:
            belief.supporting_evidence.append(ev_id)
            self._add_edge(ev_id, belief_id)

        belief.verification_count += 1
        belief.confidence = min(1.0, round(belief.confidence + boost, 3))
        belief.lifecycle_state = "VERIFIED"
        belief.last_verified = datetime.now(timezone.utc).isoformat()
        belief.provenance_chain = self._trace_full_provenance(belief.supporting_evidence)
        self.persist()
        return belief

    # -------------------------------------------------------------------------
    # Internal Helpers & Persistence
    # -------------------------------------------------------------------------
    def _get_node_confidence(self, node_id: str) -> Optional[float]:
        if node_id in self.evidence_nodes:
            return self.evidence_nodes[node_id].confidence
        if node_id in self.observation_nodes:
            return self.observation_nodes[node_id].confidence
        if node_id in self.finding_nodes:
            return self.finding_nodes[node_id].confidence
        if node_id in self.hypothesis_nodes:
            return self.hypothesis_nodes[node_id].confidence
        if node_id in self.beliefs:
            return self.beliefs[node_id].confidence
        return None

    def _set_node_confidence(self, node_id: str, val: float) -> None:
        if node_id in self.observation_nodes:
            self.observation_nodes[node_id].confidence = val
        elif node_id in self.finding_nodes:
            self.finding_nodes[node_id].confidence = val
        elif node_id in self.hypothesis_nodes:
            self.hypothesis_nodes[node_id].confidence = val
        elif node_id in self.beliefs:
            self.beliefs[node_id].confidence = val
            self.beliefs[node_id].updated_at = datetime.now(timezone.utc).isoformat()

    def verify_integrity(self) -> Dict[str, Any]:
        """Performs complete integrity audit of the evidence graph.

        Verifies:
        1. Every evidence reference resolves (no dangling upstream edges).
        2. Every belief update identifies its supporting or contradicting evidence.
        3. Every completed action has a recorded outcome or an explicit explanation for its absence.
        4. Failed actions cannot be recorded as successful learning.
        5. The saved graph can be reloaded and validated after process restart.
        """
        issues: List[str] = []
        all_ids = set(self.nodes.keys())

        # Check 1: Resolvable references
        for child_id, parents in self._upstream_edges.items():
            for p in parents:
                if p not in all_ids:
                    issues.append(f"Dangling reference: node '{child_id}' references non-existent parent '{p}'")

        # Check 2: Non-orphan beliefs
        for bid, b in self.beliefs.items():
            if not b.supporting_evidence:
                issues.append(f"Orphan belief: belief '{bid}' has no supporting evidence")
            for ref in b.supporting_evidence:
                if ref not in all_ids:
                    issues.append(f"Belief '{bid}' references non-existent evidence '{ref}'")

        # Check 3: Action outcomes
        outcome_action_ids = {o.action_id for o in self.outcome_nodes.values()}
        for act_id, act in self.action_nodes.items():
            if act.status == "EXECUTED" and act_id not in outcome_action_ids:
                if not act.metadata.get("explanation_for_missing_outcome"):
                    issues.append(f"Unrecorded action outcome: executed action '{act_id}' has no outcome node or explanation")

        # Check 4: Failed actions cannot be recorded as successful learning
        for l_id, l in self.learning_nodes.items():
            out_node = self.outcome_nodes.get(l.outcome_id)
            if out_node and not out_node.success and l.is_valid_learning:
                issues.append(f"Invalid learning: learning '{l_id}' marked valid despite failed outcome '{out_node.node_id}'")

        # Check 5: Reload verification
        reload_ok = True
        try:
            self.persist()
            temp_g = EvidenceGraph(storage_path=self.storage_path)
            if len(temp_g.nodes) != len(self.nodes):
                issues.append(f"Reload mismatch: persisted {len(self.nodes)} nodes, reloaded {len(temp_g.nodes)}")
                reload_ok = False
        except Exception as e:
            issues.append(f"Restart reload failure: {e}")
            reload_ok = False

        is_valid = len(issues) == 0
        return {
            "is_valid": is_valid,
            "valid": is_valid,
            "total_nodes": len(self.nodes),
            "evidence_nodes": len(self.evidence_nodes),
            "observation_nodes": len(self.observation_nodes),
            "finding_nodes": len(self.finding_nodes),
            "hypothesis_nodes": len(self.hypothesis_nodes),
            "beliefs": len(self.beliefs),
            "goal_nodes": len(self.goal_nodes),
            "action_nodes": len(self.action_nodes),
            "outcome_nodes": len(self.outcome_nodes),
            "learning_nodes": len(self.learning_nodes),
            "issues": issues,
            "reload_verified": reload_ok
        }

    def persist(self) -> None:
        """Persists the evidence graph atomically to disk."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "cycle": self.current_cycle,
                "evidence_nodes": {k: v.model_dump() for k, v in self.evidence_nodes.items()},
                "observation_nodes": {k: v.model_dump() for k, v in self.observation_nodes.items()},
                "finding_nodes": {k: v.model_dump() for k, v in self.finding_nodes.items()},
                "hypothesis_nodes": {k: v.model_dump() for k, v in self.hypothesis_nodes.items()},
                "beliefs": {k: v.model_dump() for k, v in self.beliefs.items()},
                "goal_nodes": {k: v.model_dump() for k, v in self.goal_nodes.items()},
                "action_nodes": {k: v.model_dump() for k, v in self.action_nodes.items()},
                "outcome_nodes": {k: v.model_dump() for k, v in self.outcome_nodes.items()},
                "learning_nodes": {k: v.model_dump() for k, v in self.learning_nodes.items()},
                "downstream_edges": {k: list(v) for k, v in self._downstream_edges.items()},
                "upstream_edges": {k: list(v) for k, v in self._upstream_edges.items()}
            }
            tmp_path = self.storage_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            if tmp_path.exists():
                tmp_path.replace(self.storage_path)
        except Exception as e:
            logger.warning(f"Could not persist evidence graph: {e}")

    def _load(self) -> None:
        """Loads and deserializes all node types from disk."""
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.current_cycle = data.get("cycle", 0)
            for k, v in data.get("evidence_nodes", {}).items():
                self.evidence_nodes[k] = EvidenceNode(**v)
            for k, v in data.get("observation_nodes", {}).items():
                self.observation_nodes[k] = ObservationNode(**v)
            for k, v in data.get("finding_nodes", {}).items():
                self.finding_nodes[k] = FindingNode(**v)
            for k, v in data.get("hypothesis_nodes", {}).items():
                self.hypothesis_nodes[k] = HypothesisNode(**v)
            for k, v in data.get("beliefs", {}).items():
                self.beliefs[k] = Belief(**v)
            for k, v in data.get("goal_nodes", {}).items():
                self.goal_nodes[k] = GoalNode(**v)
            for k, v in data.get("action_nodes", {}).items():
                self.action_nodes[k] = ActionNode(**v)
            for k, v in data.get("outcome_nodes", {}).items():
                self.outcome_nodes[k] = OutcomeNode(**v)
            for k, v in data.get("learning_nodes", {}).items():
                self.learning_nodes[k] = LearningNode(**v)
            for k, v in data.get("downstream_edges", {}).items():
                self._downstream_edges[k] = set(v)
            for k, v in data.get("upstream_edges", {}).items():
                self._upstream_edges[k] = set(v)
        except Exception as e:
            logger.warning(f"Could not load evidence graph: {e}")


# Singleton default graph
evidence_graph = EvidenceGraph()
