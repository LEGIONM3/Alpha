"""Universal Knowledge Graph: Relationship types, Edge model, and Relationship Engine.

Part 2: Universal Knowledge Graph
Supports the 14 mandatory relationship types:
depends_on, causes, supports, contradicts, created_by, belongs_to,
derived_from, improves, replaces, uses, validates, contains, references, related_to.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field


class RelationType(str, Enum):
    """The 14 canonical relationship types in Alpha's Universal Knowledge Graph."""
    DEPENDS_ON = "depends_on"
    CAUSES = "causes"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CREATED_BY = "created_by"
    BELONGS_TO = "belongs_to"
    DERIVED_FROM = "derived_from"
    IMPROVES = "improves"
    REPLACES = "replaces"
    USES = "uses"
    VALIDATES = "validates"
    CONTAINS = "contains"
    REFERENCES = "references"
    RELATED_TO = "related_to"


class GraphEdge(BaseModel):
    """A directed, weighted, semantic edge in the Universal Knowledge Graph."""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = Field(default=1.0, ge=0.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


INVERSE_RELATION_MAP: Dict[RelationType, Optional[str]] = {
    RelationType.DEPENDS_ON: "depended_on_by",
    RelationType.CAUSES: "caused_by",
    RelationType.SUPPORTS: "supported_by",
    RelationType.CONTRADICTS: "contradicted_by",
    RelationType.CREATED_BY: "creates",
    RelationType.BELONGS_TO: "owns_or_has",
    RelationType.DERIVED_FROM: "source_of",
    RelationType.IMPROVES: "improved_by",
    RelationType.REPLACES: "replaced_by",
    RelationType.USES: "used_by",
    RelationType.VALIDATES: "validated_by",
    RelationType.CONTAINS: "contained_in",
    RelationType.REFERENCES: "referenced_by",
    RelationType.RELATED_TO: "related_to",
}


class RelationshipEngine:
    """Manages relationship validation, semantics, lifecycle impacts, and inverse inferences."""

    def validate_edge(self, edge: GraphEdge) -> bool:
        """Validate edge structural integrity."""
        if not edge.source_id or not edge.target_id:
            return False
        if edge.source_id == edge.target_id and edge.relation_type in (
            RelationType.CAUSES, RelationType.REPLACES, RelationType.CONTRADICTS
        ):
            # A node cannot cause, replace, or contradict itself
            return False
        return True

    def get_inverse_relation(self, relation_type: RelationType) -> Optional[str]:
        """Return the inverse semantic descriptor for a relation type."""
        return INVERSE_RELATION_MAP.get(relation_type)

    def is_causal(self, relation_type: RelationType) -> bool:
        """Check if relation constitutes a direct causal dependency."""
        return relation_type in (RelationType.CAUSES, RelationType.DEPENDS_ON)

    def is_epistemic(self, relation_type: RelationType) -> bool:
        """Check if relation carries epistemological weight (support/contradiction)."""
        return relation_type in (RelationType.SUPPORTS, RelationType.CONTRADICTS, RelationType.VALIDATES)
