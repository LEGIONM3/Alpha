"""Evidence Graph Data Models for Project Alpha.

Represents the strict 5-layer epistemic hierarchy:
Evidence -> Observation -> Finding -> Hypothesis -> Belief

Strict Invariants:
- A belief without evidence must never exist (OrphanBeliefError).
- Full provenance chain tracking from base evidence to belief.
- Explicit supporting and contradictory evidence collections.
- Dynamic confidence and decay rates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, model_validator


class OrphanBeliefError(ValueError):
    """Raised when an attempt is made to create or register a belief without verifiable evidence."""
    pass


class NodeType(str, Enum):
    EVIDENCE = "evidence"
    OBSERVATION = "observation"
    FINDING = "finding"
    HYPOTHESIS = "hypothesis"
    BELIEF = "belief"
    GOAL = "goal"
    ACTION = "action"
    OUTCOME = "outcome"
    LEARNING = "learning"


class EvidenceNode(BaseModel):
    """Base empirical facts directly recorded from external reality."""
    node_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.EVIDENCE
    content: Any
    source: str
    source_type: str = "raw_fact"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.content_hash:
            c_str = json.dumps(self.content, sort_keys=True, default=str) if isinstance(self.content, (dict, list)) else str(self.content)
            raw = f"{self.source}|{c_str}"
            self.content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ObservationNode(BaseModel):
    """Structured empirical observation derived from one or more base evidence items."""
    node_id: str = Field(default_factory=lambda: f"obs_node_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.OBSERVATION
    observation_id: str
    evidence_ids: List[str] = Field(default_factory=list)
    source: str
    source_type: str
    facts: Any
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FindingNode(BaseModel):
    """Synthesized research finding backed by verified observations and citations."""
    node_id: str = Field(default_factory=lambda: f"find_node_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.FINDING
    query: str
    observation_ids: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    claims: List[str] = Field(default_factory=list)
    evidence_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HypothesisNode(BaseModel):
    """Falsifiable scientific hypothesis formulated from findings and observations."""
    node_id: str = Field(default_factory=lambda: f"hyp_node_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.HYPOTHESIS
    statement: str
    mechanism: str
    finding_ids: List[str] = Field(default_factory=list)
    falsification_criteria: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.60, ge=0.0, le=1.0)
    status: str = "FORMULATED"  # "FORMULATED", "TESTED", "VERIFIED", "REFUTED"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Belief(BaseModel):
    """Ground-truth reality belief strictly backed by evidence lineage."""
    belief_id: str = Field(default_factory=lambda: f"belief_{uuid.uuid4().hex[:10]}")
    statement: str
    confidence: float = Field(default=0.60, ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)  # IDs of supporting nodes
    contradictory_evidence: List[str] = Field(default_factory=list)  # IDs of contradicting nodes
    contradiction_history: List[str] = Field(default_factory=list)
    verification_status: str = Field(default="UNVERIFIED")
    last_verified: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decay_rate: float = Field(default=0.02, ge=0.0, le=1.0)
    provenance_chain: List[Dict[str, Any]] = Field(default_factory=list)
    lifecycle_state: str = "ACTIVE"  # "ACTIVE", "VERIFIED", "CONTESTED", "DECAYING", "RETIRED"
    verification_count: int = 0
    contradiction_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="after")
    def validate_non_orphan(self) -> "Belief":
        if not self.supporting_evidence:
            raise OrphanBeliefError(
                f"A belief without evidence must never exist! Belief '{self.belief_id}' "
                f"statement: '{self.statement}' has zero supporting evidence."
            )
        return self

    @property
    def node_id(self) -> str:
        return self.belief_id

    @property
    def node_type(self) -> NodeType:
        return NodeType.BELIEF

    # Compatibility properties for existing code
    @property
    def evidence_items(self) -> List[Dict[str, Any]]:
        return [{"evidence_id": eid} for eid in self.supporting_evidence]

    @property
    def lineage(self) -> Any:
        class _CompatLineage:
            def __init__(self, parent_ids, evolution_log):
                self.parent_belief_ids = parent_ids
                self.child_belief_ids = []
                self.origin_observations = []
                self.evolution_log = evolution_log
        return _CompatLineage(self.supporting_evidence, self.provenance_chain)


class GoalNode(BaseModel):
    """World-driven goal emergent from verified evidence and beliefs."""
    node_id: str = Field(default_factory=lambda: f"goal_node_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.GOAL
    goal_id: str
    statement: str
    originating_belief_id: Optional[str] = None
    originating_observation_ids: List[str] = Field(default_factory=list)
    parent_ids: List[str] = Field(default_factory=list)
    channel: str = "UNKNOWN"
    epistemic_priority: float = Field(default=0.80, ge=0.0, le=1.0)
    status: str = "ACTIVE"  # "ACTIVE", "COMPLETED", "FAILED", "DEFERRED"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionNode(BaseModel):
    """Execution step or test performed by an actuator (e.g. Laya)."""
    node_id: str = Field(default_factory=lambda: f"act_node_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.ACTION
    action_name: str
    goal_id: Optional[str] = None
    parent_ids: List[str] = Field(default_factory=list)
    tool: str
    target: str
    modality: str = "FILESYSTEM_IO"  # AST_INSPECTION, FILESYSTEM_IO, TERMINAL_EXECUTION, BROWSER_AUTOMATION, GUI_AUTOMATION
    status: str = "EXECUTED"  # "EXECUTED", "FAILED", "BLOCKED"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutcomeNode(BaseModel):
    """Observed empirical result from an executed action."""
    node_id: str = Field(default_factory=lambda: f"out_node_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.OUTCOME
    action_id: str
    parent_ids: List[str] = Field(default_factory=list)
    success: bool
    observed_state: Any = None
    expected_state: Any = None
    explanation_if_failed_or_absent: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningNode(BaseModel):
    """Knowledge update synthesized from verified action outcomes."""
    node_id: str = Field(default_factory=lambda: f"learn_node_{uuid.uuid4().hex[:10]}")
    node_type: NodeType = NodeType.LEARNING
    outcome_id: str
    parent_ids: List[str] = Field(default_factory=list)
    belief_id: Optional[str] = None
    learning_type: str = "REVISION"  # REINFORCEMENT, FALSIFICATION, REVISION, DISCOVERY
    delta_confidence: float = 0.0
    is_valid_learning: bool = True  # Strict invariant: failed actions cannot be recorded as successful learning!
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
