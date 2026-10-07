"""Memory schemas and data contracts for Memory Manager."""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from alpha.core.types import MemoryType, utc_now

class MemoryItem(BaseModel):
    """A discrete unit of stored memory."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)
    last_accessed_at: datetime = Field(default_factory=utc_now)
    
    def estimate_tokens(self) -> int:
        """Heuristic token count estimation (~4 chars per token)."""
        return max(1, len(self.content) // 4)

class WorkingMemory(BaseModel):
    """Transient working scratchpad for the currently active execution context."""
    active_goal_id: Optional[str] = None
    active_task_id: Optional[str] = None
    scratchpad: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, str] = Field(default_factory=dict)
    recent_observations: List[str] = Field(default_factory=list)
    max_observations: int = 10
    
    def add_observation(self, obs: str) -> None:
        self.recent_observations.append(obs)
        if len(self.recent_observations) > self.max_observations:
            self.recent_observations.pop(0)
            
    def set_variable(self, key: str, value: str) -> None:
        self.variables[key] = value
        
    def get_variable(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.variables.get(key, default)
        
    def clear(self) -> None:
        self.scratchpad.clear()
        self.variables.clear()
        self.recent_observations.clear()

class MemoryQuery(BaseModel):
    """Query parameters for retrieval from persistent memory."""
    query_text: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    limit: int = 5
    min_importance: float = 0.0
    max_tokens: Optional[int] = 600
