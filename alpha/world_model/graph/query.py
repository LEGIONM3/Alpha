"""Graph Query Engine: Path finding, subgraph extraction, neighborhood expansion, and pattern matching."""

from typing import List, Dict, Any, Optional, Set
import networkx as nx

from alpha.world_model.graph.core import KnowledgeGraphCore, GraphNode
from alpha.world_model.graph.relationships import GraphEdge, RelationType


class GraphQueryResult:
    """Encapsulates nodes, edges, and paths matching a query."""
    def __init__(self, nodes: List[GraphNode], edges: List[GraphEdge], paths: Optional[List[List[str]]] = None):
        self.nodes = nodes
        self.edges = edges
        self.paths = paths or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "path_count": len(self.paths),
            "paths": self.paths
        }


class GraphQueryEngine:
    """Traverses, filters, and queries the Universal Knowledge Graph."""

    def __init__(self, graph: KnowledgeGraphCore):
        self.graph = graph

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        relation_type: Optional[RelationType] = None
    ) -> List[GraphNode]:
        """Retrieve neighboring nodes along specified direction and relation type."""
        neighbor_ids: Set[str] = set()

        if direction in ("out", "both"):
            for edge in self.graph.get_out_edges(node_id, relation_type):
                neighbor_ids.add(edge.target_id)

        if direction in ("in", "both"):
            for edge in self.graph.get_in_edges(node_id, relation_type):
                neighbor_ids.add(edge.source_id)

        return [self.graph.get_node(nid) for nid in neighbor_ids if self.graph.get_node(nid)]

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Compute the shortest path using NetworkX."""
        nx_g = self.graph.to_networkx()
        try:
            return nx.shortest_path(nx_g, source=source_id, target=target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def find_all_paths(self, source_id: str, target_id: str, cutoff: int = 4) -> List[List[str]]:
        """Compute all simple paths up to a cutoff depth."""
        nx_g = self.graph.to_networkx()
        try:
            return list(nx.all_simple_paths(nx_g, source=source_id, target=target_id, cutoff=cutoff))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def extract_subgraph(self, center_node_ids: List[str], depth: int = 1) -> GraphQueryResult:
        """Extract ego-subgraph centered around a set of nodes up to specified depth."""
        visited_nodes: Set[str] = set(center_node_ids)
        frontier: Set[str] = set(center_node_ids)

        for _ in range(depth):
            next_frontier: Set[str] = set()
            for nid in frontier:
                for edge in self.graph.get_out_edges(nid):
                    if edge.target_id not in visited_nodes:
                        next_frontier.add(edge.target_id)
                for edge in self.graph.get_in_edges(nid):
                    if edge.source_id not in visited_nodes:
                        next_frontier.add(edge.source_id)
            visited_nodes.update(next_frontier)
            frontier = next_frontier

        # Collect nodes and induced edges
        sub_nodes = [self.graph.get_node(nid) for nid in visited_nodes if self.graph.get_node(nid)]
        sub_edges = []
        for src in visited_nodes:
            for edge in self.graph.get_out_edges(src):
                if edge.target_id in visited_nodes:
                    sub_edges.append(edge)

        return GraphQueryResult(nodes=sub_nodes, edges=sub_edges)

    def pattern_match(
        self,
        source_type: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
        target_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find entity triplets matching (SourceType) -[Relation]-> (TargetType)."""
        results = []
        for edge in self.graph.get_all_edges():
            if relation_type and edge.relation_type != relation_type:
                continue

            src_node = self.graph.get_node(edge.source_id)
            tgt_node = self.graph.get_node(edge.target_id)
            if not src_node or not tgt_node:
                continue

            if source_type and src_node.node_type != source_type:
                continue
            if target_type and tgt_node.node_type != target_type:
                continue

            results.append({
                "source": src_node.to_dict(),
                "relation": edge.relation_type.value,
                "target": tgt_node.to_dict(),
                "weight": edge.weight,
                "confidence": edge.confidence
            })
        return results
