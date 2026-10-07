"""Research Knowledge Graph: Graph representation of all scientific research entities and linkages.

Connects Problems, Questions, Hypotheses, Experiments, Observations, Evidence,
Findings, Theories, Predictions, Publications, Replications, and Refutations.
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel, Field

from alpha.research.entities import (
    ResearchProblem,
    ResearchQuestion,
    Hypothesis,
    Experiment,
    Observation,
    Evidence,
    Finding,
    Theory,
    Prediction,
    Publication,
    Replication,
    Refutation,
)


class ResearchEdgeType(str, Enum):
    ADDRESSES_PROBLEM = "ADDRESSES_PROBLEM"
    DERIVED_FROM_QUESTION = "DERIVED_FROM_QUESTION"
    TESTED_BY_EXPERIMENT = "TESTED_BY_EXPERIMENT"
    GENERATED_OBSERVATION = "GENERATED_OBSERVATION"
    SUPPORTS_HYPOTHESIS = "SUPPORTS_HYPOTHESIS"
    REFUTES_HYPOTHESIS = "REFUTES_HYPOTHESIS"
    EVIDENCED_BY = "EVIDENCED_BY"
    SUPPORTS_FINDING = "SUPPORTS_FINDING"
    SYNTHESIZED_INTO_THEORY = "SYNTHESIZED_INTO_THEORY"
    GENERATES_PREDICTION = "GENERATES_PREDICTION"
    REPLICATES_EXPERIMENT = "REPLICATES_EXPERIMENT"
    REFUTES_ENTITY = "REFUTES_ENTITY"
    PUBLISHED_IN = "PUBLISHED_IN"
    EVOLVED_FROM = "EVOLVED_FROM"


class ResearchEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: ResearchEdgeType
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


CLASS_TO_ID_FIELD = {
    "ResearchProblem": "problem_id",
    "ResearchQuestion": "question_id",
    "Hypothesis": "hypothesis_id",
    "Experiment": "experiment_id",
    "Observation": "observation_id",
    "Evidence": "evidence_id",
    "Finding": "finding_id",
    "Theory": "theory_id",
    "Prediction": "prediction_id",
    "Publication": "publication_id",
    "Replication": "replication_id",
    "Refutation": "refutation_id",
}


class ResearchGraph:
    """Thread-safe dedicated Graph for all scientific entities and epistemic lineages."""

    def __init__(self):
        self._nodes: Dict[str, Any] = {}
        self._node_types: Dict[str, str] = {}
        self._edges: List[ResearchEdge] = []
        self._adjacency_out: Dict[str, List[ResearchEdge]] = {}
        self._adjacency_in: Dict[str, List[ResearchEdge]] = {}
        self._lock = threading.RLock()

    def add_node(self, entity: Any) -> str:
        """Register any research entity as a graph node."""
        with self._lock:
            cls_name = entity.__class__.__name__
            id_field = CLASS_TO_ID_FIELD.get(cls_name)
            node_id = getattr(entity, id_field, None) if id_field else None

            if not node_id:
                for field in [
                    f"{cls_name.lower()}_id",
                    "id", "hypothesis_id", "question_id", "problem_id",
                    "experiment_id", "observation_id", "evidence_id", "finding_id",
                    "theory_id", "prediction_id", "publication_id", "replication_id", "refutation_id"
                ]:
                    val = getattr(entity, field, None)
                    if val:
                        node_id = val
                        break

            if not node_id:
                raise ValueError(f"Cannot determine ID for entity: {entity}")

            self._nodes[node_id] = entity
            self._node_types[node_id] = entity.__class__.__name__
            if node_id not in self._adjacency_out:
                self._adjacency_out[node_id] = []
            if node_id not in self._adjacency_in:
                self._adjacency_in[node_id] = []
            return node_id

    def get_node(self, node_id: str) -> Optional[Any]:
        with self._lock:
            return self._nodes.get(node_id)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: ResearchEdgeType,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResearchEdge:
        with self._lock:
            edge = ResearchEdge(
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                weight=weight,
                metadata=metadata or {}
            )
            self._edges.append(edge)
            self._adjacency_out.setdefault(source_id, []).append(edge)
            self._adjacency_in.setdefault(target_id, []).append(edge)
            return edge

    def get_outgoing(self, node_id: str, edge_type: Optional[ResearchEdgeType] = None) -> List[ResearchEdge]:
        with self._lock:
            edges = self._adjacency_out.get(node_id, [])
            if edge_type:
                return [e for e in edges if e.edge_type == edge_type]
            return list(edges)

    def get_incoming(self, node_id: str, edge_type: Optional[ResearchEdgeType] = None) -> List[ResearchEdge]:
        with self._lock:
            edges = self._adjacency_in.get(node_id, [])
            if edge_type:
                return [e for e in edges if e.edge_type == edge_type]
            return list(edges)

    def get_nodes_by_type(self, entity_class_name: str) -> List[Any]:
        with self._lock:
            return [
                node for nid, node in self._nodes.items()
                if self._node_types.get(nid) == entity_class_name
            ]

    def get_lineage(self, node_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Trace backward lineage through evidence and provenance."""
        with self._lock:
            visited: Set[str] = set()
            lineage: List[Dict[str, Any]] = []

            def _traverse(current_id: str, depth: int):
                if depth > max_depth or current_id in visited:
                    return
                visited.add(current_id)
                incoming = self._adjacency_in.get(current_id, [])
                for edge in incoming:
                    src_node = self._nodes.get(edge.source_id)
                    lineage.append({
                        "from_id": edge.source_id,
                        "from_type": self._node_types.get(edge.source_id),
                        "to_id": edge.target_id,
                        "edge_type": edge.edge_type.value,
                        "depth": depth
                    })
                    _traverse(edge.source_id, depth + 1)

            _traverse(node_id, 1)
            return lineage

    def stats(self) -> Dict[str, int]:
        with self._lock:
            type_counts: Dict[str, int] = {}
            for t in self._node_types.values():
                type_counts[t] = type_counts.get(t, 0) + 1
            return {
                "total_nodes": len(self._nodes),
                "total_edges": len(self._edges),
                "node_types": type_counts
            }
