"""Agent Runtime: Lifecycle Manager, Scheduler, State Manager, and Central Orchestrator."""

import concurrent.futures
import threading
import time
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from alpha.agents.communication.bus import AgentMessageBus
from alpha.agents.communication.context import SharedContextLayer
from alpha.agents.communication.messages import AgentMessage, MessageType, MessagePriority
from alpha.agents.core.base import BaseAgent, AgentRole, AgentStatus, AgentMetrics
from alpha.agents.core.registry import AgentRegistry

class StateTransitionRecord(BaseModel):
    agent_id: str
    old_status: AgentStatus
    new_status: AgentStatus
    reason: str
    timestamp: float = Field(default_factory=time.time)

class AgentStateManager:
    """Manages agent state lifecycles and auditable state transitions."""

    def __init__(self):
        self._history: List[StateTransitionRecord] = []
        self._lock = threading.RLock()

    def transition(self, agent: BaseAgent, new_status: AgentStatus, reason: str = "") -> None:
        with self._lock:
            old_status = agent.status
            agent.status = new_status
            record = StateTransitionRecord(
                agent_id=agent.agent_id,
                old_status=old_status,
                new_status=new_status,
                reason=reason
            )
            self._history.append(record)

    def get_history(self, agent_id: Optional[str] = None) -> List[StateTransitionRecord]:
        with self._lock:
            if agent_id:
                return [r for r in self._history if r.agent_id == agent_id]
            return list(self._history)

class AgentLifecycleManager:
    """Controls spawning, suspension, resumption, retirement, and versioning of agents."""

    def __init__(
        self,
        registry: AgentRegistry,
        bus: AgentMessageBus,
        shared_context: SharedContextLayer,
        state_manager: AgentStateManager
    ):
        self.registry = registry
        self.bus = bus
        self.shared_context = shared_context
        self.state_manager = state_manager
        self._lock = threading.RLock()

    def spawn(
        self,
        agent_factory: Type[BaseAgent],
        name: str,
        role: AgentRole,
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "",
        **kwargs: Any
    ) -> BaseAgent:
        """Spawn and initialize an agent into the society."""
        with self._lock:
            agent = agent_factory(
                name=name,
                role=role,
                version=version,
                capabilities=capabilities or [],
                primary_objective=primary_objective,
                **kwargs
            )
            mailbox = self.bus.register_agent(agent.agent_id, role.value)
            agent.attach_runtime(self.bus, mailbox, self.shared_context)
            self.registry.register(agent)
            self.state_manager.transition(agent, AgentStatus.IDLE, reason="Spawned by LifecycleManager")
            return agent

    def suspend(self, agent_id: str, reason: str = "Admin suspension") -> bool:
        with self._lock:
            agent = self.registry.get(agent_id)
            if not agent:
                return False
            self.state_manager.transition(agent, AgentStatus.SUSPENDED, reason=reason)
            agent.suspend()
            return True

    def resume(self, agent_id: str, reason: str = "Admin resumption") -> bool:
        with self._lock:
            agent = self.registry.get(agent_id)
            if not agent:
                return False
            self.state_manager.transition(agent, AgentStatus.IDLE, reason=reason)
            agent.resume()
            return True

    def retire(self, agent_id: str, reason: str = "Agent retired") -> bool:
        with self._lock:
            agent = self.registry.get(agent_id)
            if not agent:
                return False
            self.state_manager.transition(agent, AgentStatus.RETIRED, reason=reason)
            agent.retire()
            self.registry.unregister(agent_id)
            self.bus.unregister_agent(agent_id)
            return True

    def monitor(self, agent_id: str) -> Optional[Dict[str, Any]]:
        agent = self.registry.get(agent_id)
        if not agent:
            return None
        return {
            "agent_id": agent.agent_id,
            "name": agent.identity.name,
            "role": agent.role.value,
            "status": agent.status.value,
            "version": agent.identity.version,
            "generation": agent.identity.generation,
            "capabilities": agent.capabilities,
            "fitness_score": agent.metrics.fitness_score,
            "success_rate": agent.metrics.success_rate,
            "tasks_completed": agent.metrics.tasks_completed,
            "tasks_failed": agent.metrics.tasks_failed,
            "avg_latency_ms": agent.metrics.avg_latency_ms,
            "unread_messages": agent.mailbox.peek_unread_count() if agent.mailbox else 0,
        }

    def upgrade_version(self, agent_id: str, new_version: str) -> Optional[BaseAgent]:
        """Version an agent, creating a next-generation clone."""
        with self._lock:
            agent = self.registry.get(agent_id)
            if not agent:
                return None
            agent.identity.version = new_version
            agent.identity.generation += 1
            return agent

class AgentScheduler:
    """Dispatches tasks to the most suitable available agents."""

    def __init__(self, registry: AgentRegistry, state_manager: AgentStateManager, max_workers: int = 8):
        self.registry = registry
        self.state_manager = state_manager
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()

    def select_agent(
        self,
        role: Optional[AgentRole] = None,
        capability: Optional[str] = None
    ) -> Optional[BaseAgent]:
        """Select best candidate agent: must be IDLE, highest fitness score."""
        with self._lock:
            candidates: List[BaseAgent] = []
            if role:
                candidates = self.registry.get_by_role(role, status=AgentStatus.IDLE)
            elif capability:
                candidates = [
                    a for a in self.registry.get_by_capability(capability)
                    if a.status == AgentStatus.IDLE
                ]
            else:
                candidates = self.registry.get_all(status=AgentStatus.IDLE)

            if not candidates:
                return None
            # Sort by fitness descending
            candidates.sort(key=lambda a: a.metrics.fitness_score, reverse=True)
            return candidates[0]

    def execute_task(
        self,
        agent: BaseAgent,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchronously execute a task on an agent, updating state and metrics."""
        self.state_manager.transition(agent, AgentStatus.RUNNING, reason="Executing assigned task")
        t0 = time.perf_counter()
        success = False
        error_msg = ""
        result: Dict[str, Any] = {}
        try:
            result = agent.execute_task(task_context)
            success = bool(result.get("success", True))
        except Exception as e:
            success = False
            error_msg = str(e)
            result = {"success": False, "error": error_msg}
        finally:
            latency_ms = max(0.01, (time.perf_counter() - t0) * 1000.0)
            agent.record_execution(success=success, latency_ms=latency_ms, reward=1.0 if success else -0.5)
            new_status = AgentStatus.IDLE if agent.status != AgentStatus.RETIRED else AgentStatus.RETIRED
            self.state_manager.transition(agent, new_status, reason="Task execution completed")

        result["latency_ms"] = latency_ms
        return result

    def dispatch_async(
        self,
        agent: BaseAgent,
        task_context: Dict[str, Any]
    ) -> concurrent.futures.Future:
        """Asynchronously dispatch task on threadpool."""
        return self.executor.submit(self.execute_task, agent, task_context)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False)

class AgentRuntime:
    """Master operating system runtime managing the cognitive multi-agent society."""

    def __init__(self, max_workers: int = 8):
        self.bus = AgentMessageBus()
        self.shared_context = SharedContextLayer(context_id="society_root")
        self.registry = AgentRegistry()
        self.state_manager = AgentStateManager()
        self.lifecycle = AgentLifecycleManager(
            registry=self.registry,
            bus=self.bus,
            shared_context=self.shared_context,
            state_manager=self.state_manager
        )
        self.scheduler = AgentScheduler(
            registry=self.registry,
            state_manager=self.state_manager,
            max_workers=max_workers
        )

    def shutdown(self) -> None:
        self.scheduler.shutdown()
