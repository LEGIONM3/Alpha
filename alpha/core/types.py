"""Core types, enums, and base interfaces for Alpha Phase 1 Scaffolding."""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class TaskStatus(str, Enum):
    """Lifecycle status of a node in the Task Tree."""
    PENDING = "pending"          # Created, waiting for dependencies or scheduling
    READY = "ready"              # All dependencies satisfied, ready for execution
    IN_PROGRESS = "in_progress"  # Currently being processed
    COMPLETED = "completed"      # Successfully executed and validated
    FAILED = "failed"            # Failed execution after maximum retries
    BLOCKED = "blocked"          # Dependency failed or unmet precondition
    SKIPPED = "skipped"          # Omitted due to conditional branch or alternative path

class TaskLevel(int, Enum):
    """Hierarchical level of task decomposition."""
    GOAL = 0             # High-level objective
    SUB_GOAL = 1         # Distinct milestone or component objective
    TASK = 2             # Discrete unit of work
    ATOMIC_ACTION = 3    # Single-step, unambiguous primitive for low-reasoning SLM

class MemoryType(str, Enum):
    """Taxonomy of memories handled by the Memory Manager."""
    OBSERVATION = "observation"          # Environmental feedback or runtime observations
    PROJECT_KNOWLEDGE = "project_knowledge" # Domain rules, configurations, system facts
    COMPLETED_TASK = "completed_task"    # Record of a successfully completed task
    FAILURE = "failure"                  # Record of a failed execution with error cause
    LESSON_LEARNED = "lesson_learned"    # Distilled cognitive heuristic from reflection

class KnowledgeType(str, Enum):
    """Categories of documents in the Knowledge Store."""
    DOCUMENT = "document"                # General specifications, guides, and manuals
    PROJECT_NOTE = "project_note"        # Informal notes, meeting takeaways, scratch ideas
    ARCHITECTURE_DECISION = "adr"       # Architecture Decision Records
    RESEARCH = "research"                # Literature reviews, benchmarks, API references
    HEURISTIC = "heuristic"              # High-value procedural rules

class ValidationType(str, Enum):
    """Deterministic validation methods for planner steps."""
    DETERMINISTIC_ASSERTION = "assertion" # Python assertion / programmatic boolean check
    REGEX_PATTERN = "regex"              # Output must match regex pattern
    SCHEMA_MATCH = "schema"              # Output must deserialize into Pydantic schema
    KEYWORD_PRESENCE = "keyword"        # Output must contain specific critical substrings
    REFLECTION_RUBRIC = "rubric"         # Evaluated via reflection scoring

class ComplexityScore(int, Enum):
    """Complexity estimate for task execution."""
    TRIVIAL = 1    # Direct lookup or 1-line format conversion
    LOW = 2        # Single atomic step with unambiguous inputs
    MEDIUM = 3     # Multi-variable coordination or conditional logic
    HIGH = 4       # Synthesis of multiple sources with constraint checking
    EXTREME = 5    # Needs further decomposition before a weak model can handle

class ExecutionResult(BaseModel):
    """Standardized output of any executed task or atomic step."""
    task_id: str
    success: bool
    raw_output: str
    parsed_output: Optional[Any] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    tokens_used_est: int = 0
    executed_at: datetime = Field(default_factory=utc_now)
