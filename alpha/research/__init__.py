"""Project Alpha: Phase 5 Research Civilization Package.

Transforms Alpha into a self-sustaining discovery civilization capable of:
- Unknown Detection & Question Discovery
- Hypothesis Generation & Competition
- Experiment Planning, Simulation & Auditing
- Evidence Marketplaces, Chains, & Trust
- Parsimonious Causal Theory Formulation
- Mandatory Independent Replication
- 7 Specialized Scientific Discovery Agents
- 9 Canonical Domains + 100+ Specialized Subdomains
- Valued Knowledge Resource Economy
- 5-Layer Inviolable Governance (Truth, Governance, Identity, Drift, Replication)
- Meta-Research & Intellectual History Preservation
- Recursive Alpha Self-Research
- Continuous Autonomous Discovery Loops
"""

from alpha.research.entities import (
    ResearchStatus,
    EvidencePolarity,
    EvidenceStrength,
    ResearchProblem,
    ResearchQuestion,
    Hypothesis,
    Experiment,
    Observation,
    Evidence,
    Finding,
    Prediction,
    Theory,
    Replication,
    Refutation,
    Publication,
)

from alpha.research.graph import (
    ResearchEdgeType,
    ResearchEdge,
    ResearchGraph,
)

from alpha.research.curiosity import (
    UnknownDetector,
    DetectedUnknown,
    KnowledgeFrontierMapper,
    KnowledgeFrontierMap,
    DomainFrontier,
    QuestionGenerator,
    ResearchPrioritizer,
    ResearchBacklog,
    KnowledgeGapEntry,
)

from alpha.research.hypotheses import (
    HypothesisGenerator,
    PatternDetector,
    AnalogyEngine,
    ConceptBlender,
    AnomalyDetector,
    HypothesisCompetitionManager,
    HypothesisMatchup,
)

from alpha.research.experiments import (
    ExperimentPlanner,
    ExperimentPlanMetrics,
    ExperimentSimulator,
    SimulationOutcome,
    ExperimentValidator,
    ExperimentValidationReport,
)

from alpha.research.evidence import (
    EvidenceMarketplace,
    EvidenceListing,
    EvidenceStake,
    EvidenceRankingEngine,
    EvidenceProvenanceChain,
    ChainLink,
    EvidenceConflictResolver,
    ConflictResolutionVerdict,
    EvidenceTrustModel,
    AgentTrustProfile,
)

from alpha.research.theories import (
    TheoryBuilder,
    TheoryEvaluator,
    TheoryAuditReport,
    TheoryRefiner,
    TheoryRetirement,
)

from alpha.research.agents import (
    ScientificAgentBase,
    AgentActionLog,
    LiteratureAgent,
    HypothesisAgent,
    ExperimentAgent,
    CriticAgent,
    ReplicationAgent,
    PublicationAgent,
    MetaResearchAgent,
)

from alpha.research.cross_domain import (
    CANONICAL_DOMAINS,
    SUBDOMAINS_BY_PARENT,
    DomainRegistry,
    CrossDomainSynthesizer,
    CrossDomainSynthesisResult,
)

from alpha.research.knowledge_economy import (
    KnowledgeAsset,
    KnowledgeAssetRanker,
)

from alpha.research.governance import (
    ResearchGovernancePipeline,
    GovernanceAuditResult,
    LayerAuditResult,
)

from alpha.research.meta_research import (
    ResearchArchives,
    TimelineEvent,
    TheoryEvolutionGraph,
    TheoryEvolutionNode,
    MethodologyEvaluator,
)

from alpha.research.competition import (
    ScientificArena,
    CompetitionTournamentResult,
)

from alpha.research.feedback import (
    ResearchWorldModelBridge,
    WorldModelFeedbackSummary,
)

from alpha.research.self_research import (
    AlphaSelfResearchBranch,
    ArchitecturalProposal,
)

from alpha.research.loops import (
    ScientificDiscoveryLoop,
    DiscoveryCycleRecord,
)

from alpha.research.civilization import (
    ResearchCivilization,
    ResearchCivilizationTelemetry,
)

__all__ = [
    # Entities & Graph
    "ResearchStatus",
    "EvidencePolarity",
    "EvidenceStrength",
    "ResearchProblem",
    "ResearchQuestion",
    "Hypothesis",
    "Experiment",
    "Observation",
    "Evidence",
    "Finding",
    "Prediction",
    "Theory",
    "Replication",
    "Refutation",
    "Publication",
    "ResearchEdgeType",
    "ResearchEdge",
    "ResearchGraph",
    # Curiosity
    "UnknownDetector",
    "DetectedUnknown",
    "KnowledgeFrontierMapper",
    "KnowledgeFrontierMap",
    "DomainFrontier",
    "QuestionGenerator",
    "ResearchPrioritizer",
    "ResearchBacklog",
    "KnowledgeGapEntry",
    # Hypotheses
    "HypothesisGenerator",
    "PatternDetector",
    "AnalogyEngine",
    "ConceptBlender",
    "AnomalyDetector",
    "HypothesisCompetitionManager",
    "HypothesisMatchup",
    # Experiments
    "ExperimentPlanner",
    "ExperimentPlanMetrics",
    "ExperimentSimulator",
    "SimulationOutcome",
    "ExperimentValidator",
    "ExperimentValidationReport",
    # Evidence
    "EvidenceMarketplace",
    "EvidenceListing",
    "EvidenceStake",
    "EvidenceRankingEngine",
    "EvidenceProvenanceChain",
    "ChainLink",
    "EvidenceConflictResolver",
    "ConflictResolutionVerdict",
    "EvidenceTrustModel",
    "AgentTrustProfile",
    # Theories
    "TheoryBuilder",
    "TheoryEvaluator",
    "TheoryAuditReport",
    "TheoryRefiner",
    "TheoryRetirement",
    # Scientific Agents
    "ScientificAgentBase",
    "AgentActionLog",
    "LiteratureAgent",
    "HypothesisAgent",
    "ExperimentAgent",
    "CriticAgent",
    "ReplicationAgent",
    "PublicationAgent",
    "MetaResearchAgent",
    # Cross Domain
    "CANONICAL_DOMAINS",
    "SUBDOMAINS_BY_PARENT",
    "DomainRegistry",
    "CrossDomainSynthesizer",
    "CrossDomainSynthesisResult",
    # Knowledge Economy
    "KnowledgeAsset",
    "KnowledgeAssetRanker",
    # Governance
    "ResearchGovernancePipeline",
    "GovernanceAuditResult",
    "LayerAuditResult",
    # Meta-Research
    "ResearchArchives",
    "TimelineEvent",
    "TheoryEvolutionGraph",
    "TheoryEvolutionNode",
    "MethodologyEvaluator",
    # Competition
    "ScientificArena",
    "CompetitionTournamentResult",
    # Feedback & Self-Research
    "ResearchWorldModelBridge",
    "WorldModelFeedbackSummary",
    "AlphaSelfResearchBranch",
    "ArchitecturalProposal",
    # Discovery Loops & Master Facade
    "ScientificDiscoveryLoop",
    "DiscoveryCycleRecord",
    "ResearchCivilization",
    "ResearchCivilizationTelemetry",
]
