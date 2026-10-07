"""Failure Analysis Models: Schemas for tracking model failure modes."""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class FailureType(str, Enum):
    HALLUCINATION = "hallucination"
    REASONING_GAP = "reasoning_gap"
    LOGIC_CONTRADICTION = "logic_contradiction"
    INCONSISTENCY = "inconsistency"
    INSTRUCTION_VIOLATION = "instruction_violation"
    CONFIDENCE_MISCALIBRATION = "confidence_miscalibration"


class FailureReport(BaseModel):
    failure_id: str = Field(default_factory=lambda: f"fail_{uuid.uuid4().hex[:8]}")
    failure_type: FailureType
    detected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    description: str
    evidence: List[str] = Field(default_factory=list)
    remediation_strategy: str
    location_context: Optional[str] = None
