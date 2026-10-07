"""Alpha Multi-Agent Cognitive Operating System (Phase 3).

Transforms Project Alpha from a single cognitive entity into a civilization of specialized minds.
"""

# Core Runtime & Model
from alpha.agents.core.base import (
    BaseAgent,
    AgentRole,
    AgentStatus,
    AgentIdentity,
    AgentObjectives,
    AgentMetrics,
    PrivateAgentMemory,
)
from alpha.agents.core.registry import AgentRegistry
from alpha.agents.core.runtime import (
    AgentRuntime,
    AgentLifecycleManager,
    AgentScheduler,
    AgentStateManager,
    StateTransitionRecord,
)

# Communication
from alpha.agents.communication.messages import (
    AgentMessage,
    MessageType,
    MessagePriority,
)
from alpha.agents.communication.mailbox import AgentMailbox
from alpha.agents.communication.context import SharedContextLayer
from alpha.agents.communication.bus import AgentMessageBus

# 18 Specialized Archetypes
from alpha.agents.types import (
    AgentTypeSpec,
    ResearchAgent,
    PlannerAgent,
    ArchitectAgent,
    BuilderAgent,
    CodingAgent,
    TestingAgent,
    ValidationAgent,
    MemoryAgent,
    KnowledgeAgent,
    OptimizationAgent,
    AnalyticsAgent,
    DocumentationAgent,
    SecurityAgent,
    RiskAgent,
    CriticAgent,
    ReflectionAgent,
    MetaLearningAgent,
    DirectorAgent,
    ROLE_TO_CLASS_MAP,
)

# Deliberation & Competitive Reasoning
from alpha.agents.deliberation.council import (
    CouncilDeliberationSystem,
    CouncilVerdict,
)
from alpha.agents.deliberation.adversarial import (
    CompetitiveReasoningEngine,
    CompetitiveReasoningResult,
    AdversarialRound,
)

# Dynamic Teams
from alpha.agents.teams.project_team import (
    DynamicTeam,
    TeamManager,
    TeamMember,
)

# Knowledge Society
from alpha.agents.knowledge_society.knowledge_society import (
    KnowledgeItem,
    SharedKnowledgeLayer,
)

# Skill System
from alpha.agents.skills.skill_system import (
    Skill,
    SkillLibrary,
    SkillRegistry,
    SkillComposer,
    SkillExecutor,
    SkillValidator,
)

# Agent Evolution
from alpha.agents.evolution.evolution_engine import (
    AgentEvolutionEngine,
    EvolutionActionType,
    ImprovementProposal,
    AgentRankEntry,
)

# Meta-Learning Framework
from alpha.agents.meta_learning.meta_learning_engine import (
    MetaLearningFramework,
    OperationalRule,
    MetaHeuristic,
)

# 9-Layer Memory Civilization
from alpha.agents.memory_civilization.civilization_memory import (
    CivilizationMemorySystem,
    BaseMemoryLayer,
    MemoryEntry,
    RetentionPolicy,
)

# Self-Observation
from alpha.agents.observer.observer import (
    SystemObserver,
    TelemetrySnapshot,
    ImprovementReport,
)

# Execution Marketplace
from alpha.agents.marketplace.marketplace import (
    ExecutionMarketplace,
    ResourceEconomy,
    Job,
    AgentBid,
)

# Change Governance
from alpha.agents.governance.governance import (
    ChangeGovernanceSystem,
    GovernanceProposal,
)

# Virtual Simulation World
from alpha.agents.simulation.sandbox_world import (
    VirtualSandboxWorld,
    SimulationHypothesis,
    SimulationRun,
)

__all__ = [
    # Core
    "BaseAgent",
    "AgentRole",
    "AgentStatus",
    "AgentIdentity",
    "AgentObjectives",
    "AgentMetrics",
    "PrivateAgentMemory",
    "AgentRegistry",
    "AgentRuntime",
    "AgentLifecycleManager",
    "AgentScheduler",
    "AgentStateManager",
    "StateTransitionRecord",
    # Communication
    "AgentMessage",
    "MessageType",
    "MessagePriority",
    "AgentMailbox",
    "SharedContextLayer",
    "AgentMessageBus",
    # Archetypes
    "AgentTypeSpec",
    "ResearchAgent",
    "PlannerAgent",
    "ArchitectAgent",
    "BuilderAgent",
    "CodingAgent",
    "TestingAgent",
    "ValidationAgent",
    "MemoryAgent",
    "KnowledgeAgent",
    "OptimizationAgent",
    "AnalyticsAgent",
    "DocumentationAgent",
    "SecurityAgent",
    "RiskAgent",
    "CriticAgent",
    "ReflectionAgent",
    "MetaLearningAgent",
    "DirectorAgent",
    "ROLE_TO_CLASS_MAP",
    # Deliberation
    "CouncilDeliberationSystem",
    "CouncilVerdict",
    "CompetitiveReasoningEngine",
    "CompetitiveReasoningResult",
    "AdversarialRound",
    # Teams
    "DynamicTeam",
    "TeamManager",
    "TeamMember",
    # Knowledge
    "KnowledgeItem",
    "SharedKnowledgeLayer",
    # Skills
    "Skill",
    "SkillLibrary",
    "SkillRegistry",
    "SkillComposer",
    "SkillExecutor",
    "SkillValidator",
    # Evolution
    "AgentEvolutionEngine",
    "EvolutionActionType",
    "ImprovementProposal",
    "AgentRankEntry",
    # Meta Learning
    "MetaLearningFramework",
    "OperationalRule",
    "MetaHeuristic",
    # Memory Civilization
    "CivilizationMemorySystem",
    "BaseMemoryLayer",
    "MemoryEntry",
    "RetentionPolicy",
    # Observer
    "SystemObserver",
    "TelemetrySnapshot",
    "ImprovementReport",
    # Marketplace
    "ExecutionMarketplace",
    "ResourceEconomy",
    "Job",
    "AgentBid",
    # Governance
    "ChangeGovernanceSystem",
    "GovernanceProposal",
    # Simulation
    "VirtualSandboxWorld",
    "SimulationHypothesis",
    "SimulationRun",
    # Epistemic Auditor (Phase 8)
    "EpistemicAuditorAgent",
    "AuditFinding",
    "EpistemicAuditReport",
]

from alpha.agents.epistemic_auditor import (
    EpistemicAuditorAgent,
    AuditFinding,
    EpistemicAuditReport,
)
