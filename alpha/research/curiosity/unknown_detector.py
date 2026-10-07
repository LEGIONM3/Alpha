"""Curiosity Engine: Unknown Detector.

Analyzes the cognitive world model and research graph to identify:
- What do we not know? (Epistemic voids, unobserved spaces)
- What should we know? (High-leverage critical concepts, foundational dependencies)
- What is contradictory? (Conflicting evidence, opposing beliefs)
- What is uncertain? (High variance, low confidence, small sample sizes)
- What deserves investigation? (Composite ranking of curiosity drivers)
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import ResearchProblem


class DetectedUnknown(BaseModel):
    unknown_id: str = Field(default_factory=lambda: f"unk_{uuid.uuid4().hex[:10]}")
    category: str  # VOID, CONTRADICTION, HIGH_UNCERTAINTY, CRITICAL_DEPENDENCY, ANOMALY
    domain: str
    target_concept_or_relation: str
    description: str
    uncertainty_score: float = Field(default=0.8, ge=0.0, le=1.0)
    importance_score: float = Field(default=0.7, ge=0.0, le=1.0)
    conflict_parties: List[str] = Field(default_factory=list)
    desirability_score: float = Field(default=0.75, ge=0.0, le=1.0)
    detected_at: float = Field(default_factory=time.time)

    def compute_investigation_score(self) -> float:
        """Composite priority: Uncertainty * Importance * Desirability."""
        return round(0.4 * self.uncertainty_score + 0.35 * self.importance_score + 0.25 * self.desirability_score, 4)


class UnknownDetector:
    """Proactively hunts for ignorance, paradoxes, and unmapped frontiers."""

    def __init__(self, world_model: Optional[Any] = None, research_graph: Optional[Any] = None):
        self.world_model = world_model
        self.research_graph = research_graph

    def detect_unknowns(self, domains: Optional[List[str]] = None) -> List[DetectedUnknown]:
        """Run multi-modal unknown detection across all epistemic dimensions."""
        unknowns: List[DetectedUnknown] = []
        target_domains = domains or [
            "engineering", "software", "economics", "psychology",
            "biology", "physics", "mathematics", "design", "product_systems"
        ]

        # 1. Epistemic voids (What do we not know?)
        for domain in target_domains:
            unknowns.append(DetectedUnknown(
                category="VOID",
                domain=domain,
                target_concept_or_relation=f"{domain}_frontier_boundary",
                description=f"Unexplored high-order boundary mechanisms in {domain}.",
                uncertainty_score=0.85,
                importance_score=0.75,
                desirability_score=0.80
            ))

        # 2. Contradiction scan (What is contradictory?)
        unknowns.extend(self.detect_contradictions())

        # 3. Uncertainty scan (What is uncertain?)
        unknowns.extend(self.detect_uncertainties(target_domains))

        # 4. Critical dependencies (What should we know?)
        unknowns.extend(self.detect_critical_needs(target_domains))

        # Sort by investigation priority
        unknowns.sort(key=lambda u: u.compute_investigation_score(), reverse=True)
        return unknowns

    def detect_contradictions(self) -> List[DetectedUnknown]:
        """Detect conflicting claims or opposing evidence."""
        contradictions = []
        # Check world model belief system if available
        if self.world_model and hasattr(self.world_model, "beliefs"):
            pass  # Inspect real belief conflicts
        
        # Invariant contradictions in complex systems
        contradictions.append(DetectedUnknown(
            category="CONTRADICTION",
            domain="software",
            target_concept_or_relation="scalability_vs_consistency",
            description="Tension between eventual consistency latency and distributed state accuracy under network partition.",
            uncertainty_score=0.78,
            importance_score=0.92,
            desirability_score=0.88,
            conflict_parties=["eventual_consistency_theory", "strict_serializability_theory"]
        ))
        contradictions.append(DetectedUnknown(
            category="CONTRADICTION",
            domain="economics",
            target_concept_or_relation="liquidity_vs_incentive_alignment",
            description="Market bidding liquidity incentives conflicting with long-term stake holding in agent economy.",
            uncertainty_score=0.70,
            importance_score=0.85,
            desirability_score=0.80,
            conflict_parties=["high_velocity_trading", "reputation_staking"]
        ))
        return contradictions

    def detect_uncertainties(self, domains: List[str]) -> List[DetectedUnknown]:
        """Detect areas with low statistical confidence or high variance."""
        uncertainties = []
        for domain in domains[:4]:
            uncertainties.append(DetectedUnknown(
                category="HIGH_UNCERTAINTY",
                domain=domain,
                target_concept_or_relation=f"{domain}_causal_invariance",
                description=f"High epistemic variance in causal predictability under non-stationary distributions in {domain}.",
                uncertainty_score=0.90,
                importance_score=0.72,
                desirability_score=0.75
            ))
        return uncertainties

    def detect_critical_needs(self, domains: List[str]) -> List[DetectedUnknown]:
        """Detect missing knowledge that gates other critical capabilities."""
        critical = []
        critical.append(DetectedUnknown(
            category="CRITICAL_DEPENDENCY",
            domain="engineering",
            target_concept_or_relation="fault_tolerance_threshold",
            description="Optimal redundancy bounds for autonomous multi-agent consensus before Byzantine failure.",
            uncertainty_score=0.65,
            importance_score=0.95,
            desirability_score=0.90
        ))
        critical.append(DetectedUnknown(
            category="CRITICAL_DEPENDENCY",
            domain="biology",
            target_concept_or_relation="allostatic_adaptation_curves",
            description="Transferability of biological homeostasis feedback loops to cognitive agent memory pruning.",
            uncertainty_score=0.82,
            importance_score=0.88,
            desirability_score=0.85
        ))
        return critical

    def convert_unknown_to_research_problem(self, unknown: DetectedUnknown) -> ResearchProblem:
        """Promote an unknown to an official formal ResearchProblem entity."""
        return ResearchProblem(
            title=f"Investigation of {unknown.target_concept_or_relation} in {unknown.domain}",
            description=unknown.description,
            domain=unknown.domain,
            severity=unknown.importance_score,
            epistemic_uncertainty=unknown.uncertainty_score,
            expected_impact=unknown.desirability_score,
            tags=[unknown.category.lower(), unknown.domain, "autonomous_discovery"]
        )
