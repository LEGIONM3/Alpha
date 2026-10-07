"""Agent Archetypes: Full catalog of all 18 specialized cognitive agents."""

from typing import Dict, Type
from alpha.agents.core.base import AgentRole, BaseAgent
from alpha.agents.types.spec import AgentTypeSpec
from alpha.agents.types.research_and_knowledge import ResearchAgent, KnowledgeAgent, MemoryAgent
from alpha.agents.types.planning_and_architecture import PlannerAgent, ArchitectAgent, RiskAgent
from alpha.agents.types.implementation_and_testing import BuilderAgent, CodingAgent, TestingAgent, ValidationAgent
from alpha.agents.types.critique_and_reflection import CriticAgent, ReflectionAgent, MetaLearningAgent
from alpha.agents.types.governance_and_support import DirectorAgent, SecurityAgent, OptimizationAgent, AnalyticsAgent, DocumentationAgent

ROLE_TO_CLASS_MAP: Dict[AgentRole, Type[BaseAgent]] = {
    AgentRole.RESEARCHER: ResearchAgent,
    AgentRole.PLANNER: PlannerAgent,
    AgentRole.ARCHITECT: ArchitectAgent,
    AgentRole.BUILDER: BuilderAgent,
    AgentRole.CODER: CodingAgent,
    AgentRole.TESTER: TestingAgent,
    AgentRole.VALIDATOR: ValidationAgent,
    AgentRole.MEMORY: MemoryAgent,
    AgentRole.KNOWLEDGE: KnowledgeAgent,
    AgentRole.OPTIMIZER: OptimizationAgent,
    AgentRole.ANALYTICS: AnalyticsAgent,
    AgentRole.DOCUMENTER: DocumentationAgent,
    AgentRole.SECURITY: SecurityAgent,
    AgentRole.RISK: RiskAgent,
    AgentRole.CRITIC: CriticAgent,
    AgentRole.REFLECTOR: ReflectionAgent,
    AgentRole.META_LEARNER: MetaLearningAgent,
    AgentRole.DIRECTOR: DirectorAgent,
}

__all__ = [
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
]
