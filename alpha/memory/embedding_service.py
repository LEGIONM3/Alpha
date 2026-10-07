"""Real Embedding Service for Project Alpha using local foundation embedding models."""

from __future__ import annotations

import json
import math
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class EmbeddedItem(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    vector: List[float] = Field(default_factory=list)
    dimension: int = 768
    created_at: float = Field(default_factory=time.time)


class EmbeddingService:
    """Manages generation, indexing, persistence, and semantic retrieval over real dense embeddings."""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:1234/v1",
        model_name: str = "text-embedding-nomic-embed-text-v1.5",
        timeout_seconds: float = 30.0,
        cache_file: Optional[str] = "data/embedding_cache.json"
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.cache_file = Path(cache_file) if cache_file else None
        self._cache: Dict[str, List[float]] = {}
        self._index: Dict[str, EmbeddedItem] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file and self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                self._cache = data.get("cache", {})
                items = data.get("index", [])
                for it in items:
                    item = EmbeddedItem(**it)
                    self._index[item.id] = item
            except Exception:
                pass

    def save_cache(self) -> None:
        if self.cache_file:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "cache": self._cache,
                "index": [it.model_dump() for it in self._index.values()]
            }
            self.cache_file.write_text(json.dumps(payload), encoding="utf-8")

    def embed_text(self, text: str) -> List[float]:
        """Generate or retrieve cached embedding for a single text."""
        clean_text = text.strip()
        if clean_text in self._cache:
            return self._cache[clean_text]

        vectors = self.embed_batch([clean_text])
        return vectors[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embeddings for a batch of strings via HTTP endpoint."""
        needed = [t.strip() for t in texts if t.strip() not in self._cache]
        if needed:
            payload = {
                "model": self.model_name,
                "input": needed
            }
            req = urllib.request.Request(
                f"{self.endpoint_url}/embeddings",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload).encode("utf-8")
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                embeds = [item["embedding"] for item in data.get("data", [])]
                for text, vec in zip(needed, embeds):
                    self._cache[text] = vec

        results = [self._cache[t.strip()] for t in texts]
        self.save_cache()
        return results

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> EmbeddedItem:
        vector = self.embed_text(text)
        item = EmbeddedItem(
            id=doc_id,
            text=text,
            metadata=metadata or {},
            vector=vector,
            dimension=len(vector)
        )
        self._index[doc_id] = item
        self.save_cache()
        return item

    def search(self, query: str, top_k: int = 5) -> List[Tuple[EmbeddedItem, float]]:
        """Perform semantic search ranking items by cosine similarity."""
        query_vec = self.embed_text(query)
        scored: List[Tuple[EmbeddedItem, float]] = []
        for item in self._index.values():
            sim = self.cosine_similarity(query_vec, item.vector)
            scored.append((item, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
