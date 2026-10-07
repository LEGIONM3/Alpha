"""Lifecycle Tracker: Tracks birth, growth, change, decay, and death across entities."""

import time
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class LifecycleStage(str, Enum):
    """The 5 universal biological/cognitive lifecycle phases."""
    BIRTH = "birth"
    GROWTH = "growth"
    CHANGE = "change"
    DECAY = "decay"
    DEATH = "death"


class LifecycleTransition(BaseModel):
    """Record of a transition between lifecycle stages."""
    entity_id: str
    from_stage: Optional[LifecycleStage]
    to_stage: LifecycleStage
    timestamp: float = Field(default_factory=time.time)
    trigger_reason: str = ""
    metric_snapshot: Dict[str, Any] = Field(default_factory=dict)


class LifecycleTracker:
    """Tracks lifecycle progression, durations, and stage transitions."""

    def __init__(self):
        self._transitions: Dict[str, List[LifecycleTransition]] = {}
        self._current_stage: Dict[str, LifecycleStage] = {}

    def record_birth(self, entity_id: str, reason: str = "instantiated", metrics: Optional[Dict[str, Any]] = None) -> LifecycleTransition:
        return self._transition(entity_id, None, LifecycleStage.BIRTH, reason, metrics)

    def record_growth(self, entity_id: str, reason: str = "strengthened", metrics: Optional[Dict[str, Any]] = None) -> LifecycleTransition:
        return self._transition(entity_id, self._current_stage.get(entity_id), LifecycleStage.GROWTH, reason, metrics)

    def record_change(self, entity_id: str, reason: str = "mutated", metrics: Optional[Dict[str, Any]] = None) -> LifecycleTransition:
        return self._transition(entity_id, self._current_stage.get(entity_id), LifecycleStage.CHANGE, reason, metrics)

    def record_decay(self, entity_id: str, reason: str = "deprecating", metrics: Optional[Dict[str, Any]] = None) -> LifecycleTransition:
        return self._transition(entity_id, self._current_stage.get(entity_id), LifecycleStage.DECAY, reason, metrics)

    def record_death(self, entity_id: str, reason: str = "terminated", metrics: Optional[Dict[str, Any]] = None) -> LifecycleTransition:
        return self._transition(entity_id, self._current_stage.get(entity_id), LifecycleStage.DEATH, reason, metrics)

    def _transition(
        self,
        entity_id: str,
        from_stage: Optional[LifecycleStage],
        to_stage: LifecycleStage,
        reason: str,
        metrics: Optional[Dict[str, Any]]
    ) -> LifecycleTransition:
        trans = LifecycleTransition(
            entity_id=entity_id,
            from_stage=from_stage,
            to_stage=to_stage,
            trigger_reason=reason,
            metric_snapshot=metrics or {}
        )
        if entity_id not in self._transitions:
            self._transitions[entity_id] = []
        self._transitions[entity_id].append(trans)
        self._current_stage[entity_id] = to_stage
        return trans

    def get_current_stage(self, entity_id: str) -> LifecycleStage:
        return self._current_stage.get(entity_id, LifecycleStage.BIRTH)

    def get_history(self, entity_id: str) -> List[LifecycleTransition]:
        return self._transitions.get(entity_id, [])
