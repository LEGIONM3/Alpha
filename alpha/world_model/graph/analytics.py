"""Graph Analytics Engine: Centrality, PageRank, components, cycles, and community structures."""

from typing import Dict, List, Any
import networkx as nx

from alpha.world_model.graph.core import KnowledgeGraphCore


class GraphAnalyticsEngine:
    """Computes topological and structural properties of the Knowledge Graph."""

    def __init__(self, graph: KnowledgeGraphCore):
        self.graph = graph

    def compute_degree_centrality(self) -> Dict[str, float]:
        """Compute degree centrality for all nodes."""
        g = self.graph.to_networkx()
        if len(g) == 0:
            return {}
        return nx.degree_centrality(g)

    def compute_pagerank(self, alpha: float = 0.85, max_iter: int = 100) -> Dict[str, float]:
        """Compute PageRank scores, reflecting epistemic and structural prominence."""
        g = self.graph.to_networkx()
        if len(g) == 0:
            return {}
        try:
            return nx.pagerank(g, alpha=alpha, max_iter=max_iter)
        except Exception:
            # Fallback for disconnected or singular nodes
            return {nid: 1.0 / len(g) for nid in g.nodes()}

    def compute_betweenness_centrality(self) -> Dict[str, float]:
        """Compute betweenness centrality, detecting bridge nodes and bottleneck entities."""
        g = self.graph.to_networkx()
        if len(g) == 0:
            return {}
        return nx.betweenness_centrality(g)

    def find_connected_components(self) -> List[List[str]]:
        """Identify weakly connected components in the knowledge graph."""
        g = self.graph.to_networkx()
        if len(g) == 0:
            return []
        return [list(c) for c in nx.weakly_connected_components(g)]

    def detect_cycles(self) -> List[List[str]]:
        """Detect elementary directed cycles (vital for detecting circular logic or deadlocks)."""
        g = self.graph.to_networkx()
        if len(g) == 0:
            return []
        try:
            return list(nx.simple_cycles(g))
        except Exception:
            return []

    def is_acyclic(self) -> bool:
        """Check if graph is a Directed Acyclic Graph (DAG)."""
        g = self.graph.to_networkx()
        return nx.is_directed_acyclic_graph(g)

    def summarize(self) -> Dict[str, Any]:
        """Generate high-level structural metrics of the graph."""
        g = self.graph.to_networkx()
        n = g.number_of_nodes()
        m = g.number_of_edges()
        density = nx.density(g) if n > 1 else 0.0
        cycles = self.detect_cycles()
        comps = self.find_connected_components()

        return {
            "node_count": n,
            "edge_count": m,
            "density": round(density, 4),
            "is_dag": len(cycles) == 0,
            "cycle_count": len(cycles),
            "component_count": len(comps),
        }
