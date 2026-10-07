"""Base architecture for Specialized Scientific Discovery Agents."""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class AgentActionLog(BaseModel):
    action_name: str
    target_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class ScientificAgentBase:
    """Foundational class for all discovery civilization agents."""

    def __init__(self, agent_id: Optional[str] = None, role_name: str = "ScientificAgent"):
        self.agent_id = agent_id or f"{role_name.lower()}_{uuid.uuid4().hex[:8]}"
        self.role_name = role_name
        self.action_history: List[AgentActionLog] = []
        self.reputation: float = 0.85
        self.created_at: float = time.time()

    def log_action(self, action_name: str, target_id: Optional[str] = None, **details: Any) -> AgentActionLog:
        log = AgentActionLog(
            action_name=action_name,
            target_id=target_id,
            details=details
        )
        self.action_history.append(log)
        return log
