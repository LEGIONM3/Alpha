"""Knowledge Society: Shared knowledge layer, inheritance, publishing, verification, and ranking."""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class KnowledgeItem(BaseModel):
    """A verified or proposed collective asset in the civilization's knowledge graph."""
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    title: str
    content: Any
    author_id: str
    author_role: str
    is_verified: bool = False
    verifications_count: int = 0
    citation_count: int = 0
    utility_score: float = 0.5
    tags: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

    def compute_ranking(self) -> float:
        """Calculate dynamic utility ranking."""
        verify_bonus = 0.4 if self.is_verified else -0.2
        citations_weight = min(0.3, self.citation_count * 0.05)
        verif_weight = min(0.3, self.verifications_count * 0.1)
        base = self.utility_score * 0.4
        return round(max(0.0, min(1.0, base + verify_bonus + citations_weight + verif_weight)), 3)

class SharedKnowledgeLayer:
    """Civilizational knowledge repository with publishing, verification, and inheritance."""

    def __init__(self):
        self._items: Dict[str, KnowledgeItem] = {}
        self._by_key: Dict[str, str] = {}
        self._role_curated: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        self._seed_foundational_knowledge()

    def _seed_foundational_knowledge(self) -> None:
        """Seed baseline architectural knowledge."""
        self.publish(
            key="axiom:deterministic_validation",
            title="Deterministic Validation Axiom",
            content="Never trust unverified language model generation without formal schema and test assertions.",
            author_id="civilization_architect",
            author_role="architect",
            tags=["core", "axiom", "security"],
            auto_verify=True
        )
        self.publish(
            key="axiom:fail_safe_isolation",
            title="Subprocess Sandbox Isolation",
            content="Execute all untrusted code within bounded timeout subprocesses.",
            author_id="civilization_architect",
            author_role="security",
            tags=["core", "sandbox"],
            auto_verify=True
        )

    def publish(
        self,
        key: str,
        title: str,
        content: Any,
        author_id: str,
        author_role: str,
        tags: Optional[List[str]] = None,
        auto_verify: bool = False
    ) -> KnowledgeItem:
        """Publish a new knowledge entry into the civilization repository."""
        with self._lock:
            item = KnowledgeItem(
                key=key,
                title=title,
                content=content,
                author_id=author_id,
                author_role=author_role,
                is_verified=auto_verify,
                verifications_count=1 if auto_verify else 0,
                utility_score=0.9 if auto_verify else 0.5,
                tags=tags or []
            )
            self._items[item.item_id] = item
            self._by_key[key] = item.item_id

            if author_role not in self._role_curated:
                self._role_curated[author_role] = []
            self._role_curated[author_role].append(item.item_id)
            return item

    def verify_knowledge(self, item_id: str, verifier_id: str, verifier_role: str, approve: bool = True) -> bool:
        """Verify and promote an existing knowledge entry."""
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return False
            if approve:
                item.is_verified = True
                item.verifications_count += 1
                item.utility_score = min(1.0, item.utility_score + 0.15)
            else:
                item.utility_score = max(0.0, item.utility_score - 0.25)
            return True

    def cite_knowledge(self, key_or_id: str) -> Optional[KnowledgeItem]:
        """Record a citation of a knowledge entry, incrementing utility."""
        with self._lock:
            item_id = self._by_key.get(key_or_id, key_or_id)
            item = self._items.get(item_id)
            if item:
                item.citation_count += 1
                return item
            return None

    def inherit_for_role(self, role: str) -> List[KnowledgeItem]:
        """Retrieve foundational and role-relevant knowledge inherited by an agent."""
        with self._lock:
            results = []
            # Inherit all core axioms
            for item in self._items.values():
                if "core" in item.tags and item.is_verified:
                    results.append(item)
                elif item.author_role == role and item.is_verified:
                    if item not in results:
                        results.append(item)
            return results

    def get_ranked_knowledge(self, tag_filter: Optional[str] = None) -> List[KnowledgeItem]:
        """Return all knowledge items sorted by ranking score descending."""
        with self._lock:
            items = list(self._items.values())
            if tag_filter:
                items = [it for it in items if tag_filter in it.tags]
            items.sort(key=lambda it: it.compute_ranking(), reverse=True)
            return items

    def total_count(self) -> int:
        with self._lock:
            return len(self._items)
