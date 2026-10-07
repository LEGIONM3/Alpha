"""Unit tests for Component 5: Experience Log."""

import pytest
from alpha.experience.logger import ExperienceLogger
from alpha.experience.schemas import ExperienceRecord, ExperienceQuery

@pytest.fixture
def logger():
    return ExperienceLogger(db_path=":memory:")

def test_record_and_query_experience(logger):
    rec1 = ExperienceRecord(
        task_id="task-100",
        step_number=1,
        action_taken="Generate JWT token",
        model_output="token_xyz",
        success=True,
        reward=1.0,
        latency_ms=15.0,
        tokens_used_est=120
    )
    rec2 = ExperienceRecord(
        task_id="task-101",
        step_number=2,
        action_taken="Verify signature",
        model_output="invalid key format",
        success=False,
        reward=-0.5,
        latency_ms=22.0,
        tokens_used_est=140,
        error_message="Key syntax rejected"
    )

    logger.record(rec1)
    logger.record(rec2)

    # Query all
    all_records = logger.query(ExperienceQuery(limit=10))
    assert len(all_records) == 2

    # Query failures only
    failures = logger.query(ExperienceQuery(only_failures=True))
    assert len(failures) == 1
    assert failures[0].task_id == "task-101"

    # Query statistics
    stats = logger.get_statistics()
    assert stats["total_runs"] == 2
    assert stats["successful_runs"] == 1
    assert stats["failed_runs"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["avg_reward"] == 0.25
