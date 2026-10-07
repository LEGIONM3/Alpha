"""Knowledge Graph Core: Nodes, Adjacency representations, and Graph Operations."""

import threading
from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx

from alpha.world_model.graph.relationships import GraphEdge, RelationType, RelationshipEngine
from alpha.world_model.ontology.entities import Entity


class GraphNode:
    """Node wrapper within the Universal Knowledge Graph."""
    def __init__(self, node_id: str, node_type: str, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.node_type = node_type
        self.name = name
        self.attributes = attributes or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "attributes": self.attributes
        }


class KnowledgeGraphCore:
    """Core in-memory Knowledge Graph with bidirectional indexing and NetworkX interoperability."""

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        # Forward adjacency: source_id -> target_id -> list of GraphEdge
        self._out_edges: Dict[str, Dict[str, List[GraphEdge]]] = {}
        # Reverse adjacency: target_id -> source_id -> list of GraphEdge
        self._in_edges: Dict[str, Dict[str, List[GraphEdge]]] = {}
        # Edge lookup: edge_id -> GraphEdge
        self._edges_by_id: Dict[str, GraphEdge] = {}
        self._lock = threading.RLock()
        self.relationship_engine = RelationshipEngine()

    def add_node(self, node_id: str, node_type: str, name: str, attributes: Optional[Dict[str, Any]] = None) -> GraphNode:
        """Add or update a node in the graph."""
        with self._lock:
            node = GraphNode(node_id, node_type, name, attributes)
            self._nodes[node_id] = node
            if node_id not in self._out_edges:
                self._out_edges[node_id] = {}
            if node_id not in self._in_edges:
                self._in_edges[node_id] = {}
            return node

    def add_entity_node(self, entity: Entity) -> GraphNode:
        """Register an ontology Entity as a graph node."""
        return self.add_node(
            node_id=entity.id,
            node_type=entity.entity_type.value,
            name=entity.name,
            attributes={"importance": entity.importance, "confidence": entity.confidence, **entity.attributes}
        )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        with self._lock:
            return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        with self._lock:
            return node_id in self._nodes

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all connected edges."""
        with self._lock:
            if node_id not in self._nodes:
                return False
            del self._nodes[node_id]

            # Remove outbound edges
            out_targets = list(self._out_edges.get(node_id, {}).keys())
            for tgt in out_targets:
                for edge in self._out_edges[node_id][tgt]:
                    self._edges_by_id.pop(edge.edge_id, None)
                    if tgt in self._in_edges and node_id in self._in_edges[tgt]:
                        self._in_edges[tgt][node_id] = [e for e in self._in_edges[tgt][node_id] if e.edge_id != edge.edge_id]
            self._out_edges.pop(node_id, None)

            # Remove inbound edges
            in_sources = list(self._in_edges.get(node_id, {}).keys())
            for src in in_sources:
                for edge in self._in_edges[node_id][src]:
                    self._edges_by_id.pop(edge.edge_id, None)
                    if src in self._out_edges and node_id in self._out_edges[src]:
                        self._out_edges[src][node_id] = [e for e in self._out_edges[src][node_id] if e.edge_id != edge.edge_id]
            self._in_edges.pop(node_id, None)
            return True

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GraphEdge:
        """Add a directed semantic edge between two nodes."""
        with self._lock:
            edge = GraphEdge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                weight=weight,
                confidence=confidence,
                metadata=metadata or {}
            )
            if not self.relationship_engine.validate_edge(edge):
                raise ValueError(f"Invalid edge: {edge}")

            # Ensure nodes exist
            if source_id not in self._nodes:
                self.add_node(source_id, "unknown", f"Node_{source_id[:6]}")
            if target_id not in self._nodes:
                self.add_node(target_id, "unknown", f"Node_{target_id[:6]}")

            # Insert into forward adjacency
            if target_id not in self._out_edges[source_id]:
                self._out_edges[source_id][target_id] = []
            self._out_edges[source_id][target_id].append(edge)

            # Insert into reverse adjacency
            if source_id not in self._in_edges[target_id]:
                self._in_edges[target_id][source_id] = []
            self._in_edges[target_id][source_id].append(edge)

            self._edges_by_id[edge.edge_id] = edge
            return edge

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge by ID."""
        with self._lock:
            edge = self._edges_by_id.pop(edge_id, None)
            if not edge:
                return False
            src, tgt = edge.source_id, edge.target_id
            if src in self._out_edges and tgt in self._out_edges[src]:
                self._out_edges[src][tgt] = [e for e in self._out_edges[src][tgt] if e.edge_id != edge_id]
                if not self._out_edges[src][tgt]:
                    del self._out_edges[src][tgt]
            if tgt in self._in_edges and src in self._in_edges[tgt]:
                self._in_edges[tgt][src] = [e for e in self._in_edges[tgt][src] if e.edge_id != edge_id]
                if not self._in_edges[tgt][src]:
                    del self._in_edges[tgt][src]
            return True

    def get_out_edges(self, node_id: str, relation_type: Optional[RelationType] = None) -> List[GraphEdge]:
        """Get all outbound edges from a node."""
        with self._lock:
            res = []
            for tgt, edges in self._out_edges.get(node_id, {}).items():
                for e in edges:
                    if relation_type is None or e.relation_type == relation_type:
                        res.append(e)
            return res

    def get_in_edges(self, node_id: str, relation_type: Optional[RelationType] = None) -> List[GraphEdge]:
        """Get all inbound edges to a node."""
        with self._lock:
            res = []
            for src, edges in self._in_edges.get(node_id, {}).items():
                for e in edges:
                    if relation_type is None or e.relation_type == relation_type:
                        res.append(e)
            return res

    def get_edges_between(self, source_id: str, target_id: str) -> List[GraphEdge]:
        """Get all edges between source and target."""
        with self._lock:
            return list(self._out_edges.get(source_id, {}).get(target_id, []))

    def node_count(self) -> int:
        with self._lock:
            return len(self._nodes)

    def edge_count(self) -> int:
        with self._lock:
            return len(self._edges_by_id)

    def get_all_nodes(self) -> List[GraphNode]:
        with self._lock:
            return list(self._nodes.values())

    def get_all_edges(self) -> List[GraphEdge]:
        with self._lock:
            return list(self._edges_by_id.values())

    def to_networkx(self) -> nx.DiGraph:
        """Convert current knowledge graph into a NetworkX DiGraph."""
        with self._lock:
            g = nx.DiGraph()
            for nid, node in self._nodes.items():
                g.add_node(nid, node_type=node.node_type, name=node.name, **node.attributes)
            for edge in self._edges_by_id.values():
                g.add_edge(
                    edge.source_id,
                    edge.target_id,
                    edge_id=edge.edge_id,
                    relation=edge.relation_type.value,
                    weight=edge.weight,
                    confidence=edge.confidence
                )
            return g
