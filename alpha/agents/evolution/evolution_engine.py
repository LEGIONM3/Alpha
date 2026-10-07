"""Agent Evolution: Performance Tracking, Ranking, Evolution Proposals, and Lifecycle Mutation."""

import threading
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.agents.core.runtime import AgentRuntime
from alpha.agents.core.base import BaseAgent, AgentStatus

class EvolutionActionType(str, Enum):
    IMPROVE = "improve"
    MERGE = "merge"
    REPLACE = "replace"
    RETIRE = "retire"

class AgentRankEntry(BaseModel):
    agent_id: str
    name: str
    role: str
    fitness_score: float
    success_rate: float
    tasks_completed: int
    tasks_failed: int
    rank: int

class ImprovementProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_agent_id: str
    action_type: EvolutionActionType
    rationale: str
    proposed_modifications: Dict[str, Any] = Field(default_factory=dict)
    secondary_agent_id: Optional[str] = None
    status: str = "PENDING"  # "PENDING", "APPROVED", "EXECUTED", "REJECTED"
    created_at: float = Field(default_factory=time.time)

class AgentEvolutionEngine:
    """Monitors fitness across society, generates evolution proposals, and retires underperformers."""

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.proposals: Dict[str, ImprovementProposal] = {}
        self._lock = threading.RLock()

    def rank_society(self) -> List[AgentRankEntry]:
        """Rank all active agents in the society by fitness score."""
        with self._lock:
            agents = self.runtime.registry.get_all()
            # Sort by fitness descending
            agents.sort(key=lambda a: a.metrics.fitness_score, reverse=True)
            leaderboard = []
            for idx, a in enumerate(agents, start=1):
                leaderboard.append(AgentRankEntry(
                    agent_id=a.agent_id,
                    name=a.identity.name,
                    role=a.role.value,
                    fitness_score=round(a.metrics.fitness_score, 2),
                    success_rate=round(a.metrics.success_rate, 3),
                    tasks_completed=a.metrics.tasks_completed,
                    tasks_failed=a.metrics.tasks_failed,
                    rank=idx
                ))
            return leaderboard

    def scan_for_underperformers(self, fitness_threshold: float = 60.0) -> List[ImprovementProposal]:
        """Scan society for underperforming agents and generate actionable evolution proposals."""
        with self._lock:
            proposals = []
            for agent in self.runtime.registry.get_all():
                if agent.status == AgentStatus.RETIRED:
                    continue
                # If agent has completed tasks and fitness is below threshold, propose action
                if agent.metrics.tasks_assigned >= 2 and agent.metrics.fitness_score < fitness_threshold:
                    if agent.metrics.consecutive_failures >= 3:
                        action = EvolutionActionType.RETIRE
                        rationale = f"Agent {agent.identity.name} has 3+ consecutive failures. Fitness score: {agent.metrics.fitness_score}."
                    elif agent.metrics.success_rate < 0.5:
                        action = EvolutionActionType.REPLACE
                        rationale = f"Agent {agent.identity.name} success rate is below 50%. Recommend replacing with Generation {agent.identity.generation + 1}."
                    else:
                        action = EvolutionActionType.IMPROVE
                        rationale = f"Agent {agent.identity.name} underperforming. Recommend capability expansion and prompt optimization."

                    prop = ImprovementProposal(
                        target_agent_id=agent.agent_id,
                        action_type=action,
                        rationale=rationale,
                        proposed_modifications={"boost_capabilities": ["heuristic_caching"]}
                    )
                    self.proposals[prop.proposal_id] = prop
                    proposals.append(prop)
            return proposals

    def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Execute approved evolution proposal on the agent runtime."""
        with self._lock:
            prop = self.proposals.get(proposal_id)
            if not prop:
                return {"success": False, "error": "Proposal not found"}

            agent = self.runtime.registry.get(prop.target_agent_id)
            if not agent:
                return {"success": False, "error": "Target agent not found"}

            result_summary = {}

            if prop.action_type == EvolutionActionType.IMPROVE:
                # Add new capabilities
                new_caps = prop.proposed_modifications.get("boost_capabilities", [])
                for c in new_caps:
                    if c not in agent.capabilities:
                        agent.capabilities.append(c)
                # Reset consecutive failure counter
                agent.metrics.consecutive_failures = 0
                result_summary = {"action": "IMPROVED", "agent_id": agent.agent_id, "capabilities": agent.capabilities}

            elif prop.action_type == EvolutionActionType.REPLACE:
                # Spawn replacement agent of same class with upgraded version
                from alpha.agents.types import ROLE_TO_CLASS_MAP
                cls = ROLE_TO_CLASS_MAP.get(agent.role)
                if cls:
                    new_agent = self.runtime.lifecycle.spawn(
                        cls,
                        name=f"{agent.identity.name}_v{agent.identity.generation + 1}",
                        role=agent.role,
                        version=f"2.0.{agent.identity.generation}",
                        capabilities=list(set(agent.capabilities + prop.proposed_modifications.get("boost_capabilities", [])))
                    )
                    new_agent.identity.generation = agent.identity.generation + 1
                    # Retire old agent
                    self.runtime.lifecycle.retire(agent.agent_id, reason="Replaced by upgraded generation")
                    result_summary = {"action": "REPLACED", "old_id": agent.agent_id, "new_id": new_agent.agent_id}

            elif prop.action_type == EvolutionActionType.RETIRE:
                self.runtime.lifecycle.retire(agent.agent_id, reason=prop.rationale)
                result_summary = {"action": "RETIRED", "agent_id": agent.agent_id}

            elif prop.action_type == EvolutionActionType.MERGE:
                # Combine capabilities into primary agent and retire secondary
                if prop.secondary_agent_id:
                    sec_agent = self.runtime.registry.get(prop.secondary_agent_id)
                    if sec_agent:
                        agent.capabilities = list(set(agent.capabilities + sec_agent.capabilities))
                        self.runtime.lifecycle.retire(sec_agent.agent_id, reason="Merged into primary agent")
                result_summary = {"action": "MERGED", "primary_id": agent.agent_id}

            prop.status = "EXECUTED"
            return {"success": True, "proposal_id": proposal_id, "details": result_summary}
