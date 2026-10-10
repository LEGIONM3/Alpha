"""Strict Versioned Request, Response, Observation, and Action Schemas for the Mac Agent.

Enforces:
- Pydantic ConfigDict(extra="forbid") to reject unknown fields and malformed payloads.
- Explicit allowlist of MacActionType primitives (zero arbitrary shell or file transfer).
- SemanticLocator validation requiring an explicit fallback reason whenever raw coordinates are used.
- Honest outcome classification (VERIFIED, FALSIFIED, INCONCLUSIVE, UNRESOLVED).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


API_VERSION = "v1"


class MacModality(str, Enum):
    BROWSER = "BROWSER"
    NATIVE_GUI = "NATIVE_GUI"


class MacActionType(str, Enum):
    # Browser primitives
    BROWSER_LAUNCH = "BROWSER_LAUNCH"
    BROWSER_NAVIGATE = "BROWSER_NAVIGATE"
    BROWSER_OBSERVE = "BROWSER_OBSERVE"
    BROWSER_CLICK = "BROWSER_CLICK"
    BROWSER_TYPE = "BROWSER_TYPE"
    BROWSER_SCROLL = "BROWSER_SCROLL"
    BROWSER_SELECT = "BROWSER_SELECT"
    BROWSER_SCREENSHOT = "BROWSER_SCREENSHOT"
    BROWSER_CLOSE = "BROWSER_CLOSE"

    # Native macOS Accessibility / Quartz primitives
    NATIVE_LIST_APPS = "NATIVE_LIST_APPS"
    NATIVE_INSPECT_WINDOW = "NATIVE_INSPECT_WINDOW"
    NATIVE_LAUNCH_APP = "NATIVE_LAUNCH_APP"
    NATIVE_CLICK = "NATIVE_CLICK"
    NATIVE_TYPE = "NATIVE_TYPE"
    NATIVE_PRESS_KEY = "NATIVE_PRESS_KEY"
    NATIVE_SCROLL = "NATIVE_SCROLL"
    NATIVE_DRAG = "NATIVE_DRAG"
    NATIVE_SCREENSHOT = "NATIVE_SCREENSHOT"

    # Control primitives
    WAIT = "WAIT"
    COMPLETE = "COMPLETE"
    ABORT = "ABORT"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FALSIFIED = "FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNRESOLVED = "UNRESOLVED"


class LocatorStrategy(str, Enum):
    ROLE = "role"
    LABEL = "label"
    TEXT = "text"
    PLACEHOLDER = "placeholder"
    TEST_ID = "test_id"
    ELEMENT_ID = "element_id"
    CSS = "css"
    COORDINATES = "coordinates"


class SemanticLocator(BaseModel):
    """Semantic-first element locator.

    Requires an explicit `coordinate_fallback_reason` if `by == 'coordinates'`.
    """
    model_config = ConfigDict(extra="forbid")

    by: LocatorStrategy = LocatorStrategy.ROLE
    value: str = ""
    role: Optional[str] = None
    name: Optional[str] = None
    exact: bool = False
    x: Optional[int] = None
    y: Optional[int] = None
    target_x: Optional[int] = None
    target_y: Optional[int] = None
    coordinate_fallback_reason: Optional[str] = None

    @model_validator(mode="after")
    def _validate_locator(self) -> "SemanticLocator":
        if self.by == LocatorStrategy.COORDINATES:
            if self.x is None or self.y is None:
                raise ValueError("Coordinate locator requires integer 'x' and 'y' values.")
            if not self.coordinate_fallback_reason or not self.coordinate_fallback_reason.strip():
                raise ValueError(
                    "Coordinate locator requires a non-empty 'coordinate_fallback_reason' explaining why semantic locators could not be used."
                )
        elif self.by == LocatorStrategy.ROLE:
            if not (self.role or self.value):
                raise ValueError("Role locator requires 'role' or 'value'.")
        else:
            if not self.value and not self.name:
                raise ValueError(f"Locator strategy '{self.by.value}' requires non-empty 'value' or 'name'.")
        return self


class ObservedUIElement(BaseModel):
    """Normalized interactive element in browser DOM or macOS Accessibility tree."""
    model_config = ConfigDict(extra="forbid")

    element_id: str
    role: str
    name: str = ""
    label: str = ""
    value: str = ""
    tag: str = ""
    visible: bool = True
    enabled: bool = True
    bbox: Optional[List[int]] = None


class MacObservationPayload(BaseModel):
    """Structured observation of the Mac browser or native desktop environment."""
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(default_factory=lambda: f"mac_obs_{uuid.uuid4().hex[:10]}")
    modality: MacModality
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    url: str = ""
    page_title: str = ""
    active_application: str = ""
    window_title: str = ""
    elements: List[ObservedUIElement] = Field(default_factory=list)
    visible_text_summary: str = ""
    untrusted_content_envelope: str = ""
    state_hash: str = ""
    screenshot_base64: Optional[str] = None
    permitted_applications: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ObserveRequest(BaseModel):
    """Request schema for `/v1/observe`."""
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    task_id: str
    modality: MacModality = MacModality.BROWSER
    app_name: Optional[str] = None
    include_screenshot: bool = False


class ObserveResponse(BaseModel):
    """Response schema for `/v1/observe`."""
    model_config = ConfigDict(extra="forbid")

    api_version: str = API_VERSION
    ok: bool
    task_id: str
    observation: Optional[MacObservationPayload] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    latency_ms: float = 0.0


class ExecuteActionRequest(BaseModel):
    """Request schema for `/v1/execute_action`."""
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    task_id: str
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    modality: MacModality = MacModality.BROWSER
    action_type: MacActionType
    locator: Optional[SemanticLocator] = None
    text: Optional[str] = None
    url: Optional[str] = None
    app_name: Optional[str] = None
    key: Optional[str] = None
    scroll_direction: Optional[Literal["up", "down", "left", "right"]] = None
    scroll_amount: int = 300
    wait_ms: int = 500
    capture_screenshot: bool = False
    rationale: str = ""
    intended_effect: str = ""
    expected_postcondition: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    consequential_confirmed_by_user: bool = False
    timeout_seconds: float = 15.0


class OutcomeVerificationDetail(BaseModel):
    """Independent verification of an executed action."""
    model_config = ConfigDict(extra="forbid")

    verification_status: VerificationStatus
    state_changed: bool
    postcondition_satisfied: bool
    pre_state_hash: str = ""
    post_state_hash: str = ""
    checks: Dict[str, bool] = Field(default_factory=dict)
    note: str = ""


class ExecuteActionResponse(BaseModel):
    """Response schema for `/v1/execute_action`."""
    model_config = ConfigDict(extra="forbid")

    api_version: str = API_VERSION
    ok: bool
    task_id: str
    action_id: str
    action_type: MacActionType
    dry_run: bool = False
    policy_decision: str = "APPROVED"
    execution_detail: str = ""
    error: Optional[str] = None
    error_code: Optional[str] = None
    pre_observation: Optional[MacObservationPayload] = None
    post_observation: Optional[MacObservationPayload] = None
    verification: Optional[OutcomeVerificationDetail] = None
    latency_ms: float = 0.0


class VerifyOutcomeRequest(BaseModel):
    """Request schema for `/v1/verify_outcome`."""
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    task_id: str
    modality: MacModality = MacModality.BROWSER
    app_name: Optional[str] = None
    expected_postcondition: Dict[str, Any]
    baseline_state_hash: Optional[str] = None


class VerifyOutcomeResponse(BaseModel):
    """Response schema for `/v1/verify_outcome`."""
    model_config = ConfigDict(extra="forbid")

    api_version: str = API_VERSION
    ok: bool
    task_id: str
    observation: Optional[MacObservationPayload] = None
    verification: OutcomeVerificationDetail
    error: Optional[str] = None
    latency_ms: float = 0.0


class CancelTaskRequest(BaseModel):
    """Request schema for `/v1/cancel_task`."""
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    task_id: str
    reason: str = "Operator requested task cancellation"


class EmergencyStopRequest(BaseModel):
    """Request schema for `/v1/emergency_stop`."""
    model_config = ConfigDict(extra="forbid")

    api_version: Literal["v1"] = "v1"
    reason: str = "Emergency stop triggered"
    reset: bool = False


class HealthResponse(BaseModel):
    """Response schema for `/v1/health` and `/v1/readiness`."""
    model_config = ConfigDict(extra="forbid")

    api_version: str = API_VERSION
    status: Literal["healthy", "degraded", "emergency_stopped"]
    ready: bool
    emergency_stop_engaged: bool
    uptime_seconds: float
    platform_summary: Dict[str, Any]


class CapabilitiesResponse(BaseModel):
    """Response schema for `/v1/capabilities`."""
    model_config = ConfigDict(extra="forbid")

    api_version: str = API_VERSION
    provider: str = "AlphaMacAgent"
    modalities_supported: List[str]
    browser_supported: bool
    native_gui_supported: bool
    native_gui_tested_vertical_slice: bool
    supported_actions: List[str]
    approved_applications: List[str]
    approved_url_prefixes: List[str]
    dry_run_supported: bool = True
    platform_report: Dict[str, Any]


class TaskStatusResponse(BaseModel):
    """Response schema for `/v1/task_status`."""
    model_config = ConfigDict(extra="forbid")

    api_version: str = API_VERSION
    task_id: str
    status: str
    actions_taken: int
    max_actions: int
    retries_used: int
    max_retries: int
    elapsed_seconds: float
    max_duration_seconds: float
    cancelled: bool
    emergency_stopped: bool
    last_verification_status: Optional[str] = None
