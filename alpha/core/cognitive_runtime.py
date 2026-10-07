"""Project Alpha: Unified Persistent Cognitive Runtime.

Central background coordinator orchestrating:
- PerceptionBus
- AwarenessManager
- InternalCommentaryEngine
- AutonomousThoughtEngine
- SelfMonitoringAgent
- GroundingMonitor
- DevelopmentSupervisorAgent
- RealityValidator

Runs independently of any UI or console process.
TCC attaches as a visualization subscriber only.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from alpha.core.perception import PerceptionBus, PerceptionEvent, PerceptionEventType
from alpha.core.awareness import AwarenessManager, AwarenessState
from alpha.reflection.commentary import InternalCommentaryEngine
from alpha.core.autonomous_thought import AutonomousThoughtEngine
from alpha.agents.self_monitoring import SelfMonitoringAgent
from alpha.verification.grounding_monitor import GroundingMonitor
from alpha.agents.development_supervisor import DevelopmentSupervisorAgent
from alpha.verification.reality_validator import RealityValidator
from alpha.model_intelligence.connector.client import OpenAICompatibleClient
from alpha.memory.embedding_service import EmbeddingService
from alpha.core.continuation import MissionExecutor

logger = logging.getLogger("alpha.core.cognitive_runtime")


class CognitiveRuntime:
    """Master persistent cognitive operating system daemon."""

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        identity_path: str = "alpha_identity.md",
        model_url: str = "http://localhost:1234/v1",
        default_model: str = "gemma-4-e4b-it-ultra-uncensored-heretic",
        embedding_model: str = "text-embedding-nomic-embed-text-v1.5",
        thought_interval_seconds: float = 6.0
    ):
        self._lock = threading.RLock()
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.identity_path = identity_path
        self.model_url = model_url.rstrip("/")
        self.default_model = default_model
        self.embedding_model = embedding_model
        self.boot_time = time.time()
        self._is_running = False

        # 1. Model Client & Embedding Service
        self.model_client = OpenAICompatibleClient(
            base_url=self.model_url,
            default_model=self.default_model,
            timeout_seconds=40.0,
            enable_mock_fallback=False
        )
        self.embedding_service = EmbeddingService(
            endpoint_url=self.model_url,
            model_name=self.embedding_model
        )

        # 2. Perception Bus
        self.perception_bus = PerceptionBus(workspace_root=self.workspace_root)

        # 3. Awareness Manager & Conscious Workspace
        self.awareness_manager = AwarenessManager(
            perception_bus=self.perception_bus,
            workspace_file=self.workspace_root / "ACTIVE_COGNITIVE_STATE.json",
            identity_path=self.identity_path
        )

        # 4. Commentary Engine
        self.commentary_engine = InternalCommentaryEngine(
            model_client=self.model_client,
            perception_bus=self.perception_bus,
            thought_log_path=str(self.workspace_root / "thought_log.jsonl"),
            reflection_log_path=str(self.workspace_root / "reflection_log.jsonl"),
            observation_log_path=str(self.workspace_root / "observation_log.jsonl")
        )

        # 5. Autonomous Thought Engine
        self.thought_engine = AutonomousThoughtEngine(
            perception_bus=self.perception_bus,
            awareness_manager=self.awareness_manager,
            commentary_engine=self.commentary_engine,
            cycle_interval_seconds=thought_interval_seconds
        )

        # 6. Self Monitoring Agent
        self.monitoring_agent = SelfMonitoringAgent(
            perception_bus=self.perception_bus,
            embedding_service=self.embedding_service,
            report_path=str(self.workspace_root / "self_monitoring_report.json")
        )

        # 7. Epistemic Grounding Monitor
        self.grounding_monitor = GroundingMonitor(
            perception_bus=self.perception_bus
        )

        # 8. Development Supervisor Agent
        self.supervisor_agent = DevelopmentSupervisorAgent(
            perception_bus=self.perception_bus,
            awareness_manager=self.awareness_manager,
            model_client=self.model_client
        )

        # 9. Reality Validator
        self.reality_validator = RealityValidator(workspace_root=self.workspace_root)

        # 10. Autonomous Continuation Layer (MissionExecutor)
        self.mission_executor = MissionExecutor(
            workspace_root=self.workspace_root,
            perception_bus=self.perception_bus,
            awareness_manager=self.awareness_manager,
            model_url=self.model_url,
            default_model=self.default_model
        )

        # UI Subscription Queues
        self._ui_queues: List[queue.Queue] = []

    def start(self) -> None:
        """Start all persistent cognitive subsystems."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            logger.info("Starting Persistent Cognitive Runtime...")

            # Start components in sequence
            self.perception_bus.start()
            self.thought_engine.start()
            self.monitoring_agent.start()
            self.grounding_monitor.start()
            self.supervisor_agent.start()
            self.mission_executor.start()

            # Initial reality audit
            try:
                self.reality_validator.generate_report_markdown()
            except Exception as ex:
                logger.warning(f"RealityValidator initial run warning: {ex}")

            logger.info("All cognitive runtime systems online and operating autonomously.")

    def stop(self) -> None:
        """Stop all background cognitive threads."""
        with self._lock:
            self._is_running = False
            self.mission_executor.stop()
            self.thought_engine.stop()
            self.monitoring_agent.stop()
            self.grounding_monitor.stop()
            self.supervisor_agent.stop()
            self.perception_bus.stop()
            logger.info("Cognitive runtime stopped cleanly.")

    def attach_ui_queue(self, q: queue.Queue) -> None:
        """Register a thread-safe queue for a visualization client."""
        with self._lock:
            self._ui_queues.append(q)
            self.perception_bus.subscribe(lambda event: q.put_nowait(event))

    def get_live_cognitive_feed(self) -> Dict[str, Any]:
        """Provides real-time cognitive snapshot for TCC and telemetry displays."""
        with self._lock:
            ws = self.awareness_manager.read_workspace()
            concerns = ws.get("active_concerns", [])
            hypotheses = ws.get("active_hypotheses", [])
            primary_concern = concerns[0] if concerns else "None (nominal operation)"
            primary_suggestion = hypotheses[0] if hypotheses else "Maintain continuous cognitive grounding."

            feed = {
                "current_thought": self.commentary_engine.latest_thought,
                "current_observation": self.commentary_engine.latest_observation,
                "current_reflection": self.commentary_engine.latest_reflection,
                "current_concern": primary_concern,
                "current_goal": ws.get("current_goal", ""),
                "current_suggestion": primary_suggestion,
                "current_risk": primary_concern,
                "current_confidence": 0.94,
                "current_mission": self.awareness_manager.what_is_my_mission(),
                "current_self_assessment": ws.get("self_assessment", ""),
                "current_target": self.mission_executor.state.current_target,
                "next_planned_action": self.mission_executor.state.next_planned_action,
                "investigations_completed": self.mission_executor.state.investigations_completed,
                "cycle_count": self.thought_engine.cycle_count,
                "runtime_uptime_s": round(time.time() - self.boot_time, 1)
            }
            return feed
