"""Cognitive World Model: The definitive Reality-Based Mind for Project Alpha.

Unified Master Model integrating:
- Universal Ontology Engine (Part 1)
- Universal Knowledge Graph (Part 2)
- Belief System & Epistemology (Part 3)
- Evidence Engine (Part 4)
- Causal Reasoning Engine (Part 5)
- World State Engine (Part 6)
- Temporal Reasoning Engine (Part 7)
- Self Model (Part 8)
- Knowledge Distillation Engine (Part 9)
- Concept Formation Engine (Part 10)
- Knowledge Synthesis Engine (Part 11)
- Uncertainty Engine (Part 12)
- World Simulation Engine (Part 13)
- Civilizational Knowledge System (Part 14)
- Meta-Knowledge Engine (Part 15)
- Cognitive Evolution Pipeline (Part 16)
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional

from alpha.world_model.ontology import (
    Entity,
    EntityType,
    LifecycleState,
    OntologyRegistry,
    OntologyValidator,
    OntologyVersionManager,
    OntologyEvolutionEngine,
    ConceptEntity,
    RuleEntity,
    BeliefEntity,
    TaskEntity,
    GoalEntity,
    ProjectEntity,
    AgentEntity,
    ToolEntity,
    SkillEntity,
)
from alpha.world_model.graph import (
    KnowledgeGraphCore,
    RelationType,
    GraphEdge,
    RelationshipEngine,
    GraphQueryEngine,
    GraphAnalyticsEngine,
)
from alpha.world_model.epistemology import (
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    EvidenceRegistry,
    EvidenceRankingSystem,
    EvidenceAggregator,
    UncertaintyLevel,
    UncertaintyEngine,
    CalibratedEstimate,
    Belief,
    BeliefSystem,
    EvidenceChainEngine,
    ContradictionDiscoveryEngine,
    WorldModelImmuneSystem,
    SelfKnowledgeEngine,
)
from alpha.world_model.causal import (
    CausalReasoningEngine,
    CausalLink,
    CauseGraphValidator,
    CounterfactualEngine,
    ConfounderDetector,
)
from alpha.scientific.scientific_engine import ScientificMethodEngine
from alpha.verification.external_grounding import ExternalGroundingMonitor
from alpha.verification.epistemic_health import EpistemicHealthDashboard
from alpha.verification.stress_testing import TruthStressTester
from alpha.world_model.temporal import (
    TimeEngine,
    LifecycleStage,
    LifecycleTracker,
    TimelineEvent,
    EventTimeline,
    BeliefTimeline,
    StateTimeline,
)
from alpha.world_model.state import (
    WorldStateSnapshot,
    WorldStateEngine,
)
from alpha.world_model.self_model import (
    SelfModel,
    SelfIntrospection,
)
from alpha.world_model.distillation import (
    DistillationEngine,
    CompressionEngine,
    AbstractionEngine,
    PatternExtractionEngine,
)
from alpha.world_model.concepts import (
    ConceptDiscoveryEngine,
    TaxonomyBuilder,
)
from alpha.world_model.synthesis import (
    KnowledgeSynthesisEngine,
    SynthesizedInsight,
)
from alpha.world_model.simulation import (
    WorldSimulationEngine,
    SimulationOutcome,
)
from alpha.world_model.civilization import (
    CivilizationalKnowledgeSystem,
    CivilizationalAsset,
)
from alpha.world_model.meta_knowledge import (
    MetaKnowledgeEngine,
    KnowledgeGap,
    LearningPriority,
)
from alpha.world_model.pipeline import (
    CognitivePipeline,
    CognitiveEvolutionResult,
)


class CognitiveWorldModel:
    """The central Cognitive World Model of Project Alpha."""

    def __init__(self):
        # 1. Ontology Engine
        self.ontology = OntologyRegistry()
        self.validator = self.ontology.validator
        self.version_manager = self.ontology.versioning
        self.evolution = self.ontology.evolution

        # 2. Universal Knowledge Graph
        self.graph = KnowledgeGraphCore()
        self.relationships = self.graph.relationship_engine
        self.graph_query = GraphQueryEngine(self.graph)
        self.graph_analytics = GraphAnalyticsEngine(self.graph)

        # 3. Epistemology & Evidence & Uncertainty
        self.evidence_registry = EvidenceRegistry()
        self.evidence_ranker = EvidenceRankingSystem()
        self.evidence_aggregator = EvidenceAggregator(self.evidence_ranker)
        self.uncertainty = UncertaintyEngine()
        self.beliefs = BeliefSystem(self.evidence_registry, self.uncertainty)

        # 4. Causal Reasoning
        self.causal = CausalReasoningEngine()

        # 5. Temporal Reasoning & Lifecycle
        self.time_engine = TimeEngine()
        self.lifecycle = LifecycleTracker()
        self.event_timeline = EventTimeline()
        self.belief_timeline = BeliefTimeline()
        self.state_timeline = StateTimeline()

        # 6. World State
        self.world_state = WorldStateEngine(self.ontology, self.beliefs)

        # 7. Self Model
        self.self_model = SelfModel(self.ontology, self.beliefs)

        # 8. Distillation & Abstraction
        self.distillation = DistillationEngine()
        self.compression = self.distillation.compression
        self.abstraction = self.distillation.abstraction
        self.pattern_extractor = self.distillation.pattern_extractor

        # 9. Concept Formation & Taxonomy
        self.concept_discovery = ConceptDiscoveryEngine()
        self.taxonomy = TaxonomyBuilder()

        # 10. Knowledge Synthesis
        self.synthesis = KnowledgeSynthesisEngine()

        # 11. Reality Sandbox / Simulation
        self.simulation = WorldSimulationEngine(self.world_state, self.causal, self.ontology)

        # 12. Civilizational Knowledge
        self.civilizational_knowledge = CivilizationalKnowledgeSystem()

        # 13. Meta-Knowledge & Gaps
        self.meta_knowledge = MetaKnowledgeEngine(self.ontology, self.beliefs)

        # 14. Cognitive Transformation Pipeline
        self.pipeline = CognitivePipeline(self.uncertainty)

        # 15. Epistemic Integrity & World Model Hardening (Phase 8)
        self.evidence_chain = EvidenceChainEngine(self.evidence_registry, self.beliefs)
        self.contradiction_discovery = ContradictionDiscoveryEngine(
            world_model=self,
            belief_system=self.beliefs,
            knowledge_graph=self.graph,
        )
        self.cause_validator = CauseGraphValidator(self.causal.cause_graph)
        self.counterfactual_engine = CounterfactualEngine(self.causal.cause_graph)
        self.confounder_detector = ConfounderDetector()
        self.immune_system = WorldModelImmuneSystem(
            belief_system=self.beliefs,
            cause_graph=self.causal.cause_graph,
            ontology=self.ontology,
        )
        self.scientific_method = ScientificMethodEngine(
            belief_system=self.beliefs,
            evidence_registry=self.evidence_registry,
            cause_graph=self.causal.cause_graph,
        )
        self.self_knowledge = SelfKnowledgeEngine(belief_system=self.beliefs)
        self.external_grounding = ExternalGroundingMonitor(
            world_model=self,
            belief_system=self.beliefs,
        )
        self.epistemic_health = EpistemicHealthDashboard(
            world_model=self,
            external_grounding=self.external_grounding,
            contradiction_engine=self.contradiction_discovery,
            causal_validator=self.cause_validator,
            immune_system=self.immune_system,
        )
        self.stress_tester = TruthStressTester(world_model=self)

        # Seed baseline foundational world knowledge
        self._initialize_baseline_world_model()

    def _initialize_baseline_world_model(self) -> None:
        """Seed foundational civilizational axioms and ontological entities."""
        # 1. Base Goal
        g1 = GoalEntity(
            name="Autonomous Self-Evolving Cognition",
            objective="Develop a fully grounded reality-based cognitive civilization",
            importance=1.0,
            confidence=1.0
        )
        self.register_entity(g1)

        # 2. Base Project
        p1 = ProjectEntity(
            name="Project Alpha Phase 4",
            goal_ids=[g1.id],
            importance=0.95,
            confidence=0.95
        )
        self.register_entity(p1)
        self.relate(p1.id, g1.id, RelationType.SUPPORTS)

        # 3. Foundational Epistemic Belief
        ev = Evidence(
            statement="Subprocess isolation and deterministic AST validators prevent arbitrary corruption.",
            polarity=EvidencePolarity.SUPPORTING,
            strength=EvidenceStrength.STRONG,
            source_type="formal_proof",
            source_id="system"
        )
        self.evidence_registry.register(ev)
        b = self.form_belief(
            statement="Deterministic verification is required before committing any generative model output to world state.",
            initial_confidence=0.98,
            evidence_ids=[ev.evidence_id],
            domain="security"
        )
        self.relate(b.belief_id, p1.id, RelationType.VALIDATES)

    # -------------------------------------------------------------------------
    # Core Unified Operations
    # -------------------------------------------------------------------------

    def register_entity(self, entity: Entity, auto_graph_node: bool = True) -> Entity:
        """Register an entity in the universal ontology and map it into the knowledge graph."""
        self.ontology.register(entity)
        self.lifecycle.record_birth(entity.id, reason="Entity registered into ontology")
        if auto_graph_node:
            self.graph.add_entity_node(entity)
        self.event_timeline.record_event(
            event_id=f"EV_REG_{entity.id[:8]}",
            event_type="entity_registered",
            actor_id="ontology_registry",
            payload={"entity_id": entity.id, "type": entity.entity_type.value, "name": entity.name},
            summary=f"Registered {entity.entity_type.value} '{entity.name}'"
        )
        return entity

    def relate(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GraphEdge:
        """Create a directed semantic edge in the universal knowledge graph."""
        edge = self.graph.add_edge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence,
            metadata=metadata
        )

        # If relation is causal or dependency, update causal reasoning engine
        if relation_type == RelationType.CAUSES:
            self.causal.register_causal_relation(source_id, target_id, strength=weight)
        elif relation_type == RelationType.DEPENDS_ON:
            self.causal.register_dependency(source_id, target_id)

        return edge

    def register_causal_link(
        self,
        cause_id: str,
        effect_id: str,
        strength: float = 1.0,
        mechanism: str = "direct",
        delay_seconds: float = 0.0
    ) -> CausalLink:
        """Register a causal mechanism and edge in knowledge graph."""
        self.relate(cause_id, effect_id, RelationType.CAUSES, weight=strength)
        return self.causal.register_causal_relation(
            cause_id, effect_id, strength=strength, mechanism=mechanism, delay_seconds=delay_seconds
        )

    def form_belief(
        self,
        statement: str,
        initial_confidence: float = 0.5,
        evidence_ids: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        domain: str = "general"
    ) -> Belief:
        """Form a confidence-weighted belief grounded in evidence."""
        b = self.beliefs.form_belief(
            statement=statement,
            initial_confidence=initial_confidence,
            evidence_ids=evidence_ids,
            sources=sources,
            domain=domain
        )
        # Register in graph
        self.graph.add_node(b.belief_id, "belief", b.statement[:40], attributes={"confidence": b.confidence})
        # Record in belief timeline
        self.belief_timeline.record_belief_state(
            b.belief_id, b.statement, b.confidence, b.is_alive(), self.time_engine.current_virtual_time
        )
        return b

    def record_evidence(
        self,
        statement: str,
        polarity: EvidencePolarity = EvidencePolarity.SUPPORTING,
        strength: EvidenceStrength = EvidenceStrength.MODERATE,
        claim_id: Optional[str] = None,
        source_id: str = "sensor"
    ) -> Evidence:
        """Register empirical evidence and update associated belief if present."""
        ev = Evidence(
            statement=statement,
            polarity=polarity,
            strength=strength,
            claim_id=claim_id,
            source_id=source_id
        )
        self.evidence_registry.register(ev)
        if claim_id and self.beliefs.get_belief(claim_id):
            self.beliefs.update_with_evidence(claim_id, ev)
            b = self.beliefs.get_belief(claim_id)
            self.belief_timeline.record_belief_state(
                b.belief_id, b.statement, b.confidence, b.is_alive(), self.time_engine.current_virtual_time
            )
        return ev

    def introspect_self(self) -> SelfIntrospection:
        """Alpha's self-awareness reflection answering all 10 existential questions."""
        return self.self_model.introspect()

    def capture_world_state(self, tag: str = "checkpoint") -> WorldStateSnapshot:
        """Capture live world state across all 12 cognitive dimensions."""
        snap = self.world_state.capture_checkpoint(tag=tag)
        self.state_timeline.record_state(snap.timestamp, snap.summary())
        return snap

    def what_was_true(self, target_time: float) -> List[Dict[str, Any]]:
        """Temporal inquiry: What was believed/true at a historical timestamp?"""
        snaps = self.belief_timeline.what_was_believed_at(target_time)
        return [{"belief_id": s.belief_id, "statement": s.statement, "confidence": s.confidence} for s in snaps]

    def what_is_true(self, min_confidence: float = 0.70) -> List[Dict[str, Any]]:
        """Epistemic inquiry: What does Alpha currently know with high certainty?"""
        active = self.beliefs.get_active_beliefs(min_confidence=min_confidence)
        return [{"belief_id": b.belief_id, "statement": b.statement, "confidence": b.confidence} for b in active]

    def what_may_become_true(self, horizon_seconds: float = 3600.0) -> WorldStateSnapshot:
        """Prognostic inquiry: Project future world state."""
        return self.world_state.project_future_state(horizon_seconds=horizon_seconds)

    def process_observation_to_understanding(self, raw_data: Dict[str, Any]) -> CognitiveEvolutionResult:
        """Transform raw observation through the complete 8-stage evolutionary pipeline."""
        res = self.pipeline.process(raw_data)
        # Register generated concept and belief into world model
        c_dict = res.concept
        concept_entity = ConceptEntity(
            id=c_dict.get("id"),
            name=c_dict.get("name"),
            definition=c_dict.get("definition", ""),
            importance=c_dict.get("importance", 0.8),
            confidence=c_dict.get("confidence", 0.85)
        )
        self.ontology.register(concept_entity, validate=False)
        self.graph.add_entity_node(concept_entity)
        return res

    @property
    def knowledge_graph(self):
        return self.graph

    @property
    def ontology_registry(self):
        return self.ontology

    @property
    def belief_system(self):
        return self.beliefs
