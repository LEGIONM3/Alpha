"""Memory Manager component for Alpha Phase 1.
Implements the pipeline: Input -> Memory Processing -> Memory Storage -> Retrieval.
"""

from typing import Any, Dict, List, Optional
from alpha.core.types import MemoryType
from alpha.memory.schemas import MemoryItem, MemoryQuery, WorkingMemory
from alpha.memory.storage import MemoryStorage

class MemoryManager:
    """Orchestrates Working Memory, Long-Term Memory Storage, and Token-Budgeted Retrieval."""

    def __init__(self, storage: Optional[MemoryStorage] = None, db_path: Optional[str] = None):
        self.storage = storage or MemoryStorage(db_path=db_path or ":memory:")
        self.working_memory = WorkingMemory()

    # --- Processing & Ingestion Pipeline (Input -> Processing -> Storage) ---

    def process_and_store(
        self,
        memory_type: MemoryType,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> MemoryItem:
        """Core pipeline: Ingest raw text -> Process/Sanitize -> Build Item -> Persist."""
        processed_content = self._preprocess_content(content)
        extracted_tags = list(set((tags or []) + self._auto_tag(processed_content, memory_type)))
        
        item = MemoryItem(
            memory_type=memory_type,
            content=processed_content,
            tags=extracted_tags,
            metadata=metadata or {},
            importance=max(0.0, min(1.0, importance))
        )
        return self.storage.save(item)

    def store_observation(self, observation: str, context: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """Record environmental observation or step result."""
        self.working_memory.add_observation(observation)
        return self.process_and_store(
            memory_type=MemoryType.OBSERVATION,
            content=observation,
            tags=["observation", "runtime"],
            metadata=context or {},
            importance=0.4
        )

    def store_project_knowledge(self, knowledge: str, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """Store permanent domain rule or project specification fact."""
        return self.process_and_store(
            memory_type=MemoryType.PROJECT_KNOWLEDGE,
            content=knowledge,
            tags=(tags or []) + ["knowledge", "domain"],
            metadata=metadata or {},
            importance=0.8
        )

    def store_completed_task(self, task_id: str, description: str, result_summary: str, latency_ms: float = 0.0) -> MemoryItem:
        """Store successful outcome of a task."""
        content = f"Task '{description}' (ID: {task_id}) succeeded. Result: {result_summary}"
        return self.process_and_store(
            memory_type=MemoryType.COMPLETED_TASK,
            content=content,
            tags=["task", "success", task_id],
            metadata={"task_id": task_id, "latency_ms": latency_ms},
            importance=0.6
        )

    def store_failure(self, task_id: str, description: str, error_message: str, root_cause: Optional[str] = None) -> MemoryItem:
        """Store failure record so weak models don't repeat the same error."""
        content = f"Task '{description}' (ID: {task_id}) FAILED with error: {error_message}"
        if root_cause:
            content += f" | Root Cause: {root_cause}"
        return self.process_and_store(
            memory_type=MemoryType.FAILURE,
            content=content,
            tags=["task", "failure", "warning", task_id],
            metadata={"task_id": task_id, "error": error_message, "root_cause": root_cause},
            importance=0.85
        )

    def store_lesson_learned(self, rule: str, context_trigger: str, rationale: Optional[str] = None) -> MemoryItem:
        """Store distilled heuristic rule discovered through reflection."""
        content = f"RULE: {rule} | WHEN: {context_trigger}"
        if rationale:
            content += f" | WHY: {rationale}"
        return self.process_and_store(
            memory_type=MemoryType.LESSON_LEARNED,
            content=content,
            tags=["lesson", "heuristic", "reflection"],
            metadata={"rule": rule, "trigger": context_trigger, "rationale": rationale},
            importance=0.9
        )

    # --- Retrieval & Context Formatting ---

    def retrieve(
        self,
        query_text: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 5,
        max_tokens: int = 600
    ) -> List[MemoryItem]:
        """Retrieve relevant memories matching query within token constraints."""
        query = MemoryQuery(
            query_text=query_text,
            memory_types=memory_types,
            limit=limit,
            max_tokens=max_tokens
        )
        return self.storage.search(query)

    def retrieve_relevant_lessons(self, context_text: str, limit: int = 3) -> List[MemoryItem]:
        """Retrieve distilled heuristics and past failures matching current task."""
        return self.storage.search(MemoryQuery(
            query_text=context_text,
            memory_types=[MemoryType.LESSON_LEARNED, MemoryType.FAILURE],
            limit=limit,
            min_importance=0.6
        ))

    def format_context_for_prompt(self, task_description: str, max_tokens: int = 600) -> str:
        """Format working scratchpad and retrieved memories into a high-density, low-token injection string for SLMs."""
        retrieved = self.retrieve(query_text=task_description, limit=5, max_tokens=max_tokens)
        
        lines: List[str] = []
        if self.working_memory.variables:
            lines.append("### Active Variables:")
            for k, v in self.working_memory.variables.items():
                lines.append(f"- {k}: {v}")
                
        if self.working_memory.recent_observations:
            lines.append("### Recent Observations:")
            for obs in self.working_memory.recent_observations[-3:]:
                lines.append(f"- {obs}")
                
        if retrieved:
            lines.append("### Relevant Memory & Lessons:")
            for item in retrieved:
                prefix = f"[{item.memory_type.value.upper()}]"
                lines.append(f"- {prefix} {item.content}")

        return "\n".join(lines) if lines else "(No prior memories relevant)"

    # --- Internal Helpers ---

    def _preprocess_content(self, raw: str) -> str:
        """Clean and normalize text before persistence."""
        return " ".join(raw.strip().split())

    def _auto_tag(self, text: str, mtype: MemoryType) -> List[str]:
        """Extract lightweight domain tags."""
        tags = [mtype.value]
        text_lower = text.lower()
        keywords = ["schema", "database", "api", "json", "timeout", "syntax", "validation", "error", "auth"]
        for kw in keywords:
            if kw in text_lower:
                tags.append(kw)
        return tags
