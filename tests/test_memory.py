"""Unit tests for Component 1: Memory Manager."""

import pytest
from alpha.core.types import MemoryType
from alpha.memory.manager import MemoryManager
from alpha.memory.storage import MemoryStorage

@pytest.fixture
def memory_manager():
    storage = MemoryStorage(db_path=":memory:")
    return MemoryManager(storage=storage)

def test_store_and_retrieve_observation(memory_manager):
    obs_item = memory_manager.store_observation("Database connection established on port 5432")
    assert obs_item.memory_type == MemoryType.OBSERVATION
    assert "port 5432" in obs_item.content
    assert len(memory_manager.working_memory.recent_observations) == 1

def test_store_and_retrieve_lesson(memory_manager):
    lesson = memory_manager.store_lesson_learned(
        rule="Always quote identifiers in SQLite",
        context_trigger="sqlite_query",
        rationale="Prevents keyword conflict errors"
    )
    assert lesson.memory_type == MemoryType.LESSON_LEARNED
    
    # Retrieve with FTS
    results = memory_manager.retrieve(query_text="SQLite identifiers", memory_types=[MemoryType.LESSON_LEARNED])
    assert len(results) >= 1
    assert "Always quote identifiers" in results[0].content

def test_store_completed_task_and_failure(memory_manager):
    memory_manager.store_completed_task(
        task_id="t-1",
        description="Initialize database",
        result_summary="Tables created successfully",
        latency_ms=12.5
    )
    memory_manager.store_failure(
        task_id="t-2",
        description="Migrate schema",
        error_message="Table already exists",
        root_cause="Missing IF NOT EXISTS clause"
    )

    failures = memory_manager.retrieve(query_text="Migrate schema", memory_types=[MemoryType.FAILURE])
    assert len(failures) == 1
    assert "Missing IF NOT EXISTS" in failures[0].content

def test_context_budget_formatting(memory_manager):
    memory_manager.working_memory.set_variable("env", "production")
    memory_manager.store_lesson_learned("Check disk space prior to writing", "io_ops")

    context_str = memory_manager.format_context_for_prompt("disk space io", max_tokens=200)
    assert "### Active Variables:" in context_str
    assert "env: production" in context_str
    assert "Check disk space" in context_str
