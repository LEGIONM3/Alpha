"""Knowledge Economy: Scientific assets treated as tradeable and rankable resources."""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class KnowledgeAsset(BaseModel):
    asset_id: str = Field(default_factory=lambda: f"asset_{uuid.uuid4().hex[:10]}")
    title: str
    target_entity_type: str  # Theory, Finding, Publication, Hypothesis
    target_entity_id: str
    domain: str
    # 5 Fundamental Knowledge Resource Metrics
    value: float = Field(default=0.80, ge=0.0, le=1.0)
    novelty: float = Field(default=0.85, ge=0.0, le=1.0)
    impact: float = Field(default=0.75, ge=0.0, le=1.0)
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    verification: float = Field(default=0.80, ge=0.0, le=1.0)
    composite_rank: float = 0.0
    citation_count: int = 0
    created_at: float = Field(default_factory=time.time)

    def calculate_composite_rank(self) -> float:
        """Composite economic-epistemic ranking."""
        raw = (
            0.25 * self.value +
            0.20 * self.novelty +
            0.25 * self.impact +
            0.15 * self.confidence +
            0.15 * self.verification
        )
        self.composite_rank = round(raw, 4)
        return self.composite_rank
