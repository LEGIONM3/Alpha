"""Core Agent Model: Identity, Role, Memory, Capabilities, Objectives, Performance Metrics."""

import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.agents.communication.messages import AgentMessage, MessageType, MessagePriority
from alpha.agents.communication.mailbox import AgentMailbox
from alpha.agents.communication.bus import AgentMessageBus
from alpha.agents.communication.context import SharedContextLayer

class AgentStatus(str, Enum):
    SPAWNED = "spawned"
    IDLE = "idle"
    RUNNING = "running"
    SUSPENDED = "suspended"
    RETIRED = "retired"
    ERROR = "error"

class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    PLANNER = "planner"
    ARCHITECT = "architect"
    BUILDER = "builder"
    CODER = "coder"
    TESTER = "tester"
    VALIDATOR = "validator"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    OPTIMIZER = "optimizer"
    ANALYTICS = "analytics"
    DOCUMENTER = "documenter"
    SECURITY = "security"
    RISK = "risk"
    CRITIC = "critic"
    REFLECTOR = "reflector"
    META_LEARNER = "meta_learner"
    DIRECTOR = "director"

class AgentIdentity(BaseModel):
    """Immutable & versioned identity of an agent in the society."""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: AgentRole
    version: str = "1.0.0"
    generation: int = 1
    created_at: float = Field(default_factory=time.time)
    parent_agent_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class AgentObjectives(BaseModel):
    """Target goals and priority objectives of an agent."""
    primary_objective: str = ""
    active_goals: List[str] = Field(default_factory=list)
    completed_goals: List[str] = Field(default_factory=list)

class AgentMetrics(BaseModel):
    """Real-time performance tracking and fitness scoring."""
    tasks_assigned: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_latency_ms: float = 0.0
    accumulated_reward: float = 0.0
    consecutive_failures: int = 0
    last_active_at: float = Field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        if self.tasks_assigned == 0:
            return 1.0
        return self.tasks_completed / self.tasks_assigned

    @property
    def avg_latency_ms(self) -> float:
        if self.tasks_completed == 0:
            return 0.0
        return self.total_latency_ms / self.tasks_completed

    @property
    def fitness_score(self) -> float:
        """Composite fitness score: rewards success rate, penalizes failure streaks."""
        base = self.success_rate * 100.0
        reward_factor = max(0.0, self.accumulated_reward * 2.0)
        penalty = self.consecutive_failures * 15.0
        return max(0.0, base + reward_factor - penalty)

class PrivateAgentMemory:
    """Private cognitive workspace for an agent."""

    def __init__(self, agent_id: str, max_short_term: int = 100):
        self.agent_id = agent_id
        self.max_short_term = max_short_term
        self.working_memory: Dict[str, Any] = {}
        self.short_term_log: List[Dict[str, Any]] = []
        self.episodic_records: List[Dict[str, Any]] = []

    def set_working(self, key: str, value: Any) -> None:
        self.working_memory[key] = value

    def get_working(self, key: str, default: Any = None) -> Any:
        return self.working_memory.get(key, default)

    def log_interaction(self, event_type: str, details: Dict[str, Any]) -> None:
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "details": details
        }
        self.short_term_log.append(entry)
        if len(self.short_term_log) > self.max_short_term:
            self.short_term_log.pop(0)

    def record_episode(self, task: str, result: Dict[str, Any], success: bool) -> None:
        self.episodic_records.append({
            "timestamp": time.time(),
            "task": task,
            "result": result,
            "success": success
        })

class BaseAgent(ABC):
    """Abstract Cognitive Agent Base Class."""

    def __init__(
        self,
        name: str,
        role: AgentRole,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = ""
    ):
        self.identity = AgentIdentity(name=name, role=role, version=version)
        self.status = AgentStatus.SPAWNED
        self.capabilities = capabilities or []
        self.objectives = AgentObjectives(primary_objective=primary_objective)
        self.metrics = AgentMetrics()
        self.memory = PrivateAgentMemory(agent_id=self.identity.agent_id)

        self.bus: Optional[AgentMessageBus] = None
        self.mailbox: Optional[AgentMailbox] = None
        self.shared_context: Optional[SharedContextLayer] = None

    @property
    def agent_id(self) -> str:
        return self.identity.agent_id

    @property
    def role(self) -> AgentRole:
        return self.identity.role

    def attach_runtime(
        self,
        bus: AgentMessageBus,
        mailbox: AgentMailbox,
        shared_context: Optional[SharedContextLayer] = None
    ) -> None:
        """Attach agent to communication bus and runtime environment."""
        self.bus = bus
        self.mailbox = mailbox
        self.shared_context = shared_context
        self.status = AgentStatus.IDLE

    def send_message(
        self,
        recipient_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        trace_id: Optional[str] = None
    ) -> AgentMessage:
        """Construct and send a message through the bus."""
        if not self.bus:
            raise RuntimeError(f"Agent {self.identity.name} is not connected to a message bus")
        msg = AgentMessage(
            sender_id=self.agent_id,
            sender_role=self.role.value,
            recipient_id=recipient_id,
            message_type=message_type,
            priority=priority,
            payload=payload,
            trace_id=trace_id or str(uuid.uuid4())
        )
        self.bus.send(msg)
        return msg

    def broadcast_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        role_filter: Optional[str] = None
    ) -> int:
        if not self.bus:
            raise RuntimeError(f"Agent {self.identity.name} is not connected to a message bus")
        msg = AgentMessage(
            sender_id=self.agent_id,
            sender_role=self.role.value,
            recipient_id="*",
            message_type=message_type,
            payload=payload
        )
        return self.bus.broadcast(msg, role_filter=role_filter)

    def receive_next_message(self, block: bool = False, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        if not self.mailbox:
            return None
        return self.mailbox.pop_next(block=block, timeout=timeout)

    def record_execution(self, success: bool, latency_ms: float, reward: float = 1.0) -> None:
        """Update metrics upon completing or failing a task."""
        self.metrics.tasks_assigned += 1
        if success:
            self.metrics.tasks_completed += 1
            self.metrics.consecutive_failures = 0
            self.metrics.accumulated_reward += reward
        else:
            self.metrics.tasks_failed += 1
            self.metrics.consecutive_failures += 1
            self.metrics.accumulated_reward -= 0.5
        self.metrics.total_latency_ms += latency_ms
        self.metrics.last_active_at = time.time()

    def suspend(self) -> None:
        self.status = AgentStatus.SUSPENDED

    def resume(self) -> None:
        if self.status != AgentStatus.RETIRED:
            self.status = AgentStatus.IDLE

    def retire(self) -> None:
        self.status = AgentStatus.RETIRED

    @abstractmethod
    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a cognitive assignment and return structured results."""
        pass
