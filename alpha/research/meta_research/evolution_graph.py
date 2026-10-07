"""Theory Evolution Graph: Tracks the intellectual lineage and genealogy of scientific theories."""

from __future__ import annotations

import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class TheoryEvolutionNode(BaseModel):
    theory_id: str
    theory_name: str
    domain: str
    version: int
    parent_theory_ids: List[str] = Field(default_factory=list)
    child_theory_ids: List[str] = Field(default_factory=list)
    evolution_type: str = "GENESIS"  # GENESIS, REVISION, MERGER, SPLIT, SUPERSEDED


class TheoryEvolutionGraph:
    """Directed graph capturing the historical genealogy of theoretical models."""

    def __init__(self):
        self.nodes: Dict[str, TheoryEvolutionNode] = {}
        self._lock = threading.RLock()

    def record_genesis(self, theory_id: str, name: str, domain: str) -> TheoryEvolutionNode:
        with self._lock:
            node = TheoryEvolutionNode(
                theory_id=theory_id,
                theory_name=name,
                domain=domain,
                version=1,
                evolution_type="GENESIS"
            )
            self.nodes[theory_id] = node
            return node

    def record_revision(self, parent_id: str, new_theory_id: str, new_name: str, version: int) -> TheoryEvolutionNode:
        with self._lock:
            parent = self.nodes.get(parent_id)
            node = TheoryEvolutionNode(
                theory_id=new_theory_id,
                theory_name=new_name,
                domain=parent.domain if parent else "general",
                version=version,
                parent_theory_ids=[parent_id] if parent else [],
                evolution_type="REVISION"
            )
            if parent:
                parent.child_theory_ids.append(new_theory_id)
            self.nodes[new_theory_id] = node
            return node

    def record_merger(self, parent_ids: List[str], merged_id: str, merged_name: str, domain: str) -> TheoryEvolutionNode:
        with self._lock:
            node = TheoryEvolutionNode(
                theory_id=merged_id,
                theory_name=merged_name,
                domain=domain,
                version=1,
                parent_theory_ids=list(parent_ids),
                evolution_type="MERGER"
            )
            for pid in parent_ids:
                if pid in self.nodes:
                    self.nodes[pid].child_theory_ids.append(merged_id)
            self.nodes[merged_id] = node
            return node

    def get_lineage(self, theory_id: str) -> List[str]:
        with self._lock:
            lineage = []
            curr = self.nodes.get(theory_id)
            while curr and curr.parent_theory_ids:
                parent_id = curr.parent_theory_ids[0]
                lineage.append(parent_id)
                curr = self.nodes.get(parent_id)
            return lineage
