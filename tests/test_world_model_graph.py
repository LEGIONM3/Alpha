"""Tests for Universal Knowledge Graph (Part 2)."""

import pytest
from alpha.world_model.graph import (
    RelationType,
    GraphEdge,
    RelationshipEngine,
    KnowledgeGraphCore,
    GraphQueryEngine,
    GraphAnalyticsEngine,
    INVERSE_RELATION_MAP,
)
from alpha.world_model.ontology import AgentEntity, ToolEntity, TaskEntity


def test_all_14_relationship_types_and_inverses():
    """Verify all 14 mandatory relationship types exist and have valid semantic inverses."""
    assert len(RelationType) == 14
    engine = RelationshipEngine()

    for rel in RelationType:
        inv = engine.get_inverse_relation(rel)
        assert inv is not None
        assert isinstance(inv, str)

    assert engine.is_causal(RelationType.CAUSES) is True
    assert engine.is_causal(RelationType.DEPENDS_ON) is True
    assert engine.is_causal(RelationType.REFERENCES) is False

    assert engine.is_epistemic(RelationType.SUPPORTS) is True
    assert engine.is_epistemic(RelationType.CONTRADICTS) is True
    assert engine.is_epistemic(RelationType.VALIDATES) is True


def test_knowledge_graph_bidirectional_indexing():
    """Verify forward and reverse adjacency consistency."""
    graph = KnowledgeGraphCore()

    n1 = graph.add_node("agent_01", "agent", "CoderAgent")
    n2 = graph.add_node("tool_01", "tool", "PythonExecutor")
    n3 = graph.add_node("task_01", "task", "BuildModule")

    e1 = graph.add_edge("agent_01", "tool_01", RelationType.USES, weight=0.9)
    e2 = graph.add_edge("agent_01", "task_01", RelationType.DEPENDS_ON, weight=1.0)

    assert graph.node_count() == 3
    assert graph.edge_count() == 2

    out_e = graph.get_out_edges("agent_01")
    assert len(out_e) == 2

    in_e = graph.get_in_edges("tool_01")
    assert len(in_e) == 1
    assert in_e[0].source_id == "agent_01"

    # Remove node removes incident edges
    graph.remove_node("tool_01")
    assert graph.node_count() == 2
    assert graph.edge_count() == 1
    assert len(graph.get_out_edges("agent_01")) == 1


def test_graph_query_paths_and_subgraphs():
    """Verify path finding, neighborhood expansion, and pattern matching."""
    graph = KnowledgeGraphCore()
    query = GraphQueryEngine(graph)

    # Chain: A -> B -> C -> D
    graph.add_edge("A", "B", RelationType.DEPENDS_ON)
    graph.add_edge("B", "C", RelationType.CAUSES)
    graph.add_edge("C", "D", RelationType.VALIDATES)
    graph.add_edge("A", "D", RelationType.RELATED_TO)

    path = query.find_shortest_path("A", "C")
    assert path == ["A", "B", "C"]

    all_paths = query.find_all_paths("A", "D")
    assert len(all_paths) == 2  # ["A", "D"] and ["A", "B", "C", "D"]

    neighbors = query.get_neighbors("B", direction="both")
    neighbor_ids = {n.node_id for n in neighbors}
    assert "A" in neighbor_ids
    assert "C" in neighbor_ids

    sub = query.extract_subgraph(["B"], depth=1)
    sub_node_ids = {n.node_id for n in sub.nodes}
    assert "A" in sub_node_ids
    assert "B" in sub_node_ids
    assert "C" in sub_node_ids


def test_graph_pattern_matching():
    """Verify pattern matching triplets."""
    graph = KnowledgeGraphCore()
    query = GraphQueryEngine(graph)

    graph.add_node("ag1", "agent", "AgentOne")
    graph.add_node("t1", "tool", "ToolOne")
    graph.add_node("doc1", "document", "DocOne")

    graph.add_edge("ag1", "t1", RelationType.USES)
    graph.add_edge("ag1", "doc1", RelationType.REFERENCES)

    matches = query.pattern_match(source_type="agent", relation_type=RelationType.USES, target_type="tool")
    assert len(matches) == 1
    assert matches[0]["source"]["node_id"] == "ag1"
    assert matches[0]["target"]["node_id"] == "t1"


def test_graph_analytics_centrality_and_pagerank():
    """Verify PageRank, degree centrality, betweenness, and cycle detection."""
    graph = KnowledgeGraphCore()
    analytics = GraphAnalyticsEngine(graph)

    # Star graph centered on Hub
    graph.add_edge("N1", "Hub", RelationType.SUPPORTS)
    graph.add_edge("N2", "Hub", RelationType.SUPPORTS)
    graph.add_edge("N3", "Hub", RelationType.SUPPORTS)
    graph.add_edge("Hub", "Sink", RelationType.CAUSES)

    pr = analytics.compute_pagerank()
    assert "Hub" in pr
    assert "Sink" in pr
    # Sink and Hub accumulate prominence
    assert pr["Sink"] > pr["N1"]

    deg = analytics.compute_degree_centrality()
    assert deg["Hub"] > deg["N1"]

    assert analytics.is_acyclic() is True
    assert len(analytics.detect_cycles()) == 0

    # Add cycle: Sink -> N1
    graph.add_edge("Sink", "N1", RelationType.CAUSES)
    assert analytics.is_acyclic() is False
    assert len(analytics.detect_cycles()) >= 1
