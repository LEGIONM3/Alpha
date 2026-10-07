"""Memory Civilization: 9-Layer Cognitive Memory Hierarchy with Retention, Compression, Retrieval, and Version Control."""

import threading
import time
import uuid
import copy
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MemoryEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    value: Any
    tags: List[str] = Field(default_factory=list)
    importance: float = 0.5  # 0.0 to 1.0
    created_at: float = Field(default_factory=time.time)
    last_accessed_at: float = Field(default_factory=time.time)
    access_count: int = 0
    version: int = 1

class RetentionPolicy(BaseModel):
    max_entries: int = 1000
    ttl_seconds: Optional[float] = None
    min_importance_threshold: float = 0.0

class BaseMemoryLayer:
    """Base memory layer providing retention, compression, retrieval strategies, and version control."""

    def __init__(self, name: str, retention_policy: Optional[RetentionPolicy] = None):
        self.name = name
        self.retention = retention_policy or RetentionPolicy()
        self._entries: Dict[str, MemoryEntry] = {}
        self._versions_log: List[Dict[str, Any]] = []
        self._current_revision: int = 0
        self._lock = threading.RLock()

    def store(self, key: str, value: Any, tags: Optional[List[str]] = None, importance: float = 0.5) -> MemoryEntry:
        """Store or update memory entry, bumping version."""
        with self._lock:
            self._apply_retention()
            version = 1
            if key in self._entries:
                version = self._entries[key].version + 1

            entry = MemoryEntry(
                key=key,
                value=value,
                tags=tags or [],
                importance=importance,
                version=version
            )
            self._entries[key] = entry
            self._record_revision(action="store", key=key, version=version)
            return entry

    def retrieve(self, key: str) -> Optional[Any]:
        """Recency & access-tracked retrieval."""
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return None
            if self.retention.ttl_seconds:
                if (time.time() - entry.created_at) > self.retention.ttl_seconds:
                    del self._entries[key]
                    return None
            entry.last_accessed_at = time.time()
            entry.access_count += 1
            return entry.value

    def query(
        self,
        tag: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Retrieval strategy based on tags, importance threshold, and recency."""
        with self._lock:
            results = []
            now = time.time()
            for entry in self._entries.values():
                if self.retention.ttl_seconds and (now - entry.created_at) > self.retention.ttl_seconds:
                    continue
                if entry.importance < min_importance:
                    continue
                if tag and tag not in entry.tags:
                    continue
                results.append(entry)

            # Sort by composite score (importance * 0.6 + recency * 0.4)
            results.sort(key=lambda e: (e.importance * 0.6 + (e.last_accessed_at / now) * 0.4), reverse=True)
            return results[:limit]

    def compress(self) -> int:
        """Compression policy: deduplicate and prune entries below importance threshold."""
        with self._lock:
            initial = len(self._entries)
            keys_to_remove = [
                k for k, e in self._entries.items()
                if e.importance < 0.3 and e.access_count == 0
            ]
            for k in keys_to_remove:
                del self._entries[k]
            self._record_revision(action="compress", count=len(keys_to_remove))
            return initial - len(self._entries)

    def _apply_retention(self) -> None:
        """LRU and TTL eviction policy."""
        now = time.time()
        if self.retention.ttl_seconds:
            expired = [k for k, e in self._entries.items() if (now - e.created_at) > self.retention.ttl_seconds]
            for k in expired:
                del self._entries[k]

        if len(self._entries) >= self.retention.max_entries:
            # Evict least recently accessed
            sorted_entries = sorted(self._entries.items(), key=lambda item: item[1].last_accessed_at)
            overflow = len(self._entries) - self.retention.max_entries + 1
            for k, _ in sorted_entries[:overflow]:
                del self._entries[k]

    def create_snapshot(self) -> Dict[str, Any]:
        """Version control: snapshot of entire layer."""
        with self._lock:
            return {
                "name": self.name,
                "revision": self._current_revision,
                "entries": copy.deepcopy({
                    k: (e.model_dump() if hasattr(e, "model_dump") else e.dict())
                    for k, e in self._entries.items()
                }),
                "timestamp": time.time()
            }

    def _record_revision(self, **kwargs: Any) -> None:
        self._current_revision += 1
        self._versions_log.append({
            "revision": self._current_revision,
            "timestamp": time.time(),
            **kwargs
        })

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

class CivilizationMemorySystem:
    """Master 9-layer cognitive memory civilization for Project Alpha."""

    def __init__(self):
        # 1. Short-Term Memory (volatile context scratchpad, TTL 600s, max 200)
        self.short_term = BaseMemoryLayer(
            name="short_term",
            retention_policy=RetentionPolicy(max_entries=200, ttl_seconds=600.0)
        )
        # 2. Working Memory (active task state, max 500)
        self.working = BaseMemoryLayer(
            name="working",
            retention_policy=RetentionPolicy(max_entries=500, ttl_seconds=1800.0)
        )
        # 3. Project Memory (scoped to team/task lifecycle, max 2000)
        self.project = BaseMemoryLayer(
            name="project",
            retention_policy=RetentionPolicy(max_entries=2000)
        )
        # 4. Long-Term Memory (persistent historical facts, max 10000)
        self.long_term = BaseMemoryLayer(
            name="long_term",
            retention_policy=RetentionPolicy(max_entries=10000, min_importance_threshold=0.4)
        )
        # 5. Knowledge Memory (verified concepts, ontology links, max 5000)
        self.knowledge = BaseMemoryLayer(
            name="knowledge",
            retention_policy=RetentionPolicy(max_entries=5000, min_importance_threshold=0.6)
        )
        # 6. Collective Memory (civilizational consensus, max 2000)
        self.collective = BaseMemoryLayer(
            name="collective",
            retention_policy=RetentionPolicy(max_entries=2000, min_importance_threshold=0.7)
        )
        # 7. Agent Memory (per-agent episodic workspace, max 5000)
        self.agent = BaseMemoryLayer(
            name="agent",
            retention_policy=RetentionPolicy(max_entries=5000)
        )
        # 8. Reflection Memory (post-mortem reviews, lessons learned, max 2000)
        self.reflection = BaseMemoryLayer(
            name="reflection",
            retention_policy=RetentionPolicy(max_entries=2000, min_importance_threshold=0.5)
        )
        # 9. Experience Memory (state-action-reward trajectories, max 5000)
        self.experience = BaseMemoryLayer(
            name="experience",
            retention_policy=RetentionPolicy(max_entries=5000)
        )

    def total_entries(self) -> int:
        return sum([
            self.short_term.count(),
            self.working.count(),
            self.project.count(),
            self.long_term.count(),
            self.knowledge.count(),
            self.collective.count(),
            self.agent.count(),
            self.reflection.count(),
            self.experience.count(),
        ])
