"""Multi-layer Memory Manager for the Foundation Model Agent.

Implements a hierarchical memory system inspired by biological cognition,
with specialized stores at different temporal and abstraction levels:

Memory Layers (from transient to permanent):
┌─────────────────────────────────────────────────────────────────┐
│  Experience Layer        │ — Episodic traces of completed actions│
│  (temporary, high-fidelity)                                       │
├─────────────────────────────────────────────────────────────────┤
│  Working Memory          │ — Current context window              │
│  (active in-memory state)                                         │
├─────────────────────────────────────────────────────────────────┤
│  Short-term Memory       │ — Recent observations, < 1 hour      │
├─────────────────────────────────────────────────────────────────┤
│  Long-term Memory        │ — Core beliefs and facts             │
│  (KnowledgeStore)                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Skills Layer            │ — Learned strategies & procedures     │
│                          │  (persistent, high-confidence)        │
└─────────────────────────────────────────────────────────────────┘

Memory is not just storage — it shapes cognition. Each layer serves
a different cognitive function:
- Short-term → attention & perception
- Long-term → identity & world model
- Skills → procedural execution
- Experience → episodic learning

Author: Gemini (Alpha Principal Systems Engineer)
"""

import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from alpha.foundation_model.knowledge_store import KnowledgeStore, utc_now


@dataclass
class MemoryRecord:
    """A single memory record with full provenance."""
    id: str = ""
    content: str = ""
    layer: str = "short_term"  # short_term, long_term, working, experience, skill
    created_at: datetime = field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    importance: float = 0.5  # 0.0 to 1.0 — how critical is this?
    
    # Retrieval metadata
    embeddings: List[float] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        if not self.id:
            from uuid import uuid4
            self.id = f"mem_{utc_now().strftime('%Y%m%d%H%M%S%f')}{uuid4().hex[:8]}"


class MemoryManager:
    """Central memory system with multi-layer storage and retrieval.
    
    The Foundation Model's cognitive architecture is shaped by its memory. This manager
    orchestrates how information flows between layers, ensuring that what the agent
    remembers informs how it thinks and acts.
    
    Layer Hierarchy & Purpose:
    ┌──────────────┬─────────────────────┬─────────────────────────────────────────┐
    │ Layer        │ Lifetime            │ Cognitive Role                          │
    ├──────────────┼─────────────────────┼─────────────────────────────────────────┤
    │ working      │ ephemeral (RAM)     │ Current context, active reasoning       │
    ├───▲──────────┤                     │ "What am I thinking right now?"         │
    │   │          │  Memory is NOT neutral — it shapes what │
    │   └──────────┴────│ the agent notices and how it interprets │
    │     │            │ events. This manager encodes that truth. │
    ├───▲──────────┤                     │ "What did I just learn?"                 │
    │   │          │  Lower layers constrain & enable         │
    │   └──────────┴────│ higher-layer cognition (Hebbian-like)    │
    │     │            │                                          │
    ├───▲──────────┼──────────┐                        │ "What do I know about the world?"      │
    │   │          ▼  Long-term ←───┘                        │ "How should I act?"                     │
    │   └────────── Short-term     │                                                │
    │                            │   Experience Layer         │  (episodic: what happened)
    │   Skills                    │  Working Memory           │  (active context)
    │   ←─ procedural knowledge  │  Long-term Memory          │  (beliefs & facts)
    └────────────────────────────┴── Knowledge Store (file) ──┘ (persistent truth)
    
    Key Principle: Retrieval is generation. There is no "database query" — only
    pattern-matching against the memory landscape. The agent retrieves what it
    *thinks* matters, and in doing so, constructs its world view.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self._workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        
        # Layer-specific stores with different retention policies
        self.working_memory: Dict[str, MemoryRecord] = {}  # in-memory, active context
        self.short_term: List[MemoryRecord] = []           # < 1 hour window
        self.experience_layer: List[MemoryRecord] = []     # recent completed actions
        
        # Persistent stores (KnowledgeStore-backed)
        self.long_term_store = KnowledgeStore(
            path=self._workspace_root / "foundation_model" / "long_term_memory.json"
        )
        self.skills_store = KnowledgeStore(
            path=self._workspace_root / "foundation_model" / "skills.json"
        )

    def _encode_embedding(self, content: str) -> List[float]:
        """Convert text to a simple TF-IDF style embedding for comparison.
        
        In production this would use nomic-embed-text or similar. This is a
        lightweight fallback that works with plain Python.
        """
        words = content.lower().replace("\n", " ").replace("  ", " ").split()
        word_count = len(words)
        
        # Count word frequencies (bag-of-words)
        doc_words: Dict[str, int] = {}
        for w in words:
            if not w.startswith(("mem_", "know_")):  # skip IDs
                doc_words[w] = doc_words.get(w, 0) + 1
        
        # Compute term frequency - inverse document frequency style score
        embedding = []
        all_docs_count = sum(len(r.content.split()) for r in self.short_term + self.experience_layer) + 50
        
        for w, count in doc_words.items():
            tf_idf = (count / max(word_count, 1)) * min(1.0, all_docs_count / max(count, 1))
            embedding.append(tf_idf)
        
        return embedding[:256] if embedding else [0.0] * 256

    def store(self, content: str, layer: str = "short_term") -> MemoryRecord:
        """Store a memory in the appropriate layer."""
        
        record = MemoryRecord(
            id=f"mem_{utc_now().strftime('%Y%m%d%H%M%S%f')}{time.time_ns()}",
            content=content,
            layer=layer,
            importance=self._infer_importance(content),
        )
        
        embeddings = self._encode_embedding(content)
        record.embeddings = embeddings
        
        if layer == "working":
            # Working memory is overwritten — last write wins
            self.working_memory[record.id] = record
            
        elif layer == "short_term":
            self.short_term.append(record)
            if len(self.short_term) > 50:  # Hard cap to prevent blowup
                oldest = self.short_term.pop(0)
                
        elif layer == "experience":
            self.experience_layer.insert(0, record)
            if len(self.experience_layer) > 100:
                self.experience_layer.pop()

        else:  # long_term or skill
            # Persist to KnowledgeStore (long-term storage on disk)
            self._persist_to_knowledge_store(record)

        return record

    def _infer_importance(self, content: str) -> float:
        """Heuristic inference of memory importance."""
        high_value_keywords = ["error", "fail", "learned", "should never", "never again",
                               "success", "best practice", "root cause", "lesson"]
        
        content_lower = content.lower()
        matches = sum(1 for kw in high_value_keywords if kw in content_lower)
        return min(0.9 + (matches * 0.05), 1.0)

    def _persist_to_knowledge_store(self, record: MemoryRecord) -> None:
        """Write a memory record to the persistent KnowledgeStore."""
        kind = "belief" if record.layer == "long_term" else ("skill" if record.layer == "skill" else "observation")
        
        content_data = {"content": record.content}
        self.long_term_store.store(
            kind,
            json.dumps(content_data),
            confidence=min(record.importance + 0.3, 1.0),
            source=f"memory_{record.layer}"
        )

    def retrieve(self, query: str, limit: int = 5) -> List[MemoryRecord]:
        """Retrieve memories relevant to a query using semantic matching."""
        results = []
        
        # Search long-term store (persistent knowledge)
        for record in self.long_term_store.retrieve(query, limit=limit):
            if "belief" in record.kind or "lesson" in record.kind:
                results.append(record)
        
        # Search experience layer — recent failures and successes are highly relevant
        for record in self.experience_layer[-10:]:  # last 10 experiences
            score = self._compute_similarity(query, record.content)
            if score > 0.3:
                results.append((record, score))
        
        # Search short-term — recent context
        for record in self.short_term[-5:]:
            score = self._compute_similarity(query, record.content)
            if score > 0.2:
                results.append((record, score))
        
        # Sort by relevance and deduplicate
        seen_ids = set()
        final_results = []
        for r in sorted(results, key=lambda x: -(x[1] or -float("inf"))):
            record = r[0] if isinstance(r, tuple) else r
            if record.id not in seen_ids:
                seen_ids.add(record.id)
                final_results.append(record)
        
        return final_results[:limit]

    def retrieve_by_kind(self, kind: str, limit: int = 10) -> List[MemoryRecord]:
        """Retrieve all memories of a specific type."""
        if kind == "belief" or kind == "long_term":
            return self.long_term_store.get_by_kind("belief")[:limit]
        elif kind == "skill":
            skills = self.skills_store.get_by_kind("skill")
            records = []
            for skill in skills:
                content = json.loads(skill.content)
                record = MemoryRecord(
                    id=f"skill_{content['name']}",
                    layer="skill",
                    content=json.dumps(content),
                    created_at=utc_now(),
                    importance=0.9,
                )
                records.append(record)
            return records[:limit]

    def _compute_similarity(self, query: str, memory_content: str) -> float:
        """Compute relevance score between a query and memory content."""
        # Jaccard similarity on token sets (fast, exact matching)
        query_tokens = set(query.lower().split())
        mem_tokens = set(memory_content.lower().split())
        
        if not query_tokens or not mem_tokens:
            return 0.0
        
        intersection = len(query_tokens & mem_tokens)
        union = len(query_tokens | mem_tokens)
        
        # Jaccard + recency bonus
        jaccard = intersection / max(union, 1)
        
        # Bonus for recent memories
        from datetime import timedelta
        age_days = (utc_now() - record.created_at).days / 14.0 if "record" in locals() else 7.0
        recency_bonus = 1.0 / max(1.0, age_days)
        
        return jaccard * 0.7 + min(recency_bonus, 0.3)

    def get_working_memory(self) -> Dict[str, MemoryRecord]:
        """Get the current active working memory context."""
        return self.working_memory.copy()

    def forget(self, record_id: str) -> bool:
        """Delete a specific memory (for self-correction)."""
        if record_id in self.working_memory:
            del self.working_memory[record_id]
            return True
        
        for i, r in enumerate(self.short_term):
            if r.id == record_id:
                self.short_term.pop(i)
                return True

        # Delete from persistent store (expensive — rebuild index)
        new_data = []
        for rec in self.long_term_store._data:
            if rec.id != record_id:
                new_data.append(rec)
        
        self.long_term_store._data = new_data
        
        # Rebuild kind index
        self.long_term_store._index_by_kind = {}
        for i, r in enumerate(new_data):
            if r.kind not in self.long_term_store._index_by_kind:
                self.long_term_store._index_by_kind[r.kind] = []
            self.long_term_store._index_by_kind[r.kind].append(i)

        return True

    def get_experience(self, last_n: int = 20) -> List[MemoryRecord]:
        """Get the most recent N experiences (actions taken and outcomes)."""
        return self.experience_layer[-last_n:]

    @property
    def total_size(self) -> Dict[str, int]:
        """Memory size breakdown by layer."""
        return {
            "working": len(self.working_memory),
            "short_term": len(self.short_term),
            "experience": len(self.experience_layer),
            "long_term": self.long_term_store.size(),
            "skills": self.skills_store.size(),
        }

    def summarize_state(self) -> str:
        """Return a human-readable summary of the memory system state."""
        total = sum(self.total_size.values())
        
        parts = [
            f"Memory State Summary (total records: {total})",
            "-" * 50,
            f"  Working Memory:     {self.total_size['working']}",
            f"  Short-term (recent):{self.total_size['short_term']} (<1hr window)",
            f"  Long-term:          {self.total_size['long_term']} (persistent beliefs/facts)",
            f"  Skills:             {self.total_size['skills']} (procedural knowledge)",
        ]
        
        return "\n".join(parts)
