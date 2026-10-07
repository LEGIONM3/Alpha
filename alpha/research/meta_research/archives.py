"""Research Archives, Timelines, and Lineages: Preserving the intellectual history of Project Alpha."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Publication, Theory, Refutation


class TimelineEvent(BaseModel):
    event_id: str
    event_type: str  # DISCOVERY, THEORY_ESTABLISHED, PARADIGM_SHIFT, REFUTATION, PUBLICATION
    title: str
    description: str
    entity_id: str
    timestamp: float = Field(default_factory=time.time)


class ResearchArchives:
    """Permanent repository preserving every intellectual milestone and retired model."""

    def __init__(self):
        self.publications: Dict[str, Publication] = {}
        self.retired_theories: Dict[str, Dict[str, Any]] = {}
        self.refutations: Dict[str, Refutation] = {}
        self.timeline: List[TimelineEvent] = []
        self._lock = threading.RLock()

    def archive_publication(self, pub: Publication) -> None:
        with self._lock:
            self.publications[pub.publication_id] = pub
            self.timeline.append(TimelineEvent(
                event_id=f"evt_{len(self.timeline)+1}",
                event_type="PUBLICATION",
                title=f"Published: {pub.title}",
                description=pub.abstract[:120],
                entity_id=pub.publication_id
            ))

    def archive_retired_theory(self, theory: Theory, refutation: Refutation) -> None:
        with self._lock:
            self.retired_theories[theory.theory_id] = {
                "theory": theory,
                "refutation": refutation,
                "archived_at": time.time()
            }
            self.refutations[refutation.refutation_id] = refutation
            self.timeline.append(TimelineEvent(
                event_id=f"evt_{len(self.timeline)+1}",
                event_type="PARADIGM_SHIFT",
                title=f"Retired Theory: {theory.name}",
                description=refutation.argumentation,
                entity_id=theory.theory_id
            ))

    def get_timeline(self) -> List[TimelineEvent]:
        with self._lock:
            return sorted(self.timeline, key=lambda e: e.timestamp)
