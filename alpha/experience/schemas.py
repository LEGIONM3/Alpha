"""Schemas for the Experience Log audit trail."""

import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from alpha.core.types import utc_now

class ExperienceRecord(BaseModel):
    """Immutable audit record for every action, decision, result, failure, and reward."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    step_number: Optional[int] = None
    goal_id: Optional[str] = None
    decision_context: Dict[str, Any] = Field(default_factory=dict, description="Context snapshot passed to model")
    action_taken: str = Field(description="Action/Prompt attempted")
    model_output: str = Field(description="Model output")
    success: bool = True
    reward: float = Field(default=0.0, ge=-1.0, le=1.0, description="Evaluated reward signal (-1 to +1)")
    latency_ms: float = 0.0
    tokens_used_est: int = 0
    reflection_report_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)

class ExperienceQuery(BaseModel):
    """Query filter for the experience log."""
    task_id: Optional[str] = None
    goal_id: Optional[str] = None
    only_failures: bool = False
    only_successes: bool = False
    min_reward: Optional[float] = None
    limit: int = 50
