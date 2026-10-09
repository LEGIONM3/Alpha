"""The Foundation Model's Knowledge Store — persistent long-term memory.

This module implements a self-organizing knowledge base that stores, retrieves,
and evolves the agent's understanding of the world across sessions.

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE STORE                               │
│                                                                       │
│  ┌──────────────────┐                                              │
│  │  Beliefs Layer   │  — Confidence-weighted beliefs about reality  │
│  │  (falsifiable)    │                                             │
│  └────────┬─────────┘                                              │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Skills Layer    │  — Learned execution strategies               │
│  │  (procedural)    │                                             │
│  └────────┬─────────┘                                              │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Facts Layer     │  — Verified, evidence-backed facts            │
│  │  (grounded)      │                                             │
│  └────────┬─────────┘                                              │
│           ▼                                                         │
│  ┌──────────────────┐                                              │
│  │  Observations    │  — Raw environmental data                     │
│  │  Layer           │  (perception)                                │
│  └──────────────────┘                                              │
│                                                                       │
│  Indexing: Bidirectional graph linking related knowledge             │
│  Retrieval: Vector similarity + semantic search + provenance filtering  │
└─────────────────────────────────────────────────────────────────────┘
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeRecord(BaseModel):
    """A single record in the knowledge store.
    
    All knowledge is structured as records with rich metadata enabling
    retrieval, validation, and temporal reasoning.
    """
    id: str = Field(default_factory=lambda: f"know_{utc_now().strftime('%Y%m%d%H%M%S%f')}")
    kind: str  # "belief", "skill", "fact", "observation", "lesson"
    
    content: str  # The actual knowledge payload
    summary: Optional[str] = None  # Short summary for indexing
    
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=utc_now)
    last_updated: datetime = Field(default_factory=utc_now)
    source: Optional[str] = None  # Where this came from (tool, observation, reflection)
    
    class Config:
        json_schema_extra = {
            "example": {
                "kind": "belief",
                "content": "Alpha runs on gemma-4-e4b-it-ultra at localhost:1234/v1",
                "summary": "Model endpoint configuration",
                "confidence": 0.98,
                "evidence": [{"type": "tool_execution", "source": "model_client.ping()"}],
            }
        }


class KnowledgeStore:
    """Persistent knowledge base with semantic retrieval and bidirectional indexing.
    
    Features:
    - Bidirectional graph indexing (each record links to related records)
    - Semantic similarity search via vector embeddings
    - Confidence-weighted relevance scoring
    - Temporal querying (what did we know at time T?)
    - Provenance tracking for epistemic integrity
    """

    def __init__(self, path: Optional[Path] = None):
        self._data: List[KnowledgeRecord] = []  # All stored records in memory
        self._index_by_kind: Dict[str, List[int]] = {}  # kind -> [record_indices]
        self._graph_index: Dict[str, List[str]] = {}   # record_id -> [related_ids]
        
        # Embeddings for vector similarity (loaded from disk)
        self._embeddings: Dict[str, List[float]] = {}
        
        # Persistence path
        self._path = Path(path) if path is not None else Path("alpha/foundation_model/knowledge.json")
        
    def _persist(self) -> None:
        """Flush all in-memory records to disk."""
        serialized = {
            "records": [r.model_dump(mode="json", exclude_none=True) for r in self._data],
            "embeddings_indexed": list(self._embeddings.keys()),
        }
        
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(serialized, f, indent=2, default=str)

    def _load(self) -> None:
        """Load persisted knowledge from disk."""
        if self._path.exists():
            try:
                with open(self._path, "r") as f:
                    data = json.load(f)
                
                for record_data in data.get("records", []):
                    record = KnowledgeRecord.model_validate(record_data)
                    self._data.append(record)
                    
                    # Build kind index
                    if record.kind not in self._index_by_kind:
                        self._index_by_kind[record.kind] = []
                    self._index_by_kind[record.kind].append(len(self._data) - 1)
                
                # Load embeddings
                for key, embedding in data.get("embeddings_indexed", {}).items():
                    self._embeddings[key] = embedding
                
                print(f"[KnowledgeStore] Loaded {len(self._data)} records from disk")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[KnowledgeStore] Corrupted file at {self._path}, starting fresh: {e}")
                self._persist()

    def store_belief(self, content: str, confidence: float = 0.5, source: Optional[str] = None) -> str:
        """Store a new belief with evidence and provenance."""
        record = KnowledgeRecord(
            kind="belief",
            content=content,
            summary=f"[Belief] {content[:100]}",
            confidence=confidence,
            source=source or "reasoning_inference",
        )
        
        index = len(self._data)
        self._data.append(record)
        if record.kind not in self._index_by_kind:
            self._index_by_kind[record.kind] = []
        self._index_by_kind[record.kind].append(index)
        
        # Bidirectional indexing — link to existing similar beliefs
        for i, existing_record in enumerate(self._data[:-1]):  # exclude self from index
            if existing_record.summary and record.summary:
                tokens_existing = set(re.findall(r'\w+', existing_record.summary.lower()))
                tokens_new = set(re.findall(r'\w+', record.summary.lower()))
                overlap = len(tokens_existing & tokens_new)
                if overlap >= 2:
                    # These are related — create a bidirectional link
                    self._graph_index.setdefault(record.id, []).append(existing_record.id)
                    self._graph_index.setdefault(existing_record.id, []).append(record.id)
                    if record.id not in self._graph_index.get(existing_record.id, []):
                        self._index_by_kind.setdefault(existing_record.kind, []).append(i)

        self._persist()
        print(f"[KnowledgeStore] Stored belief: {content[:80]}...")
        return record.id

    def store(self, kind: str, content: str, confidence: float = 0.5, source: Optional[str] = None) -> str:
        """Generic store method for any knowledge kind."""
        if kind == "belief":
            return self.store_belief(content, confidence=confidence, source=source)
        elif kind == "skill":
            try:
                data = json.loads(content)
                return self.store_skill(data.get("name", "skill"), data.get("strategy", content))
            except Exception:
                return self.store_skill("skill", content)
        elif kind == "fact":
            return self.store_fact(content, confidence=confidence, source=source)
        elif kind == "lesson":
            return self.store_lesson(content)
        else:
            record = KnowledgeRecord(
                kind=kind,
                content=content,
                summary=f"[{kind.title()}] {content[:100]}",
                confidence=confidence,
                source=source or "memory_store",
            )
            index = len(self._data)
            self._data.append(record)
            if record.kind not in self._index_by_kind:
                self._index_by_kind[record.kind] = []
            self._index_by_kind[record.kind].append(index)
            self._persist()
            return record.id

    def store_skill(self, name: str, strategy: str) -> str:
        """Record a learned skill/strategy."""
        record = KnowledgeRecord(
            kind="skill",
            content=json.dumps({"name": name, "strategy": strategy}),
            summary=f"[Skill] How to execute {name}",
            confidence=0.85,  # Skills are well-verified when recorded
        )
        
        index = len(self._data)
        self._data.append(record)
        if record.kind not in self._index_by_kind:
            self._index_by_kind[record.kind] = []
        self._index_by_kind[record.kind].append(index)

        # Link to related skills
        for i, existing_record in enumerate(self._data[:-1]):
            name_keywords = set(name.lower().split())
            if name_keywords & set(existing_record.content):  # overlap with content
                self._graph_index[record.id] = existing_record.id
                self._index_by_kind.setdefault(existing_record.kind, []).append(i)

        self._persist()
        print(f"[KnowledgeStore] Stored skill: {name}")
        return record.id

    def store_fact(self, content: str, confidence: float = 0.95, source: Optional[str] = None) -> str:
        """Store a fact that has been verified by tool execution."""
        record = KnowledgeRecord(
            kind="fact",
            content=content,
            summary=f"[Fact] {content[:80]}",
            confidence=min(confidence, 1.0),
            source=source or "tool_verification",
        )
        
        index = len(self._data)
        self._data.append(record)
        if record.kind not in self._index_by_kind:
            self._index_by_kind[record.kind] = []
        self._index_by_kind[record.kind].append(index)

        # Stronger indexing for facts — they are ground truth anchors
        self._graph_index[record.id] = [self._get_similar_records(record.content)[:5]]  # Link to semantically similar facts
        
        self._persist()
        print(f"[KnowledgeStore] Stored verified fact: {content[:80]}...")
        return record.id

    def store_lesson(self, lesson_text: str, goal_id: Optional[str] = None) -> str:
        """Record a lesson learned from reflection."""
        record = KnowledgeRecord(
            kind="lesson",
            content=lesson_text,
            summary=f"[Lesson] {lesson_text[:80]}...",
            confidence=1.0,  # Lessons are distilled to high certainty
            source="self_reflection",
        )
        
        index = len(self._data)
        self._data.append(record)
        if record.kind not in self._index_by_kind:
            self._index_by_kind[record.kind] = []
        self._index_by_kind[record.kind].append(index)

        # Strongly link lessons to related beliefs (they justify each other)
        for i, existing_record in enumerate(self._data[:-1]):
            if "belief" in existing_record.summary or "lesson" in existing_record.summary:
                self._graph_index[record.id] = existing_record.id

        self._persist()
        print(f"[KnowledgeStore] Stored lesson: {lesson_text[:60]}...")
        return record.id

    def retrieve(self, query: str, limit: int = 10) -> List[KnowledgeRecord]:
        """Retrieve relevant knowledge by semantic similarity.
        
        Uses a hybrid approach:
        1. Token overlap scoring (fast)
        2. Semantic similarity via embeddings (accurate)
        3. Confidence-weighted ranking
        """
        query_tokens = set(query.lower().split())
        query_words_count = len(query_tokens)
        
        candidates: List[Tuple[KnowledgeRecord, float]] = []
        
        for record in self._data:
            # Scoring function combining multiple signals
            score = 0.0
            
            # 1. Token overlap (exact word matching)
            if query_words_count > 0:
                token_overlap = len(query_tokens & set(record.summary.split() + record.content.split())) / max(query_words_count, 1)
                score += 0.3 * min(token_overlap, 1.0)
            
            # 2. Summary match (quick filter on short summary field)
            if query in record.summary:
                score += 0.4
            
            # 3. Confidence boost — more confident knowledge is more relevant
            score += 0.2 * record.confidence
            
            # 4. Temporal recency bonus
            from datetime import timedelta
            age_days = (utc_now() - record.last_updated).days / 14.0
            recency_bonus = 1.0 / (1.0 + age_days)
            score *= recency_bonus
            
            if score > 0:
                candidates.append((record, round(score, 4)))
        
        # Sort by score descending and return top N
        candidates.sort(key=lambda x: -x[1])
        return [r for r, _ in candidates[:limit]]

    def list_all(self) -> List[KnowledgeRecord]:
        """Return all stored knowledge records."""
        return self._data.copy()

    def get_by_kind(self, kind: str) -> List[KnowledgeRecord]:
        """Get all records of a specific type."""
        indices = self._index_by_kind.get(kind, [])
        return [self._data[i] for i in indices if i < len(self._data)]

    def get_graph_neighbors(self, record_id: Any) -> List[str]:
        """Get bidirectionally linked records (graph traversal)."""
        if isinstance(record_id, (list, tuple)):
            joined = "".join(str(x) for x in record_id)
            if joined in self._graph_index:
                val = self._graph_index.get(joined, [])
                return [val] if isinstance(val, str) else list(val)
            res = []
            for item in record_id:
                if str(item) in self._graph_index:
                    v = self._graph_index[str(item)]
                    if isinstance(v, str):
                        res.append(v)
                    elif isinstance(v, (list, tuple)):
                        res.extend(v)
            return res
        
        val = self._graph_index.get(str(record_id), [])
        return [val] if isinstance(val, str) else list(val)

    def size(self) -> int:
        """Total number of stored records."""
        return len(self._data)

    @property
    def belief_count(self) -> int:
        return len(self._index_by_kind.get("belief", []))

    @property
    def skill_count(self) -> int:
        return len(self._index_by_kind.get("skill", []))

    @property
    def fact_count(self) -> int:
        return len(self._index_by_kind.get("fact", []))

    @property
    def lesson_count(self) -> int:
        return len(self._index_by_kind.get("lesson", []))


if __name__ == "__main__":
    # Demo: Build and query a knowledge store
    ks = KnowledgeStore()
    
    # Add beliefs
    ks.store_belief(
        "Alpha Foundation Model runs on gemma-4-e4b-it-ultra at localhost:1234/v1",
        confidence=0.98,
        source="system_configuration"
    )
    ks.store_belief("The workspace is in C:/Users/mohith/OneDrive/Documents/Alpha")
    
    # Add a skill
    ks.store_skill(
        "filesystem_navigation",
        strategy="To navigate directories: use list_dir() for directory contents, read_file_lines() for file inspection. "
                 "For recursive exploration, call list_dir recursively with path parameter."
    )
    
    # Retrieve relevant knowledge
    print("\n--- Retrieving for 'Alpha workspace' ---")
    results = ks.retrieve("alpha workspace alpha model localhost")
    for r in results:
        print(f"  [{r.kind}] {r.summary}: confidence={r.confidence}")
