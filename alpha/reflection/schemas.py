"""Schemas for the Reflection Engine and Evaluation Rubrics."""

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from alpha.core.types import utc_now

class RubricScore(BaseModel):
    """Evaluation score for a specific dimension."""
    criterion: str  # e.g., "correctness", "constraint_adherence", "completeness", "format"
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    feedback: str = ""

class FailurePattern(BaseModel):
    """Categorized failure mode observed during execution."""
    category: str  # e.g., "schema_violation", "hallucination", "timeout", "incomplete"
    symptom: str
    suspected_cause: str

class LessonLearned(BaseModel):
    """Distilled operational insight to be stored into permanent memory."""
    rule: str
    trigger: str
    rationale: str

class ReflectionReport(BaseModel):
    """Comprehensive output of the Reflection Engine."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_id: str
    step_number: Optional[int] = None
    overall_score: float = Field(default=1.0, ge=0.0, le=1.0)
    passed: bool = True
    what_worked: List[str] = Field(default_factory=list)
    what_failed: List[str] = Field(default_factory=list)
    what_can_improve: List[str] = Field(default_factory=list)
    rubric_scores: List[RubricScore] = Field(default_factory=list)
    failures: List[FailurePattern] = Field(default_factory=list)
    lessons: List[LessonLearned] = Field(default_factory=list)
    corrective_prompt_injection: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
