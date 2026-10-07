"""Project Alpha Cognitive World Model.

Transforms Alpha from Memory-Based Intelligence into Reality-Based Intelligence.
"""

from alpha.world_model.ontology import (
    Entity,
    EntityType,
    LifecycleState,
    EntityVersion,
    ProvenanceRecord,
    PersonEntity,
    OrganizationEntity,
    ProjectEntity,
    AgentEntity,
    SkillEntity,
    ToolEntity,
    TaskEntity,
    GoalEntity,
    MemoryEntity,
    ExperienceEntity,
    DocumentEntity,
    ConceptEntity,
    RuleEntity,
    BeliefEntity,
    ObservationEntity,
    EventEntity,
    CapabilityEntity,
    ResourceEntity,
    RiskEntity,
    DecisionEntity,
    HypothesisEntity,
    TheoryEntity,
    PredictionEntity,
    SimulationEntity,
    RelationshipEntity,
    OntologyRegistry,
    OntologyValidator,
    OntologyVersionManager,
    OntologyEvolutionEngine,
)
from alpha.world_model.graph import (
    RelationType,
    GraphEdge,
    RelationshipEngine,
    GraphNode,
    KnowledgeGraphCore,
    GraphQueryEngine,
    GraphAnalyticsEngine,
)
from alpha.world_model.epistemology import (
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    EvidenceChain,
    EvidenceRegistry,
    EvidenceRankingSystem,
    EvidenceAggregator,
    UncertaintyLevel,
    CalibratedEstimate,
    UncertaintyEngine,
    Belief,
    VerificationRecord,
    BeliefSystem,
)
from alpha.world_model.causal import (
    CausalLink,
    CauseGraph,
    EffectGraph,
    DependencyGraph,
    InfluenceNetwork,
    CauseDetector,
    DependencyDiscovery,
    TemporalCorrelationAnalyzer,
    CounterfactualAnalyzer,
    RootCauseAnalyzer,
    ImpactPredictor,
    CausalReasoningEngine,
)
from alpha.world_model.temporal import (
    TimeEngine,
    LifecycleStage,
    LifecycleTransition,
    LifecycleTracker,
    TimelineEvent,
    EventTimeline,
    BeliefSnapshot,
    BeliefTimeline,
    StateTimeline,
)
from alpha.world_model.state import (
    WorldStateSnapshot,
    WorldStateEngine,
)
from alpha.world_model.self_model import (
    SelfIdentity,
    SelfIntrospection,
    SelfModel,
)
from alpha.world_model.distillation import (
    CompressionEngine,
    AbstractionEngine,
    PatternExtractionEngine,
    DistillationEngine,
)
from alpha.world_model.concepts import (
    ConceptDiscoveryEngine,
    TaxonomyNode,
    HierarchyGenerator,
    TaxonomyBuilder,
)
from alpha.world_model.synthesis import (
    SynthesizedInsight,
    KnowledgeSynthesisEngine,
)
from alpha.world_model.simulation import (
    SimulationOutcome,
    WorldSimulationEngine,
)
from alpha.world_model.civilization import (
    CivilizationalAsset,
    CivilizationalKnowledgeSystem,
)
from alpha.world_model.meta_knowledge import (
    KnowledgeGap,
    LearningPriority,
    KnowledgeGapDetector,
    CuriosityEngine,
    LearningPriorityEngine,
    MetaKnowledgeEngine,
)
from alpha.world_model.pipeline import (
    PipelineStageResult,
    CognitiveEvolutionResult,
    CognitivePipeline,
)
from alpha.world_model.model import CognitiveWorldModel

__all__ = [
    # Master Model
    "CognitiveWorldModel",
    # Ontology
    "Entity",
    "EntityType",
    "LifecycleState",
    "EntityVersion",
    "ProvenanceRecord",
    "PersonEntity",
    "OrganizationEntity",
    "ProjectEntity",
    "AgentEntity",
    "SkillEntity",
    "ToolEntity",
    "TaskEntity",
    "GoalEntity",
    "MemoryEntity",
    "ExperienceEntity",
    "DocumentEntity",
    "ConceptEntity",
    "RuleEntity",
    "BeliefEntity",
    "ObservationEntity",
    "EventEntity",
    "CapabilityEntity",
    "ResourceEntity",
    "RiskEntity",
    "DecisionEntity",
    "HypothesisEntity",
    "TheoryEntity",
    "PredictionEntity",
    "SimulationEntity",
    "RelationshipEntity",
    "OntologyRegistry",
    "OntologyValidator",
    "OntologyVersionManager",
    "OntologyEvolutionEngine",
    # Graph
    "RelationType",
    "GraphEdge",
    "RelationshipEngine",
    "GraphNode",
    "KnowledgeGraphCore",
    "GraphQueryEngine",
    "GraphAnalyticsEngine",
    # Epistemology
    "Evidence",
    "EvidencePolarity",
    "EvidenceStrength",
    "EvidenceChain",
    "EvidenceRegistry",
    "EvidenceRankingSystem",
    "EvidenceAggregator",
    "UncertaintyLevel",
    "CalibratedEstimate",
    "UncertaintyEngine",
    "Belief",
    "VerificationRecord",
    "BeliefSystem",
    # Causal
    "CausalLink",
    "CauseGraph",
    "EffectGraph",
    "DependencyGraph",
    "InfluenceNetwork",
    "CauseDetector",
    "DependencyDiscovery",
    "TemporalCorrelationAnalyzer",
    "CounterfactualAnalyzer",
    "RootCauseAnalyzer",
    "ImpactPredictor",
    "CausalReasoningEngine",
    # Temporal
    "TimeEngine",
    "LifecycleStage",
    "LifecycleTransition",
    "LifecycleTracker",
    "TimelineEvent",
    "EventTimeline",
    "BeliefSnapshot",
    "BeliefTimeline",
    "StateTimeline",
    # State
    "WorldStateSnapshot",
    "WorldStateEngine",
    # Self Model
    "SelfIdentity",
    "SelfIntrospection",
    "SelfModel",
    # Distillation
    "CompressionEngine",
    "AbstractionEngine",
    "PatternExtractionEngine",
    "DistillationEngine",
    # Concepts
    "ConceptDiscoveryEngine",
    "TaxonomyNode",
    "HierarchyGenerator",
    "TaxonomyBuilder",
    # Synthesis
    "SynthesizedInsight",
    "KnowledgeSynthesisEngine",
    # Simulation
    "SimulationOutcome",
    "WorldSimulationEngine",
    # Civilization
    "CivilizationalAsset",
    "CivilizationalKnowledgeSystem",
    # Meta Knowledge
    "KnowledgeGap",
    "LearningPriority",
    "KnowledgeGapDetector",
    "CuriosityEngine",
    "LearningPriorityEngine",
    "MetaKnowledgeEngine",
    # Pipeline
    "PipelineStageResult",
    "CognitiveEvolutionResult",
    "CognitivePipeline",
]
