"""Causal Graphs: Cause Graph, Effect Graph, Dependency Graph, and Influence Network.

Part 5: Causal Reasoning Engine
Transforms associative correlation ("A related to B") into mechanistic causality ("A causes B").
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field
import networkx as nx


class CausalLink(BaseModel):
    """Directed causal mechanism link between two entities or events."""
    link_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cause_id: str
    effect_id: str
    strength: float = Field(default=1.0, ge=0.0, le=1.0)       # Causal efficacy [0, 1]
    time_delay_seconds: float = Field(default=0.0, ge=0.0)      # Temporal lag
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    mechanism: str = "direct_mechanism"
    sign: int = 1                                              # +1 for excitatory/generative, -1 for inhibitory/preventative


class CauseGraph:
    """Directed acyclic network of causal generation: Cause -> Effect."""

    def __init__(self):
        self._links: Dict[str, CausalLink] = {}
        self._by_cause: Dict[str, List[CausalLink]] = {}
        self._by_effect: Dict[str, List[CausalLink]] = {}

    def add_causal_link(self, link: CausalLink) -> CausalLink:
        self._links[link.link_id] = link
        if link.cause_id not in self._by_cause:
            self._by_cause[link.cause_id] = []
        self._by_cause[link.cause_id].append(link)

        if link.effect_id not in self._by_effect:
            self._by_effect[link.effect_id] = []
        self._by_effect[link.effect_id].append(link)
        return link

    def get_causes_of(self, effect_id: str) -> List[CausalLink]:
        return self._by_effect.get(effect_id, [])

    def get_effects_of(self, cause_id: str) -> List[CausalLink]:
        return self._by_cause.get(cause_id, [])

    def to_networkx(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for link in self._links.values():
            g.add_edge(
                link.cause_id,
                link.effect_id,
                strength=link.strength,
                weight=link.strength,
                delay=link.time_delay_seconds,
                sign=link.sign,
                mechanism=link.mechanism
            )
        return g


class EffectGraph:
    """Forward-looking projection graph tracking cascades of downstream consequences."""

    def __init__(self, cause_graph: CauseGraph):
        self.cause_graph = cause_graph

    def trace_effects(self, source_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Breadth-first forward trace of downstream ripple effects."""
        visited: Dict[str, Dict[str, Any]] = {}
        queue = [(source_id, 1.0, 0)]  # (current_id, accumulated_impact, current_depth)

        while queue:
            cur_id, impact, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for link in self.cause_graph.get_effects_of(cur_id):
                child_id = link.effect_id
                child_impact = impact * link.strength * (1 if link.sign > 0 else -0.5)
                if child_id not in visited or abs(child_impact) > abs(visited[child_id]["impact"]):
                    visited[child_id] = {
                        "parent": cur_id,
                        "impact": round(child_impact, 3),
                        "depth": depth + 1,
                        "mechanism": link.mechanism
                    }
                    queue.append((child_id, child_impact, depth + 1))

        return visited


class DependencyGraph:
    """Manages operational and structural prerequisites: Node requires Prerequisites."""

    def __init__(self):
        self._dependencies: Dict[str, Set[str]] = {}  # node -> set of prerequisites
        self._dependents: Dict[str, Set[str]] = {}    # prerequisite -> set of nodes depending on it

    def add_dependency(self, node_id: str, prerequisite_id: str) -> None:
        if node_id not in self._dependencies:
            self._dependencies[node_id] = set()
        self._dependencies[node_id].add(prerequisite_id)

        if prerequisite_id not in self._dependents:
            self._dependents[prerequisite_id] = set()
        self._dependents[prerequisite_id].add(node_id)

    def get_prerequisites(self, node_id: str) -> Set[str]:
        return self._dependencies.get(node_id, set())

    def get_dependents(self, prerequisite_id: str) -> Set[str]:
        return self._dependents.get(prerequisite_id, set())

    def to_networkx(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for node, prereqs in self._dependencies.items():
            for prereq in prereqs:
                g.add_edge(prereq, node)  # Prerequisite -> Node
        return g

    def topological_order(self) -> List[str]:
        """Compute valid execution order satisfying all dependencies."""
        g = self.to_networkx()
        try:
            return list(nx.topological_sort(g))
        except nx.NetworkXUnfeasible:
            # Contains cycle
            return []


class InfluenceNetwork:
    """Continuous weighted influence graph supporting probabilistic and graded influences."""

    def __init__(self):
        self._influences: Dict[str, Dict[str, float]] = {}  # src -> {tgt: weight}

    def set_influence(self, source_id: str, target_id: str, weight: float) -> None:
        """Set signed influence weight in [-1.0, 1.0]."""
        if source_id not in self._influences:
            self._influences[source_id] = {}
        self._influences[source_id][target_id] = max(-1.0, min(1.0, weight))

    def get_influence(self, source_id: str, target_id: str) -> float:
        return self._influences.get(source_id, {}).get(target_id, 0.0)

    def compute_total_influence_on(self, target_id: str) -> float:
        total = 0.0
        for src, targets in self._influences.items():
            if target_id in targets:
                total += targets[target_id]
        return round(total, 3)
