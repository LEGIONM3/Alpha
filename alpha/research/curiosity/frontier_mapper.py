"""Knowledge Frontier Mapper.

Maps the boundaries between established understanding and uncharted territory.
Tracks frontier advancement vectors, epistemic entropy, and domain saturation.
"""

from __future__ import annotations

import time
import math
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class DomainFrontier(BaseModel):
    domain: str
    known_concepts_count: int = 0
    verified_theories_count: int = 0
    open_questions_count: int = 0
    unresolved_problems_count: int = 0
    epistemic_entropy: float = Field(default=0.8, ge=0.0, le=1.0)
    frontier_expansion_velocity: float = Field(default=0.0)
    boundary_coordinates: Dict[str, float] = Field(default_factory=dict)
    last_updated: float = Field(default_factory=time.time)

    def calculate_saturation(self) -> float:
        """Estimate fraction of established domain maturity vs frontier."""
        total = self.known_concepts_count + self.open_questions_count + 1
        return round(self.known_concepts_count / total, 3)


class KnowledgeFrontierMap(BaseModel):
    domains: Dict[str, DomainFrontier] = Field(default_factory=dict)
    global_epistemic_entropy: float = 0.75
    frontier_advancement_vectors: Dict[str, float] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class KnowledgeFrontierMapper:
    """Computes geometric and information-theoretic properties of the knowledge boundary."""

    def __init__(self, research_graph: Optional[Any] = None):
        self.research_graph = research_graph
        self.domain_frontiers: Dict[str, DomainFrontier] = {}

    def initialize_domain(self, domain: str) -> DomainFrontier:
        if domain not in self.domain_frontiers:
            self.domain_frontiers[domain] = DomainFrontier(
                domain=domain,
                known_concepts_count=10,
                verified_theories_count=2,
                open_questions_count=8,
                unresolved_problems_count=5,
                epistemic_entropy=0.78,
                boundary_coordinates={"depth": 0.45, "breadth": 0.60, "novelty_potential": 0.85}
            )
        return self.domain_frontiers[domain]

    def record_advancement(self, domain: str, delta_theories: int = 1, delta_findings: int = 2) -> None:
        frontier = self.initialize_domain(domain)
        frontier.verified_theories_count += delta_theories
        frontier.known_concepts_count += delta_findings
        # Reducing entropy as understanding deepens
        frontier.epistemic_entropy = max(0.1, frontier.epistemic_entropy - 0.05 * delta_theories)
        frontier.frontier_expansion_velocity += 0.15 * (delta_theories + delta_findings)
        frontier.last_updated = time.time()

    def generate_frontier_map(self, domains: Optional[List[str]] = None) -> KnowledgeFrontierMap:
        target_domains = domains or [
            "engineering", "software", "economics", "psychology",
            "biology", "physics", "mathematics", "design", "product_systems"
        ]
        for d in target_domains:
            self.initialize_domain(d)

        advancement_vectors = {}
        total_entropy = 0.0
        for name, frontier in self.domain_frontiers.items():
            advancement_vectors[name] = round(frontier.frontier_expansion_velocity, 3)
            total_entropy += frontier.epistemic_entropy

        avg_entropy = round(total_entropy / max(1, len(self.domain_frontiers)), 3)

        return KnowledgeFrontierMap(
            domains={d: self.domain_frontiers[d] for d in target_domains if d in self.domain_frontiers},
            global_epistemic_entropy=avg_entropy,
            frontier_advancement_vectors=advancement_vectors
        )
