"""Epistemology module exports for Project Alpha."""

from alpha.world_model.epistemology.evidence import (
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    EvidenceChain,
    EvidenceRegistry,
    EvidenceRankingSystem,
    EvidenceAggregator,
    STRENGTH_WEIGHTS,
)
from alpha.world_model.epistemology.uncertainty import (
    UncertaintyLevel,
    CalibratedEstimate,
    UncertaintyEngine,
)
from alpha.world_model.epistemology.belief import (
    Belief,
    VerificationRecord,
    BeliefSystem,
)

from alpha.world_model.epistemology.evidence_chain import (
    EvidenceChainEngine,
    ChainValidationResult,
    EvidenceChainTrace,
)
from alpha.world_model.epistemology.contradiction import (
    ConflictType,
    ResolutionStrategy,
    ContradictionItem,
    ContradictionReport,
    ContradictionDiscoveryEngine,
)
from alpha.world_model.epistemology.immune_system import (
    ThreatType,
    QuarantineRecord,
    WorldModelImmuneSystem,
)
from alpha.world_model.epistemology.self_knowledge import (
    KnownTruth,
    WorkingHypothesis,
    KnowledgeGap,
    UnverifiableProposition,
    SelfKnowledgeState,
    SelfKnowledgeEngine,
)

__all__ = [
    "Evidence",
    "EvidencePolarity",
    "EvidenceStrength",
    "EvidenceChain",
    "EvidenceRegistry",
    "EvidenceRankingSystem",
    "EvidenceAggregator",
    "STRENGTH_WEIGHTS",
    "UncertaintyLevel",
    "CalibratedEstimate",
    "UncertaintyEngine",
    "Belief",
    "VerificationRecord",
    "BeliefSystem",
    "EvidenceChainEngine",
    "ChainValidationResult",
    "EvidenceChainTrace",
    "ConflictType",
    "ResolutionStrategy",
    "ContradictionItem",
    "ContradictionReport",
    "ContradictionDiscoveryEngine",
    "ThreatType",
    "QuarantineRecord",
    "WorldModelImmuneSystem",
    "KnownTruth",
    "WorkingHypothesis",
    "KnowledgeGap",
    "UnverifiableProposition",
    "SelfKnowledgeState",
    "SelfKnowledgeEngine",
]
