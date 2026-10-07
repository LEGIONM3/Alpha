"""Agent Registry: Catalog of all agents, indexing by role, capabilities, and version."""

import threading
from typing import Dict, List, Optional
from alpha.agents.core.base import BaseAgent, AgentRole, AgentStatus

class AgentRegistry:
    """Catalog and discovery directory for agents across the cognitive civilization."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._by_role: Dict[AgentRole, List[str]] = {}
        self._by_name: Dict[str, List[str]] = {}
        self._lock = threading.RLock()

    def register(self, agent: BaseAgent) -> None:
        """Register an agent into the directory."""
        with self._lock:
            self._agents[agent.agent_id] = agent
            role = agent.role
            if role not in self._by_role:
                self._by_role[role] = []
            if agent.agent_id not in self._by_role[role]:
                self._by_role[role].append(agent.agent_id)

            name = agent.identity.name
            if name not in self._by_name:
                self._by_name[name] = []
            if agent.agent_id not in self._by_name[name]:
                self._by_name[name].append(agent.agent_id)

    def unregister(self, agent_id: str) -> Optional[BaseAgent]:
        """Remove agent from directory."""
        with self._lock:
            agent = self._agents.pop(agent_id, None)
            if agent:
                if agent.role in self._by_role and agent_id in self._by_role[agent.role]:
                    self._by_role[agent.role].remove(agent_id)
                if agent.identity.name in self._by_name and agent_id in self._by_name[agent.identity.name]:
                    self._by_name[agent.identity.name].remove(agent_id)
            return agent

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        with self._lock:
            return self._agents.get(agent_id)

    def get_by_role(self, role: AgentRole, status: Optional[AgentStatus] = None) -> List[BaseAgent]:
        with self._lock:
            ids = self._by_role.get(role, [])
            agents = [self._agents[aid] for aid in ids if aid in self._agents]
            if status:
                agents = [a for a in agents if a.status == status]
            return agents

    def get_by_capability(self, capability: str) -> List[BaseAgent]:
        with self._lock:
            return [
                a for a in self._agents.values()
                if capability in a.capabilities
            ]

    def get_all(self, status: Optional[AgentStatus] = None) -> List[BaseAgent]:
        with self._lock:
            agents = list(self._agents.values())
            if status:
                agents = [a for a in agents if a.status == status]
            return agents

    def count(self) -> int:
        with self._lock:
            return len(self._agents)
