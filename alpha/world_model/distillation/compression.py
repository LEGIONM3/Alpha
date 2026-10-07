"""Compression Engine: Semantic deduplication, cluster compression, and memory reduction.

Part 9: Knowledge Distillation
Prevents memory explosion by compacting high-volume logs into condensed structures.
"""

from typing import List, Dict, Any, Tuple
import hashlib
from collections import defaultdict


class CompressionEngine:
    """Performs semantic deduplication, hash-based grouping, and lossy/lossless compression."""

    def deduplicate(self, items: List[Dict[str, Any]], key_fields: List[str]) -> Tuple[List[Dict[str, Any]], int]:
        """Deduplicate records based on composite hash of key fields."""
        seen = set()
        deduped = []
        for it in items:
            h = hashlib.sha256(
                "|".join(str(it.get(k, "")) for k in key_fields).encode("utf-8")
            ).hexdigest()
            if h not in seen:
                seen.add(h)
                deduped.append(it)
        removed_count = len(items) - len(deduped)
        return deduped, removed_count

    def cluster_by_tokens(self, text_items: List[str], num_clusters: int = 10) -> Dict[int, List[str]]:
        """Fast bucket clustering based on token frequencies and hashing."""
        clusters = defaultdict(list)
        for text in text_items:
            # Deterministic bucket partition
            words = text.lower().split()
            lead_token = words[0] if words else "empty"
            bucket = int(hashlib.md5(lead_token.encode("utf-8")).hexdigest(), 16) % num_clusters
            clusters[bucket].append(text)
        return dict(clusters)
