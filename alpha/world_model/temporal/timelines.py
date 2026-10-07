"""Timelines: Event Timeline, State Timeline, and Belief Timeline.

Part 7: Temporal Reasoning
Answers:
- What was true?
- What is true?
- What may become true?
"""

from __future__ import annotations

import time
import bisect
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """An event on the chronological timeline."""
    event_id: str
    event_type: str
    timestamp: float = Field(default_factory=time.time)
    actor_id: str = "system"
    payload: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""


class EventTimeline:
    """Chronologically sorted event stream for temporal audit and reasoning."""

    def __init__(self):
        self._events: List[TimelineEvent] = []
        self._timestamps: List[float] = []

    def record_event(
        self,
        event_id: str,
        event_type: str,
        actor_id: str = "system",
        payload: Optional[Dict[str, Any]] = None,
        summary: str = "",
        timestamp: Optional[float] = None
    ) -> TimelineEvent:
        ts = timestamp if timestamp is not None else time.time()
        ev = TimelineEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=ts,
            actor_id=actor_id,
            payload=payload or {},
            summary=summary
        )
        idx = bisect.bisect_right(self._timestamps, ts)
        self._timestamps.insert(idx, ts)
        self._events.insert(idx, ev)
        return ev

    def query_range(self, start_time: float, end_time: float) -> List[TimelineEvent]:
        i = bisect.bisect_left(self._timestamps, start_time)
        j = bisect.bisect_right(self._timestamps, end_time)
        return self._events[i:j]

    def get_latest(self, count: int = 10) -> List[TimelineEvent]:
        return self._events[-count:] if self._events else []


class BeliefSnapshot(BaseModel):
    belief_id: str
    statement: str
    confidence: float
    is_active: bool
    timestamp: float


class BeliefTimeline:
    """Tracks historical confidence and validity of beliefs over time."""

    def __init__(self):
        self._history: Dict[str, List[BeliefSnapshot]] = {}

    def record_belief_state(self, belief_id: str, statement: str, confidence: float, is_active: bool, timestamp: float) -> None:
        if belief_id not in self._history:
            self._history[belief_id] = []
        self._history[belief_id].append(
            BeliefSnapshot(
                belief_id=belief_id,
                statement=statement,
                confidence=confidence,
                is_active=is_active,
                timestamp=timestamp
            )
        )

    def what_was_believed_at(self, target_time: float, min_confidence: float = 0.5) -> List[BeliefSnapshot]:
        """Answer: What was true / believed at target_time?"""
        results = []
        for bid, snapshots in self._history.items():
            # Find the most recent snapshot at or before target_time
            valid_snap = None
            for snap in snapshots:
                if snap.timestamp <= target_time:
                    valid_snap = snap
                else:
                    break
            if valid_snap and valid_snap.is_active and valid_snap.confidence >= min_confidence:
                results.append(valid_snap)
        return results

    def get_belief_trajectory(self, belief_id: str) -> List[BeliefSnapshot]:
        return self._history.get(belief_id, [])


class StateTimeline:
    """Records chronological snapshots of the global world state."""

    def __init__(self):
        self._snapshots: List[Tuple[float, Dict[str, Any]]] = []

    def record_state(self, timestamp: float, state_summary: Dict[str, Any]) -> None:
        self._snapshots.append((timestamp, state_summary))

    def get_state_at(self, target_time: float) -> Optional[Dict[str, Any]]:
        """Find the state snapshot active at target_time."""
        active = None
        for ts, state in self._snapshots:
            if ts <= target_time:
                active = state
            else:
                break
        return active
