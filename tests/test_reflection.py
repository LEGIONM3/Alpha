"""Unit tests for Component 4: Reflection Engine."""

import pytest
from alpha.core.types import ExecutionResult, ValidationType
from alpha.memory.manager import MemoryManager
from alpha.planner.schemas import ExecutionStep, ValidationContract
from alpha.reflection.engine import ReflectionEngine

@pytest.fixture
def reflection_setup():
    memory = MemoryManager()
    reflection = ReflectionEngine(memory_manager=memory, quality_threshold=0.75)
    return memory, reflection

def test_reflection_on_success(reflection_setup):
    memory, reflection = reflection_setup
    step = ExecutionStep(
        step_number=1,
        task_id="t-1",
        name="Format JSON output",
        instruction="Return status object in JSON",
        validation_contracts=[
            ValidationContract(
                validation_type=ValidationType.SCHEMA_MATCH,
                rule="valid_json_object",
                description="Must be valid JSON"
            )
        ]
    )
    result = ExecutionResult(task_id="t-1", success=True, raw_output='{"status": "ok"}')

    report = reflection.reflect_on_step(step, result, raw_output=result.raw_output)
    assert report.passed is True
    assert report.overall_score >= 0.75
    assert len(report.what_worked) > 0
    assert len(report.what_failed) == 0

def test_reflection_on_contract_failure_and_corrective_prompt(reflection_setup):
    memory, reflection = reflection_setup
    step = ExecutionStep(
        step_number=1,
        task_id="t-2",
        name="Generate JSON configuration",
        instruction="Generate json config",
        validation_contracts=[
            ValidationContract(
                validation_type=ValidationType.SCHEMA_MATCH,
                rule="valid_json",
                description="Must be valid JSON"
            )
        ]
    )
    # Malformed output
    raw = "Sure! Here is the JSON: { malformed: json without quotes }"
    result = ExecutionResult(task_id="t-2", success=False, raw_output=raw)

    report = reflection.reflect_on_step(step, result, raw_output=raw)
    assert report.passed is False
    assert len(report.what_failed) > 0
    assert report.corrective_prompt_injection is not None
    assert "PREVIOUS ATTEMPT FAILED" in report.corrective_prompt_injection
    
    # Check that lesson was stored in memory
    lessons = memory.retrieve(query_text="JSON", limit=5)
    assert len(lessons) >= 1
