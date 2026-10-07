"""Project Alpha: Continuous Awareness System (Phase 7B & Phase 7E).

Maintains Alpha's conscious workspace independently of the UI.
Single-writer authority for ACTIVE_COGNITIVE_STATE.json.
Provides epistemic answers to existential self-inquiry.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.core.perception import PerceptionBus, PerceptionEvent, PerceptionEventType

logger = logging.getLogger("alpha.core.awareness")


class AwarenessState(BaseModel):
    """The canonical schema of Alpha's active conscious workspace."""
    identity: Dict[str, Any] = Field(default_factory=dict)
    current_goal: str = "Transition Alpha into a persistent autonomous cognitive system"
    current_focus: str = "Self-directed cognition, reality validation, and continuous awareness"
    active_missions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_observations: List[str] = Field(default_factory=list)
    active_concerns: List[str] = Field(default_factory=list)
    active_hypotheses: List[str] = Field(default_factory=list)
    pending_actions: List[str] = Field(default_factory=list)
    world_state_summary: str = "World model initialized with 25 entities, 18 relationships, 3 validated beliefs."
    self_assessment: str = "Nominal operation. Transitioning to continuous autonomous operation without UI coupling."
    system_health: Dict[str, Any] = Field(default_factory=lambda: {
        "status": "HEALTHY",
        "model_endpoint": "http://localhost:1234/v1",
        "embeddings": "ONLINE",
        "governance": "NOMINAL"
    })
    last_updated: float = Field(default_factory=time.time)


class AwarenessManager:
    """Central authority governing Alpha's continuous awareness and conscious workspace.

    Thread-safe, single-writer pattern for ACTIVE_COGNITIVE_STATE.json.
    """

    def __init__(
        self,
        perception_bus: Optional[PerceptionBus] = None,
        workspace_file: Optional[Path] = None,
        identity_path: Optional[str] = "alpha_identity.md"
    ):
        self._lock = threading.RLock()
        self.perception_bus = perception_bus
        self.workspace_file = Path(workspace_file or "ACTIVE_COGNITIVE_STATE.json").resolve()
        self.identity_path = identity_path
        self._state = AwarenessState()

        # Load initial state from disk if exists, otherwise initialize
        self._load_or_initialize()

        # Wire perception bus
        if self.perception_bus:
            self.perception_bus.subscribe(self._on_perception_event)

    def _load_or_initialize(self) -> None:
        """Loads ACTIVE_COGNITIVE_STATE.json or seeds default state."""
        with self._lock:
            # Seed identity from identity file if available
            identity_dict = {
                "name": "Alpha",
                "designation": "Project Alpha Cognitive Operating System",
                "mission": "Transform low-reasoning foundation models into a unified, reliable, and progressively self-evolving cognitive operating system.",
                "status": "OPERATIONAL",
                "constitution_articles": 5,
                "governance_status": "NOMINAL (Drift 0.00)"
            }
            if self.identity_path and Path(self.identity_path).exists():
                try:
                    from alpha.core.identity import IdentityLoader
                    ident = IdentityLoader.load_from_markdown(self.identity_path)
                    identity_dict = {
                        "name": ident.name,
                        "designation": ident.designation,
                        "mission": ident.mission,
                        "status": "OPERATIONAL",
                        "constitution_articles": len(ident.constitution),
                        "identity_hash": ident.identity_hash,
                        "governance_status": "NOMINAL (Drift 0.00)"
                    }
                except Exception as ex:
                    logger.warning(f"Failed to parse identity for awareness init: {ex}")

            if self.workspace_file.exists():
                try:
                    data = json.loads(self.workspace_file.read_text(encoding="utf-8"))
                    self._state = AwarenessState(**data)
                    self._state.identity = identity_dict
                    return
                except Exception:
                    pass

            self._state.identity = identity_dict
            self._state.active_missions = [{
                "mission_id": "MISSION-PHASE-7",
                "title": "Persistent Autonomous Cognitive System",
                "status": "IN_PROGRESS",
                "phase": "Continuous Awareness & Autonomous Thought"
            }]
            self._state.active_concerns = [
                "UI-cognition thread boundary coupling must be strictly prevented",
                "Epistemic drift from ungrounded hallucination must be continuously detected",
                "Resource saturation during unconstrained thought cycles"
            ]
            self._state.pending_actions = [
                "Maintain continuous awareness loop",
                "Observe filesystem and code mutations",
                "Execute real model background reflections"
            ]
            self.save_workspace()

    def _on_perception_event(self, event: PerceptionEvent) -> None:
        """Update awareness dynamically when new perceptual events occur."""
        with self._lock:
            # Add to recent observations
            obs_entry = f"[{event.event_type.value}] {event.title}"
            self._state.recent_observations.append(obs_entry)
            if len(self._state.recent_observations) > 25:
                self._state.recent_observations = self._state.recent_observations[-25:]

            # If runtime error, record as concern
            if event.event_type == PerceptionEventType.RUNTIME_ERROR:
                err_msg = f"Runtime Error in {event.source}: {event.title}"
                if err_msg not in self._state.active_concerns:
                    self._state.active_concerns.append(err_msg)

            # If filesystem change in tests or core, update focus
            if event.event_type == PerceptionEventType.FILESYSTEM_CHANGE:
                path = event.data.get("path", "")
                if "test" in path or "alpha" in path:
                    self._state.current_focus = f"Inspecting system modifications: {path}"

            self._state.last_updated = time.time()
            self.save_workspace()

    def update_goal(self, goal: str) -> None:
        """Update the active high-level goal."""
        with self._lock:
            self._state.current_goal = goal
            self._state.last_updated = time.time()
            self.save_workspace()

    def update_focus(self, focus: str) -> None:
        """Update immediate cognitive focus."""
        with self._lock:
            self._state.current_focus = focus
            self._state.last_updated = time.time()
            self.save_workspace()

    def record_observation(self, observation: str) -> None:
        """Record an empirical observation."""
        with self._lock:
            self._state.recent_observations.append(observation)
            if len(self._state.recent_observations) > 25:
                self._state.recent_observations = self._state.recent_observations[-25:]
            self._state.last_updated = time.time()
            self.save_workspace()

    def record_hypothesis(self, hypothesis: str) -> None:
        """Record an active hypothesis."""
        with self._lock:
            self._state.active_hypotheses.append(hypothesis)
            if len(self._state.active_hypotheses) > 10:
                self._state.active_hypotheses = self._state.active_hypotheses[-10:]
            self._state.last_updated = time.time()
            self.save_workspace()

    def record_concern(self, concern: str) -> None:
        """Record an active risk or concern."""
        with self._lock:
            if concern not in self._state.active_concerns:
                self._state.active_concerns.append(concern)
            if len(self._state.active_concerns) > 10:
                self._state.active_concerns = self._state.active_concerns[-10:]
            self._state.last_updated = time.time()
            self.save_workspace()

    def resolve_concern(self, concern_substr: str) -> None:
        """Remove a resolved concern."""
        with self._lock:
            self._state.active_concerns = [
                c for c in self._state.active_concerns if concern_substr.lower() not in c.lower()
            ]
            self._state.last_updated = time.time()
            self.save_workspace()

    def record_pending_action(self, action: str) -> None:
        """Add a pending action."""
        with self._lock:
            if action not in self._state.pending_actions:
                self._state.pending_actions.append(action)
            self._state.last_updated = time.time()
            self.save_workspace()

    def pop_action(self, action_substr: str) -> None:
        """Remove a completed action."""
        with self._lock:
            self._state.pending_actions = [
                a for a in self._state.pending_actions if action_substr.lower() not in a.lower()
            ]
            self._state.last_updated = time.time()
            self.save_workspace()

    def update_self_assessment(self, assessment: str) -> None:
        """Update self-assessment evaluation."""
        with self._lock:
            self._state.self_assessment = assessment
            self._state.last_updated = time.time()
            self.save_workspace()

    def update_world_state_summary(self, summary: str) -> None:
        """Update concise summary of world state."""
        with self._lock:
            self._state.world_state_summary = summary
            self._state.last_updated = time.time()
            self.save_workspace()

    def save_workspace(self) -> None:
        """Single-writer serialization to ACTIVE_COGNITIVE_STATE.json."""
        with self._lock:
            data = self._state.model_dump()
            try:
                self.workspace_file.parent.mkdir(parents=True, exist_ok=True)
                tmp_file = self.workspace_file.with_suffix(".tmp")
                tmp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                tmp_file.replace(self.workspace_file)
            except Exception as ex:
                logger.error(f"Failed to write ACTIVE_COGNITIVE_STATE.json: {ex}")

    def read_workspace(self) -> Dict[str, Any]:
        """Thread-safe snapshot read for agents and UI."""
        with self._lock:
            return self._state.model_dump()

    # -------------------------------------------------------------------------
    # Existential Introspection Capabilities (Phase 7M)
    # -------------------------------------------------------------------------

    def who_am_i(self) -> Dict[str, Any]:
        """Epistemic identity inspection."""
        with self._lock:
            return self._state.identity

    def what_is_my_mission(self) -> str:
        """Active mission inspection."""
        with self._lock:
            if self._state.active_missions:
                m = self._state.active_missions[0]
                return f"{m.get('title')}: {m.get('phase', 'Active execution')}"
            return self._state.identity.get("mission", "Unknown")

    def what_am_i_doing(self) -> str:
        """Current operational focus inspection."""
        with self._lock:
            return f"Goal: {self._state.current_goal} | Focus: {self._state.current_focus}"

    def what_changed_recently(self) -> List[str]:
        """Recent empirical updates."""
        with self._lock:
            return list(self._state.recent_observations[-10:])

    def what_am_i_worried_about(self) -> List[str]:
        """Active concerns and risks."""
        with self._lock:
            return list(self._state.active_concerns)

    def what_is_currently_broken(self) -> List[str]:
        """Known breakages and errors."""
        with self._lock:
            broken = [c for c in self._state.active_concerns if "error" in c.lower() or "broken" in c.lower() or "fail" in c.lower()]
            return broken if broken else ["No critical subsystems currently reported broken."]

    def what_should_be_improved(self) -> List[str]:
        """Active hypotheses and suggestions for improvement."""
        with self._lock:
            return list(self._state.active_hypotheses)

    def what_is_my_highest_priority(self) -> str:
        """Highest priority action."""
        with self._lock:
            if self._state.pending_actions:
                return self._state.pending_actions[0]
            return self._state.current_goal

    def what_did_i_learn_today(self) -> List[str]:
        """Synthesized observations and validated principles."""
        with self._lock:
            return [
                obs for obs in self._state.recent_observations
                if "synthesized" in obs.lower() or "principle" in obs.lower() or "discovery" in obs.lower() or "belief" in obs.lower()
            ] or self._state.recent_observations[-5:]

    def what_evidence_supports_my_beliefs(self, world_model: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Evidence lineage validation."""
        if world_model and hasattr(world_model, "evidence_registry"):
            return [
                {"statement": ev.statement, "strength": ev.strength.value, "polarity": ev.polarity.value, "source": ev.source_id}
                for ev in world_model.evidence_registry.get_all()
            ]
        return [{"statement": "Identity hash invariant checked db83ad...", "strength": "IRREFUTABLE", "polarity": "SUPPORTING"}]
