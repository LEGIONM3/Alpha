"""Schemas for Knowledge Store: Documents, ADRs, Notes, and Research."""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from alpha.core.types import KnowledgeType, utc_now

class KnowledgeDocument(BaseModel):
    """Document in the Knowledge Store."""
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    doc_type: KnowledgeType = KnowledgeType.DOCUMENT
    content: str
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def estimate_tokens(self) -> int:
        return max(1, len(self.content) // 4)

class KnowledgeQuery(BaseModel):
    """Query parameters for knowledge retrieval."""
    query_text: Optional[str] = None
    doc_types: Optional[List[KnowledgeType]] = None
    tags: Optional[List[str]] = None
    limit: int = 5
    max_tokens: Optional[int] = 500
