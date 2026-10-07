"""Project Alpha: Autonomous Thought Engine (Phase 7F).

Executes continuous, self-directed cognitive reasoning cycles:
Perceive
  ↓
Evaluate Significance
  ↓
Generate Observation
  ↓
Update Workspace
  ↓
Generate Reflection
  ↓
Generate Improvement Suggestion
  ↓
Update Memory

Runs indefinitely in a background daemon thread without waiting for user prompts.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from alpha.core.perception import PerceptionBus, PerceptionEvent, PerceptionEventType
from alpha.core.awareness import AwarenessManager
from alpha.reflection.commentary import InternalCommentaryEngine

logger = logging.getLogger("alpha.core.autonomous_thought")


class AutonomousThoughtEngine:
    """Continuously active cognitive loop powering Alpha's autonomous mind."""

    def __init__(
        self,
        perception_bus: PerceptionBus,
        awareness_manager: AwarenessManager,
        commentary_engine: InternalCommentaryEngine,
        world_model: Optional[Any] = None,
        memory_storage: Optional[Any] = None,
        cycle_interval_seconds: float = 6.0
    ):
        self._lock = threading.RLock()
        self.perception_bus = perception_bus
        self.awareness_manager = awareness_manager
        self.commentary_engine = commentary_engine
        self.world_model = world_model
        self.memory_storage = memory_storage
        self.cycle_interval_seconds = cycle_interval_seconds

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._cycle_count = 0
        self._wake_event = threading.Event()
        self._last_cycle_record: Dict[str, Any] = {}

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        """Start the autonomous thought engine in a dedicated background runtime thread."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._wake_event.clear()
            self._thread = threading.Thread(
                target=self._continuous_thought_loop,
                name="AlphaCognitiveRuntime-AutonomousThought",
                daemon=True
            )
            self._thread.start()
            logger.info("AutonomousThoughtEngine launched in background runtime thread.")

    def stop(self) -> None:
        """Stop autonomous thought execution cleanly."""
        with self._lock:
            self._is_running = False
            self._wake_event.set()

    def run_single_cycle(self) -> Dict[str, Any]:
        """Execute a single atomic cognitive thought cycle (Perceive -> Reflect -> Commit)."""
        t_cycle_start = time.time()
        self._cycle_count += 1

        # 1. Perceive: Gather recent inputs
        recent_events = self.perception_bus.get_recent_events(limit=5)
        event_summaries = [f"[{e.event_type.value}] {e.title}" for e in recent_events]
        stimulus = "; ".join(event_summaries) if event_summaries else "Steady-state operational monitoring."

        # 2. Evaluate Significance
        max_sig = max([e.significance for e in recent_events], default=0.5)

        # 3. Generate Observation via Real Model Inference
        obs_record = self.commentary_engine.generate_observation(stimulus=stimulus)
        obs_statement = obs_record.get("statement", "")

        # 4. Update Workspace
        self.awareness_manager.record_observation(obs_statement)
        self.awareness_manager.update_focus(f"Reflecting on: {obs_statement[:50]}...")

        # 5. Generate Reflection via Real Model Inference
        refl_record = self.commentary_engine.generate_reflection(observation=obs_statement)
        insight = refl_record.get("insight", "")
        suggestion = refl_record.get("suggestion", "")

        # 6. Generate Improvement Suggestion & Update Workspace
        if suggestion:
            self.awareness_manager.record_hypothesis(suggestion)
            self.awareness_manager.record_pending_action(f"Evaluate: {suggestion[:60]}")

        # 7. Update Memory & World Model
        if self.world_model and hasattr(self.world_model, "record_evidence"):
            try:
                from alpha.world_model.epistemology.evidence import EvidencePolarity, EvidenceStrength
                self.world_model.record_evidence(
                    statement=f"Autonomous Reflection Cycle #{self._cycle_count}: {insight[:100]}",
                    polarity=EvidencePolarity.SUPPORTING,
                    strength=EvidenceStrength.MODERATE,
                    source_id=f"engine://autonomous_thought/{obs_record.get('id')}"
                )
            except Exception as ex:
                logger.warning(f"Could not commit reflection to world model: {ex}")

        cycle_data = {
            "cycle_number": self._cycle_count,
            "timestamp": time.time(),
            "duration_s": round(time.time() - t_cycle_start, 2),
            "stimulus": stimulus,
            "observation": obs_statement,
            "insight": insight,
            "suggestion": suggestion,
            "significance": max_sig
        }
        self._last_cycle_record = cycle_data

        # Notify perception bus of completed cognitive cycle
        self.perception_bus.publish(
            event_type=PerceptionEventType.TASK_COMPLETION,
            source="AutonomousThoughtEngine",
            title=f"Completed Cognitive Thought Cycle #{self._cycle_count}",
            data=cycle_data,
            significance=0.4
        )

        return cycle_data

    def _continuous_thought_loop(self) -> None:
        """Indefinite thought generation loop running on dedicated runtime thread."""
        logger.info("Autonomous thought loop active. Thinking continuously...")
        while self._is_running:
            try:
                self.run_single_cycle()
            except Exception as exc:
                logger.error(f"Error in autonomous thought cycle #{self._cycle_count}: {exc}", exc_info=True)
                if self.perception_bus:
                    self.perception_bus.publish(
                        event_type=PerceptionEventType.RUNTIME_ERROR,
                        source="AutonomousThoughtEngine",
                        title=f"Cycle Error: {str(exc)}",
                        data={"cycle": self._cycle_count, "error": str(exc)},
                        significance=0.8
                    )

            # Wait for next interval or early wakeup
            self._wake_event.wait(timeout=self.cycle_interval_seconds)
            self._wake_event.clear()
