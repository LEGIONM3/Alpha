"""World State Engine: Current, Historical, Future, and Simulated world states.

Part 6: World State Engine
Tracks: Agents, Projects, Tasks, Goals, Tools, Skills, Documents, Resources, Risks, Capabilities, Beliefs, Predictions.
Supports: Current State, Historical State, Future State, Simulated State.
"""

from __future__ import annotations

import copy
import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.world_model.ontology.registry import OntologyRegistry
from alpha.world_model.ontology.entities import (
    EntityType,
    LifecycleState,
    AgentEntity,
    ProjectEntity,
    TaskEntity,
    GoalEntity,
    ToolEntity,
    SkillEntity,
    DocumentEntity,
    ResourceEntity,
    RiskEntity,
    CapabilityEntity,
    BeliefEntity,
    PredictionEntity,
)
from alpha.world_model.epistemology.belief import BeliefSystem


class WorldStateSnapshot(BaseModel):
    """Snapshot encompassing all 12 universal cognitive entity collections."""
    timestamp: float = Field(default_factory=time.time)
    state_mode: str = "current"  # current, historical, future, simulated
    state_id: str = "snapshot"

    agents: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    goals: List[Dict[str, Any]] = Field(default_factory=list)
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[Dict[str, Any]] = Field(default_factory=list)
    capabilities: List[Dict[str, Any]] = Field(default_factory=list)
    beliefs: List[Dict[str, Any]] = Field(default_factory=list)
    predictions: List[Dict[str, Any]] = Field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "mode": self.state_mode,
            "agent_count": len(self.agents),
            "project_count": len(self.projects),
            "task_count": len(self.tasks),
            "goal_count": len(self.goals),
            "tool_count": len(self.tools),
            "skill_count": len(self.skills),
            "document_count": len(self.documents),
            "resource_count": len(self.resources),
            "risk_count": len(self.risks),
            "capability_count": len(self.capabilities),
            "belief_count": len(self.beliefs),
            "prediction_count": len(self.predictions),
        }


class WorldStateEngine:
    """Orchestrates multi-temporal and simulated representations of reality."""

    def __init__(self, ontology: OntologyRegistry, beliefs: BeliefSystem):
        self.ontology = ontology
        self.beliefs = beliefs
        self._history: List[WorldStateSnapshot] = []
        self._simulations: Dict[str, WorldStateSnapshot] = {}

    def get_current_state(self) -> WorldStateSnapshot:
        """Capture the live, verified active state across all 12 dimensions."""
        def dump_entities(t: EntityType) -> List[Dict[str, Any]]:
            ents = self.ontology.get_by_type(t, state=LifecycleState.ACTIVE)
            return [e.model_dump(exclude={"version_history"}) for e in ents]

        active_beliefs = [
            b.model_dump() for b in self.beliefs.get_active_beliefs()
        ]

        snapshot = WorldStateSnapshot(
            timestamp=time.time(),
            state_mode="current",
            state_id=f"current_{int(time.time())}",
            agents=dump_entities(EntityType.AGENT),
            projects=dump_entities(EntityType.PROJECT),
            tasks=dump_entities(EntityType.TASK),
            goals=dump_entities(EntityType.GOAL),
            tools=dump_entities(EntityType.TOOL),
            skills=dump_entities(EntityType.SKILL),
            documents=dump_entities(EntityType.DOCUMENT),
            resources=dump_entities(EntityType.RESOURCE),
            risks=dump_entities(EntityType.RISK),
            capabilities=dump_entities(EntityType.CAPABILITY),
            beliefs=active_beliefs,
            predictions=dump_entities(EntityType.PREDICTION),
        )
        return snapshot

    def capture_checkpoint(self, tag: str = "checkpoint") -> WorldStateSnapshot:
        """Persist a point-in-time historical state snapshot."""
        snap = self.get_current_state()
        snap.state_mode = "historical"
        if self._history and snap.timestamp <= self._history[-1].timestamp:
            snap.timestamp = self._history[-1].timestamp + 0.001
        snap.state_id = f"{tag}_{int(time.time())}"
        self._history.append(snap)
        return snap

    def get_historical_state(self, target_time: float) -> Optional[WorldStateSnapshot]:
        """Query state at an exact or nearest prior historical timestamp."""
        best = None
        for snap in self._history:
            if snap.timestamp <= target_time:
                best = snap
            else:
                break
        return best or (self._history[0] if self._history else None)

    def project_future_state(self, horizon_seconds: float = 3600.0) -> WorldStateSnapshot:
        """Extrapolate forward state: complete pending tasks, decay unvalidated beliefs, evaluate risks."""
        base = self.get_current_state()
        future = copy.deepcopy(base)
        future.timestamp = base.timestamp + horizon_seconds
        future.state_mode = "future"
        future.state_id = f"future_plus_{int(horizon_seconds)}s"

        # 1. Project tasks towards completion
        for t in future.tasks:
            if t.get("status") == "pending":
                t["status"] = "projected_completed"

        # 2. Project belief confidence decay
        import math
        for b in future.beliefs:
            decay_rate = b.get("decay_rate", 0.005)
            factor = math.exp(-decay_rate * (horizon_seconds / 60.0))
            b["confidence"] = round(b.get("confidence", 0.5) * factor, 4)

        # 3. Project resource consumption
        for r in future.resources:
            r["current_load"] = min(r.get("capacity", 100.0), r.get("current_load", 0.0) * 1.1)

        return future

    def fork_simulated_state(self, simulation_id: str, mutations: Optional[Dict[str, Any]] = None) -> WorldStateSnapshot:
        """Fork an isolated sandbox world state for counterfactual what-if simulation."""
        base = self.get_current_state()
        sim = copy.deepcopy(base)
        sim.state_mode = "simulated"
        sim.state_id = simulation_id

        if mutations:
            # Apply hypothetical changes
            if "remove_agent_id" in mutations:
                sim.agents = [a for a in sim.agents if a.get("id") != mutations["remove_agent_id"]]
            if "fail_project_id" in mutations:
                for p in sim.projects:
                    if p.get("id") == mutations["fail_project_id"]:
                        p["status"] = "failed"
            if "disable_tool_name" in mutations:
                sim.tools = [t for t in sim.tools if t.get("name") != mutations["disable_tool_name"]]

        self._simulations[simulation_id] = sim
        return sim
