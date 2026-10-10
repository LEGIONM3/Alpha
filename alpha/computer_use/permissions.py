"""Computer Use Integration: Permissions and Safety Gate for Laya.

Defines initial open permissions:
- READ
- OBSERVE
- NAVIGATE
- INSPECT

Restricted actions require verified approval:
- WRITE
- EXECUTE
- DELETE
- MODIFY_CONFIG
"""

from __future__ import annotations

from enum import Enum
import hashlib
import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("alpha.computer_use.permissions")


class ComputerActionType(str, Enum):
    # Initial Open Permissions (Safe / Passive Sensory)
    READ = "READ"
    OBSERVE = "OBSERVE"
    NAVIGATE = "NAVIGATE"
    INSPECT = "INSPECT"
    BROWSE = "BROWSE"
    DESKTOP_INSPECT = "DESKTOP_INSPECT"

    # Restricted Actions (Active / Mutative - Require Approval)
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    DELETE = "DELETE"
    MODIFY_CONFIG = "MODIFY_CONFIG"
    COMPUTER_TASK = "COMPUTER_TASK"
    FILE_EDIT = "WRITE"
    TERMINAL_EXEC = "EXECUTE"
    UI_MOTOR = "COMPUTER_TASK"


class ApprovalToken(BaseModel):
    """Cryptographic-style approval token for restricted actions."""
    action_type: ComputerActionType
    target: str
    approved_by: str = "SYSTEM_GOVERNANCE"
    reason: str
    timestamp: float = Field(default_factory=time.time)
    token_hash: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.token_hash:
            raw = f"{self.action_type}:{self.target}:{self.approved_by}:{self.timestamp}:{self.reason}"
            self.token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def is_valid(self, max_age_seconds: float = 300.0) -> bool:
        return (time.time() - self.timestamp) <= max_age_seconds


class PermissionGate:
    """Enforces Laya's operational boundaries."""

    OPEN_PERMISSIONS = {
        ComputerActionType.READ,
        ComputerActionType.OBSERVE,
        ComputerActionType.NAVIGATE,
        ComputerActionType.INSPECT,
        ComputerActionType.BROWSE,
        ComputerActionType.DESKTOP_INSPECT,
    }

    RESTRICTED_PERMISSIONS = {
        ComputerActionType.WRITE,
        ComputerActionType.EXECUTE,
        ComputerActionType.DELETE,
        ComputerActionType.MODIFY_CONFIG,
        ComputerActionType.COMPUTER_TASK,
    }

    def check_permission(
        self,
        action: ComputerActionType,
        target: str,
        token: Optional[ApprovalToken] = None
    ) -> Tuple[bool, str]:
        """Validates if Laya is authorized to perform the action."""
        if action in self.OPEN_PERMISSIONS:
            return True, f"Action {action.value} on '{target}' is permitted under initial open permissions."

        if action in self.RESTRICTED_PERMISSIONS:
            if not token:
                msg = f"RESTRICTED ACTION BLOCKED: {action.value} on '{target}' requires explicit approval token."
                logger.warning(msg)
                return False, msg

            if not token.is_valid():
                msg = f"RESTRICTED ACTION BLOCKED: Approval token for {action.value} has expired."
                logger.warning(msg)
                return False, msg

            if token.action_type != action:
                msg = f"RESTRICTED ACTION BLOCKED: Token action mismatch ({token.action_type} != {action})."
                logger.warning(msg)
                return False, msg

            return True, f"Action {action.value} approved by {token.approved_by} for reason: {token.reason}."

        return False, f"Unknown action type: {action}"

    def request_approval(
        self,
        action_type: ComputerActionType,
        target: str,
        justification: str,
        approved_by: str = "SYSTEM_GOVERNANCE"
    ) -> ApprovalToken:
        """Issues an approval token for an authorized action."""
        return ApprovalToken(
            action_type=action_type,
            target=target,
            reason=justification,
            approved_by=approved_by
        )

    def verify_token(
        self,
        token: Optional[ApprovalToken],
        action_type: ComputerActionType,
        target: str
    ) -> bool:
        """Verifies if an approval token is valid for the target action."""
        allowed, _ = self.check_permission(action_type, target, token)
        return allowed
