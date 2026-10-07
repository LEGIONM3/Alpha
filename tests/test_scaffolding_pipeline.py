"""End-to-End Pipeline test: Validating cognitive scaffolding behavior on a weak model."""

import pytest
from alpha.core.engine import AlphaEngine
from alpha.core.model_adapter import MockWeakModel
from alpha.experience.schemas import ExperienceQuery

def test_end_to_end_scaffolding_success():
    """Test standard goal decomposition and execution through scaffolding."""
    model = MockWeakModel(failure_on_first_try=False)
    engine = AlphaEngine(model=model, db_path=":memory:")

    # Store some initial knowledge and heuristic
    engine.knowledge.store_document(
        title="Production Configuration Standards",
        content="Configuration parameters must be structured with explicit bounds and timeout fields."
    )
    engine.memory.store_lesson_learned(
        rule="Format all system metrics in milliseconds",
        context_trigger="metrics_generation"
    )

    result = engine.execute_goal(
        goal="Configure production database caching and connection pool",
        goal_name="DB Cache Setup"
    )

    assert result["success"] is True
    assert result["completed_steps"] == result["total_steps"]
    assert len(result["results"]) >= 3

    # Check experience log recorded all steps
    records = engine.experience.query(ExperienceQuery(limit=50))
    assert len(records) >= 3
    assert all(r.success is True for r in records)
    assert all(r.reward == 1.0 for r in records)

def test_end_to_end_scaffolding_recovery_from_failure():
    """Test that cognitive scaffolding detects failure, formulates reflection, and self-corrects the weak model."""
    # Model will fail on first attempt of JSON step
    model = MockWeakModel(failure_on_first_try=True)
    engine = AlphaEngine(model=model, db_path=":memory:")

    result = engine.execute_goal(
        goal="Generate API rate limiter parameter specification",
        goal_name="Rate Limiter Spec"
    )

    assert result["success"] is True
    # Verify that experience log recorded both the failure and the subsequent success
    stats = engine.experience.get_statistics()
    assert stats["total_runs"] >= 4  # 3 steps + 1 retry
    assert stats["failed_runs"] >= 1
    assert stats["successful_runs"] >= 3

    # Verify lessons were accumulated in memory
    lessons = engine.memory.retrieve(query_text="format", limit=10)
    assert len(lessons) >= 1
