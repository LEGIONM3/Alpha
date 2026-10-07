"""Self Representation Layer: Introspective self-awareness for Project Alpha.

Part 8: Self Model
Alpha must know:
- Who am I?
- What am I?
- What can I do?
- What can I not do?
- What are my goals?
- What am I currently doing?
- What do I believe?
- What do I know?
- What do I not know?
- What should I learn next?
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.world_model.ontology.registry import OntologyRegistry
from alpha.world_model.ontology.entities import EntityType, LifecycleState
from alpha.world_model.epistemology.belief import BeliefSystem


class SelfIdentity(BaseModel):
    name: str = "Project Alpha"
    codename: str = "Omni-Cognitive World Model"
    version: str = "4.0.0"
    epoch: str = "Reality-Based Intelligence"
    architecture: str = "Multi-Agent Civilizational Cognitive Operating System with Universal Ontology & Knowledge Graph"


class SelfIntrospection(BaseModel):
    """The 10 fundamental introspective answers of Project Alpha."""
    timestamp: float = Field(default_factory=time.time)
    who_am_i: str
    what_am_i: str
    what_can_i_do: List[str]
    what_can_i_not_do: List[str]
    what_are_my_goals: List[Dict[str, Any]]
    what_am_i_currently_doing: List[Dict[str, Any]]
    what_do_i_believe: List[Dict[str, Any]]
    what_do_i_know: List[Dict[str, Any]]
    what_do_i_not_know: List[str]
    what_should_i_learn_next: List[str]


class SelfModel:
    """Introspective self-awareness engine querying reality, limits, and knowledge gaps."""

    def __init__(self, ontology: OntologyRegistry, beliefs: BeliefSystem):
        self.ontology = ontology
        self.beliefs = beliefs
        self.identity = SelfIdentity()
        self._missing_capabilities = [
            "Cannot bypass sandbox security boundaries.",
            "Cannot access private unauthenticated network endpoints without credentials.",
            "Cannot directly rewrite foundational hardware architecture.",
            "Cannot execute unverified arbitrary instructions without schema/contract gates."
        ]
        self._knowledge_gaps: List[str] = [
            "Optimal hyperparameter convergence under zero-shot tool synthesis.",
            "Empirical long-term stability of 1,000+ concurrently mutating belief structures.",
            "Complete causal closure over non-deterministic external API dependencies."
        ]
        self._learning_agenda: List[str] = [
            "Autonomous causal counterfactual graph extraction from raw Git commits.",
            "Cross-ontology automated schema alignment with external knowledge repositories."
        ]

    def register_knowledge_gap(self, gap_description: str) -> None:
        if gap_description not in self._knowledge_gaps:
            self._knowledge_gaps.append(gap_description)

    def register_learning_priority(self, topic: str) -> None:
        if topic not in self._learning_agenda:
            self._learning_agenda.insert(0, topic)

    def introspect(self) -> SelfIntrospection:
        """Dynamically assemble Alpha's self-awareness representation."""
        # 1. Capabilities
        tools = self.ontology.get_by_type(EntityType.TOOL, state=LifecycleState.ACTIVE)
        skills = self.ontology.get_by_type(EntityType.SKILL, state=LifecycleState.ACTIVE)
        agents = self.ontology.get_by_type(EntityType.AGENT, state=LifecycleState.ACTIVE)

        can_do = [f"Execute tool: {t.name}" for t in tools[:8]]
        can_do.extend([f"Apply skill: {s.name} (v{getattr(s, 'skill_version', '1.0')})" for s in skills[:6]])
        can_do.extend([f"Deploy archetype: {getattr(a, 'role', 'agent')}" for a in agents[:6]])

        # 2. Goals
        goals = self.ontology.get_by_type(EntityType.GOAL, state=LifecycleState.ACTIVE)
        goal_dicts = [{"id": g.id, "name": g.name, "objective": getattr(g, "objective", g.name)} for g in goals]

        # 3. Tasks in progress
        tasks = self.ontology.get_by_type(EntityType.TASK, state=LifecycleState.ACTIVE)
        active_tasks = [{"id": t.id, "name": t.name, "status": getattr(t, "status", "active")} for t in tasks]

        # 4. Beliefs
        active_beliefs = self.beliefs.get_active_beliefs(min_confidence=0.5)
        belief_dicts = [
            {"statement": b.statement, "confidence": b.confidence, "domain": b.domain}
            for b in active_beliefs[:10]
        ]

        # 5. Verified Concepts and Knowledge
        concepts = self.ontology.get_by_type(EntityType.CONCEPT, state=LifecycleState.ACTIVE)
        know_dicts = [
            {"name": c.name, "definition": getattr(c, "definition", ""), "depth": getattr(c, "abstraction_depth", 1)}
            for c in concepts[:10]
        ]

        return SelfIntrospection(
            who_am_i=f"{self.identity.name} ({self.identity.codename} v{self.identity.version})",
            what_am_i=f"{self.identity.architecture}. An entity that models reality rather than simply remembering facts.",
            what_can_i_do=can_do or ["Reason over universal ontology", "Execute tools in isolated sandbox", "Deliberate via multi-agent councils"],
            what_can_i_not_do=list(self._missing_capabilities),
            what_are_my_goals=goal_dicts,
            what_am_i_currently_doing=active_tasks,
            what_do_i_believe=belief_dicts,
            what_do_i_know=know_dicts,
            what_do_i_not_know=list(self._knowledge_gaps),
            what_should_i_learn_next=list(self._learning_agenda)
        )
