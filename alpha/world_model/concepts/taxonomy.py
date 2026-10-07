"""Taxonomy Builder and Hierarchy Generator: Concept taxonomy trees and ontological hierarchies."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TaxonomyNode(BaseModel):
    """A node in the conceptual taxonomy tree."""
    name: str
    concept_id: Optional[str] = None
    parent_name: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    exemplar_names: List[str] = Field(default_factory=list)
    depth: int = 0
    description: str = ""


class HierarchyGenerator:
    """Infers subsumption and parent-child specialization trees."""

    def build_parent_child_link(self, parent: TaxonomyNode, child: TaxonomyNode) -> None:
        child.parent_name = parent.name
        child.depth = parent.depth + 1
        if child.name not in parent.children:
            parent.children.append(child.name)


class TaxonomyBuilder:
    """Constructs multi-level taxonomies organizing concepts from root to leaf instances."""

    def __init__(self, root_name: str = "Universal Entity"):
        self.root = TaxonomyNode(name=root_name, depth=0, description="Root of ontological taxonomy")
        self._nodes: Dict[str, TaxonomyNode] = {root_name.lower(): self.root}
        self.hierarchy_generator = HierarchyGenerator()

    def add_category(self, name: str, parent_name: Optional[str] = None, description: str = "") -> TaxonomyNode:
        p_name = parent_name or self.root.name
        parent_node = self._nodes.get(p_name.lower())
        if not parent_node:
            parent_node = self.add_category(p_name, self.root.name)

        node = TaxonomyNode(name=name, description=description)
        self.hierarchy_generator.build_parent_child_link(parent_node, node)
        self._nodes[name.lower()] = node
        return node

    def add_exemplar(self, category_name: str, exemplar_name: str) -> None:
        node = self._nodes.get(category_name.lower())
        if not node:
            node = self.add_category(category_name)
        if exemplar_name not in node.exemplar_names:
            node.exemplar_names.append(exemplar_name)

    def get_node(self, name: str) -> Optional[TaxonomyNode]:
        return self._nodes.get(name.lower())

    def get_lineage(self, name: str) -> List[str]:
        """Return path from root down to the requested category."""
        lineage = []
        curr = self.get_node(name)
        while curr:
            lineage.append(curr.name)
            curr = self.get_node(curr.parent_name) if curr.parent_name else None
        return list(reversed(lineage))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root": self.root.name,
            "total_categories": len(self._nodes),
            "hierarchy": {k: v.model_dump() for k, v in self._nodes.items()}
        }
