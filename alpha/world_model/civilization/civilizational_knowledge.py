"""Civilizational Knowledge System: Publishing, Verification, Ranking, Retirement, Inheritance, and Evolution.

Part 14: Civilizational Knowledge System
The civilization must maintain collective understanding across all agents and generations.
"""

from __future__ import annotations

import time
import uuid
import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.world_model.ontology.entities import LifecycleState


class CivilizationalAsset(BaseModel):
    """A governed intellectual asset belonging to the civilization."""
    asset_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    title: str
    content: Any
    author_id: str
    author_role: str
    is_verified: bool = False
    verification_score: float = 0.5
    verification_count: int = 0
    citation_count: int = 0
    utility_score: float = 0.5
    version: int = 1
    lifecycle_state: LifecycleState = LifecycleState.ACTIVE
    tags: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def calculate_rank(self) -> float:
        """Composite civilizational rank based on verification, citations, and utility."""
        if self.lifecycle_state != LifecycleState.ACTIVE:
            return 0.0
        v_bonus = 0.35 if self.is_verified else 0.0
        c_bonus = min(0.30, self.citation_count * 0.05)
        u_term = self.utility_score * 0.35
        return round(min(1.0, v_bonus + c_bonus + u_term), 3)


class CivilizationalKnowledgeSystem:
    """Central repository governing civilizational knowledge creation, audit, and distribution."""

    def __init__(self):
        self._assets: Dict[str, CivilizationalAsset] = {}
        self._by_key: Dict[str, str] = {}
        self._role_index: Dict[str, List[str]] = {}
        self._lock = threading.RLock()

    def publish(
        self,
        key: str,
        title: str,
        content: Any,
        author_id: str,
        author_role: str,
        tags: Optional[List[str]] = None,
        auto_verify: bool = False
    ) -> CivilizationalAsset:
        """Publish a new civilizational asset."""
        with self._lock:
            asset = CivilizationalAsset(
                key=key,
                title=title,
                content=content,
                author_id=author_id,
                author_role=author_role,
                is_verified=auto_verify,
                verification_score=0.9 if auto_verify else 0.5,
                verification_count=1 if auto_verify else 0,
                utility_score=0.85 if auto_verify else 0.5,
                tags=tags or []
            )
            self._assets[asset.asset_id] = asset
            self._by_key[key] = asset.asset_id

            if author_role not in self._role_index:
                self._role_index[author_role] = []
            self._role_index[author_role].append(asset.asset_id)
            return asset

    def verify(
        self,
        asset_id: str,
        verifier_id: str,
        approved: bool = True,
        confidence_delta: float = 0.2
    ) -> bool:
        """Peer verification of an asset by another agent or validator."""
        with self._lock:
            asset = self._assets.get(asset_id)
            if not asset:
                return False
            asset.verification_count += 1
            if approved:
                asset.is_verified = True
                asset.verification_score = min(1.0, asset.verification_score + confidence_delta)
                asset.utility_score = min(1.0, asset.utility_score + 0.15)
            else:
                asset.verification_score = max(0.0, asset.verification_score - confidence_delta * 1.5)
                asset.utility_score = max(0.0, asset.utility_score - 0.25)
            asset.updated_at = time.time()
            return True

    def cite(self, key_or_id: str) -> Optional[CivilizationalAsset]:
        """Record usage/citation of an asset by an agent in production."""
        with self._lock:
            aid = self._by_key.get(key_or_id, key_or_id)
            asset = self._assets.get(aid)
            if asset:
                asset.citation_count += 1
                asset.utility_score = min(1.0, asset.utility_score + 0.02)
                return asset
            return None

    def evolve(self, asset_id: str, new_content: Any, reason: str = "improvement") -> CivilizationalAsset:
        """Mutate an existing asset to a new version, preserving continuity."""
        with self._lock:
            asset = self._assets.get(asset_id)
            if not asset:
                raise KeyError(f"Asset {asset_id} not found.")
            asset.content = new_content
            asset.version += 1
            asset.updated_at = time.time()
            asset.lifecycle_state = LifecycleState.EVOLVING
            return asset

    def retire(self, asset_id: str, reason: str = "obsolete") -> bool:
        """Retire/deprecate knowledge that has been superseded or falsified."""
        with self._lock:
            asset = self._assets.get(asset_id)
            if not asset:
                return False
            asset.lifecycle_state = LifecycleState.DEPRECATED
            asset.updated_at = time.time()
            return True

    def inherit_for_role(self, role: str) -> List[CivilizationalAsset]:
        """Retrieve foundational knowledge and role-curated assets inherited by an agent."""
        with self._lock:
            results = []
            for asset in self._assets.values():
                if asset.lifecycle_state != LifecycleState.ACTIVE:
                    continue
                # Inherit core foundational axioms
                if "core" in asset.tags and asset.is_verified:
                    results.append(asset)
                elif asset.author_role == role and asset.is_verified:
                    if asset not in results:
                        results.append(asset)
            return sorted(results, key=lambda a: a.calculate_rank(), reverse=True)

    def rank_all(self, tag_filter: Optional[str] = None) -> List[CivilizationalAsset]:
        """Return assets ordered by rank descending."""
        with self._lock:
            items = list(self._assets.values())
            if tag_filter:
                items = [a for a in items if tag_filter in a.tags]
            return sorted(items, key=lambda a: a.calculate_rank(), reverse=True)
