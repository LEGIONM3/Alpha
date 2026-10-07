"""Model Learning History Records: Dataclass and models for execution audit."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field


class ExecutionRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_name: str
    task_domain: str
    prompt_genome_id: Optional[str] = None
    strategy_used: str
    prompt_preview: str
    output_preview: str
    score: float = Field(..., ge=0.0, le=1.0)
    latency_ms: float = Field(..., ge=0.0)
    had_failure: bool = False
    failure_types: List[str] = Field(default_factory=list)
    amplification_factor: Optional[float] = None
