"""Core Observation Data Model for Project Alpha.

Represents an empirical, verifiable piece of external reality:
- source: identifier of origin (e.g. Filesystem, Git, Test, Documentation)
- timestamp: ISO 8601 acquisition time
- evidence: exact verifiable contents, AST signatures, git diffs, test outputs
- confidence: calibrated certainty score (0.0 to 1.0)
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator


class Observation(BaseModel):
    """Represents a verified piece of external reality acquired during an autonomous cycle."""
    source: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence: str
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    category: str = Field(default="general")
    hash: str = Field(default="")

    # Compatibility property for legacy code referencing observation.content
    @property
    def content(self) -> str:
        return self.evidence

    @model_validator(mode="before")
    @classmethod
    def sync_pre_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync content <-> evidence
            if "content" in data and "evidence" not in data:
                data["evidence"] = data["content"]
            elif "evidence" in data and "content" not in data:
                data["content"] = data["evidence"]
            if "timestamp" not in data or not data["timestamp"]:
                data["timestamp"] = datetime.now(timezone.utc).isoformat()
        return data

    @model_validator(mode="after")
    def compute_hash_if_missing(self) -> "Observation":
        if not self.hash:
            raw = f"{self.source}:{self.category}:{self.evidence}"
            h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            object.__setattr__(self, "hash", h)
        return self


# Backwards compatibility alias
ObservationRecord = Observation
