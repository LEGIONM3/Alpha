"""Agent Communication Network: Traceable, Versioned, Auditable Messages."""

import time
import uuid
import hashlib
import json
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    PROPOSAL = "proposal"
    CHALLENGE = "challenge"
    REVIEW = "review"
    APPROVAL = "approval"
    ESCALATION = "escalation"
    CANCELLATION = "cancellation"

class MessagePriority(int, Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

class AgentMessage(BaseModel):
    """Immutable, versioned, traceable message between cognitive agents."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_version: str = "3.0"
    sender_id: str
    sender_role: str
    recipient_id: str  # specific agent id or "*" for broadcast
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit & Tracing
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_msg_id: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    audit_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.audit_hash:
            self.audit_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA-256 integrity hash for auditing."""
        content = f"{self.protocol_version}:{self.sender_id}:{self.recipient_id}:{self.message_type.value}:{self.priority.value}:{self.trace_id}:{self.created_at}:{json.dumps(self.payload, sort_keys=True, default=str)}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify message has not been tampered with."""
        return self.audit_hash == self.compute_hash()
