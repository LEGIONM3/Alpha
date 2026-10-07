"""Failure Recovery Framework: Detects failure modes, applies retries with backoff, substitutes fallbacks, and triggers rollbacks."""

import time
import random
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from alpha.tools.protocol import ToolResult, ToolCapability
from alpha.tools.registry import ToolRegistry

class FailureMode(str, Enum):
    TOOL_CRASH = "tool_crash"
    TIMEOUT = "timeout"
    BAD_OUTPUT = "bad_output"
    MISSING_FILES = "missing_files"
    INVALID_SCHEMA = "invalid_schema"
    SECURITY_VIOLATION = "security_violation"
    UNKNOWN = "unknown"

class RecoveryStrategy(str, Enum):
    RETRY = "retry"
    FALLBACK_TOOL = "fallback_tool"
    ROLLBACK = "rollback"
    FAIL_AND_ESCALATE = "fail_and_escalate"

class FailureDiagnosis(BaseModel):
    failure_mode: FailureMode
    root_cause: str
    recommended_strategy: RecoveryStrategy
    suggested_modifications: Dict[str, Any] = Field(default_factory=dict)

class FailureDetector:
    """Classifies tool result failures into distinct operational modes."""

    @staticmethod
    def diagnose(result: ToolResult) -> FailureDiagnosis:
        if result.success:
            return FailureDiagnosis(
                failure_mode=FailureMode.UNKNOWN,
                root_cause="None",
                recommended_strategy=RecoveryStrategy.RETRY
            )

        err = (result.error or "").lower()

        if "timed out" in err or "timeouterror" in err:
            return FailureDiagnosis(
                failure_mode=FailureMode.TIMEOUT,
                root_cause=result.error or "Execution time limit exceeded",
                recommended_strategy=RecoveryStrategy.RETRY,
                suggested_modifications={"increase_timeout": True}
            )

        if "security policy violation" in err:
            return FailureDiagnosis(
                failure_mode=FailureMode.SECURITY_VIOLATION,
                root_cause=result.error or "Unauthorized permission requested",
                recommended_strategy=RecoveryStrategy.FALLBACK_TOOL
            )

        if "not found" in err or "no such file" in err or "missing" in err:
            return FailureDiagnosis(
                failure_mode=FailureMode.MISSING_FILES,
                root_cause=result.error or "Referenced file or artifact does not exist",
                recommended_strategy=RecoveryStrategy.RETRY
            )

        if "schema" in err or "validation failed" in err or "jsondecodeerror" in err:
            return FailureDiagnosis(
                failure_mode=FailureMode.INVALID_SCHEMA,
                root_cause=result.error or "Output did not conform to schema specification",
                recommended_strategy=RecoveryStrategy.RETRY
            )

        if "traceback" in err or "exception" in err or "error" in err:
            return FailureDiagnosis(
                failure_mode=FailureMode.TOOL_CRASH,
                root_cause=result.error or "Unhandled exception during tool execution",
                recommended_strategy=RecoveryStrategy.FALLBACK_TOOL
            )

        return FailureDiagnosis(
            failure_mode=FailureMode.BAD_OUTPUT,
            root_cause=result.error or "Malformed output",
            recommended_strategy=RecoveryStrategy.RETRY
        )

class RecoverySystem:
    """Coordinates automatic recovery, exponential backoff, tool fallbacks, and rollbacks."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self._fallback_mappings: Dict[str, str] = {
            # Standard tool fallback mappings
            "browser_navigate": "browser_extract",
            "git_clone": "fs_read_file",
            "api_rest_request": "api_webhook_trigger",
        }

    def register_fallback(self, primary_tool: str, fallback_tool: str) -> None:
        self._fallback_mappings[primary_tool] = fallback_tool

    def get_fallback_tool(self, primary_tool: str) -> Optional[str]:
        # Explicit configured fallback
        if primary_tool in self._fallback_mappings:
            cand = self._fallback_mappings[primary_tool]
            if self.registry.has_tool(cand):
                return cand
        return None

    def calculate_backoff(self, retry_attempt: int, base_seconds: float = 0.05, max_seconds: float = 1.0) -> float:
        """Calculate exponential backoff with jitter."""
        delay = min(max_seconds, base_seconds * (2 ** (retry_attempt - 1)))
        jitter = random.uniform(0.0, 0.2 * delay)
        return delay + jitter
