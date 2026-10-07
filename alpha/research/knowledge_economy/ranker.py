"""Knowledge Asset Ranker: Portfolio curation of civilization knowledge assets."""

from __future__ import annotations

import threading
from typing import Dict, List, Any, Optional
from alpha.research.knowledge_economy.asset import KnowledgeAsset


class KnowledgeAssetRanker:
    """Manages and ranks civilization intellectual assets as valued resources."""

    def __init__(self):
        self.assets: Dict[str, KnowledgeAsset] = {}
        self._lock = threading.RLock()

    def register_asset(
        self,
        title: str,
        target_entity_type: str,
        target_entity_id: str,
        domain: str,
        value: float = 0.8,
        novelty: float = 0.8,
        impact: float = 0.8,
        confidence: float = 0.85,
        verification: float = 0.8
    ) -> KnowledgeAsset:
        with self._lock:
            asset = KnowledgeAsset(
                title=title,
                target_entity_type=target_entity_type,
                target_entity_id=target_entity_id,
                domain=domain,
                value=value,
                novelty=novelty,
                impact=impact,
                confidence=confidence,
                verification=verification
            )
            asset.calculate_composite_rank()
            self.assets[asset.asset_id] = asset
            return asset

    def get_ranked_assets(self, domain: Optional[str] = None, limit: int = 50) -> List[KnowledgeAsset]:
        with self._lock:
            filtered = list(self.assets.values())
            if domain:
                filtered = [a for a in filtered if a.domain == domain]
            filtered.sort(key=lambda a: a.composite_rank, reverse=True)
            return filtered[:limit]

    def get_under_verified_high_impact_assets(self, min_impact: float = 0.75, max_verif: float = 0.60) -> List[KnowledgeAsset]:
        """Find priority targets for verification and replication."""
        with self._lock:
            return [
                a for a in self.assets.values()
                if a.impact >= min_impact and a.verification <= max_verif
            ]
