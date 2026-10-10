"""Legion-to-Mac Authenticated Client & Laya Contract Adapter (Phase 4 & Phase 5).

Used by Project Alpha on the Windows 11 Lenovo Legion to communicate with the
Apple Silicon MacBook computer-use agent over an authenticated private interface.
Also implements ILayaObservationTool and ILayaExecutionTool for seamless
registration in LayaContractRegistry.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import uuid
import requests

from alpha.computer_use.contracts import (
    ILayaExecutionTool,
    ILayaObservationTool,
    LayaCapabilityType,
    LayaManifest,
)
from alpha.computer_use.mac_agent.policy import is_private_bind_address
from alpha.computer_use.mac_agent.schemas import (
    CancelTaskRequest,
    CapabilitiesResponse,
    EmergencyStopRequest,
    ExecuteActionRequest,
    ExecuteActionResponse,
    HealthResponse,
    MacActionType,
    MacModality,
    MacObservationPayload,
    ObserveRequest,
    ObserveResponse,
    SemanticLocator,
    TaskStatusResponse,
    VerifyOutcomeRequest,
    VerifyOutcomeResponse,
)
from alpha.computer_use.permissions import ApprovalToken, ComputerActionType, PermissionGate
from alpha.observation_engine.observation import Observation

logger = logging.getLogger("alpha.computer_use.mac_agent.client")


class MacAgentClientError(RuntimeError):
    """Raised when communication, authentication, or validation with the Mac Agent fails."""

    def __init__(self, message: str, status_code: int = 0, error_code: str = "CLIENT_ERROR"):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class MacComputerUseClient(ILayaObservationTool, ILayaExecutionTool):
    """Authenticated HTTP client for the Apple Silicon Mac Agent."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout_seconds: float = 15.0,
        permission_gate: Optional[PermissionGate] = None,
    ):
        resolved_url = (base_url or os.environ.get("ALPHA_MAC_AGENT_URL", "http://127.0.0.1:8765")).rstrip("/")
        # Verify the target host is on a private/loopback/VPN interface
        host_part = resolved_url.split("://")[-1].split("/")[0].split(":")[0]
        if not is_private_bind_address(host_part):
            raise ValueError(
                f"Security policy violation: Refusing to connect MacComputerUseClient to non-private host '{host_part}'."
            )
        self.base_url = resolved_url
        self.auth_token = (
            auth_token if auth_token is not None else os.environ.get("ALPHA_MAC_AGENT_TOKEN", "")
        )
        self.timeout_seconds = timeout_seconds
        self.permission_gate = permission_gate or PermissionGate()
        self._session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.auth_token:
            hdrs["Authorization"] = f"Bearer {self.auth_token}"
        return hdrs

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MacAgentClientError(
                f"Connection to Mac Agent at {url} failed: {exc}",
                status_code=0,
                error_code="CONNECTION_FAILED",
            ) from exc

        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}

        if resp.status_code >= 400:
            raise MacAgentClientError(
                data.get("error", f"HTTP {resp.status_code}"),
                status_code=resp.status_code,
                error_code=data.get("error_code", f"HTTP_{resp.status_code}"),
            )
        return data

    def _post(self, path: str, payload: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=timeout or self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MacAgentClientError(
                f"Connection to Mac Agent at {url} failed: {exc}",
                status_code=0,
                error_code="CONNECTION_FAILED",
            ) from exc

        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}

        if resp.status_code >= 400:
            raise MacAgentClientError(
                data.get("error", f"HTTP {resp.status_code}"),
                status_code=resp.status_code,
                error_code=data.get("error_code", f"HTTP_{resp.status_code}"),
            )
        return data

    # =========================================================================
    # Typed Versioned API Operations (/v1)
    # =========================================================================

    def health(self) -> HealthResponse:
        data = self._get("/v1/health")
        return HealthResponse.model_validate(data)

    def capabilities(self) -> CapabilitiesResponse:
        data = self._get("/v1/capabilities")
        return CapabilitiesResponse.model_validate(data)

    def observe(self, req: ObserveRequest) -> ObserveResponse:
        data = self._post("/v1/observe", req.model_dump())
        return ObserveResponse.model_validate(data)

    def execute_action(self, req: ExecuteActionRequest) -> ExecuteActionResponse:
        data = self._post(
            "/v1/execute_action",
            req.model_dump(),
            timeout=max(self.timeout_seconds, req.timeout_seconds + 5.0),
        )
        return ExecuteActionResponse.model_validate(data)

    def verify_outcome(self, req: VerifyOutcomeRequest) -> VerifyOutcomeResponse:
        data = self._post("/v1/verify_outcome", req.model_dump())
        return VerifyOutcomeResponse.model_validate(data)

    def get_task_status(self, task_id: str) -> TaskStatusResponse:
        data = self._get(f"/v1/task_status/{task_id}")
        return TaskStatusResponse.model_validate(data)

    def cancel_task(self, task_id: str, reason: str = "Cancelled by Alpha controller") -> TaskStatusResponse:
        req = CancelTaskRequest(task_id=task_id, reason=reason)
        data = self._post("/v1/cancel_task", req.model_dump())
        return TaskStatusResponse.model_validate(data)

    def emergency_stop(self, reason: str = "Emergency stop from Alpha controller", reset: bool = False) -> HealthResponse:
        req = EmergencyStopRequest(reason=reason, reset=reset)
        data = self._post("/v1/emergency_stop", req.model_dump())
        return HealthResponse.model_validate(data)

    @staticmethod
    def to_alpha_observation(mac_obs: MacObservationPayload, step_index: int = 0, phase: str = "obs") -> Observation:
        """Converts MacObservationPayload into Alpha's canonical Observation model."""
        evidence_dict = {
            "url": mac_obs.url,
            "title": mac_obs.page_title or mac_obs.window_title,
            "active_application": mac_obs.active_application,
            "window_title": mac_obs.window_title,
            "modality": mac_obs.modality.value,
            "elements_count": len(mac_obs.elements),
            "elements": [
                {
                    "id": e.element_id,
                    "role": e.role,
                    "name": e.name,
                    "label": e.label,
                    "value": e.value,
                    "visible": e.visible,
                    "enabled": e.enabled,
                }
                for e in mac_obs.elements
            ],
            "dom_summary": mac_obs.visible_text_summary,
            "untrusted_content_envelope": mac_obs.untrusted_content_envelope,
            "state_hash": mac_obs.state_hash,
            "timestamp": mac_obs.timestamp,
        }
        return Observation(
            observation_id=f"{mac_obs.observation_id}_{phase}_s{step_index}",
            source=f"mac_agent:{mac_obs.modality.value.lower()}:{(mac_obs.url or mac_obs.active_application or 'session')[:40]}",
            source_type="laya_observation",
            evidence=evidence_dict,
            confidence=1.0,
            verification_status="VERIFIED",
            metadata={
                "step_index": step_index,
                "phase": phase,
                "state_hash": mac_obs.state_hash,
                **mac_obs.metadata,
            },
        )

    # =========================================================================
    # Laya Contract Implementations (ILayaObservationTool & ILayaExecutionTool)
    # =========================================================================

    def capture_screen_observation(self, metadata: Optional[Dict[str, Any]] = None) -> Observation:
        task_id = (metadata or {}).get("task_id", f"obs_task_{uuid.uuid4().hex[:6]}")
        resp = self.observe(ObserveRequest(task_id=task_id, modality=MacModality.BROWSER, include_screenshot=True))
        if resp.ok and resp.observation:
            return self.to_alpha_observation(resp.observation, phase="screen")
        return Observation(
            observation_id=f"mac_obs_err_{uuid.uuid4().hex[:8]}",
            source="mac_agent",
            source_type="laya_observation",
            evidence={"error": resp.error, "error_code": resp.error_code},
            confidence=0.0,
            verification_status="FALSIFIED",
        )

    def inspect_window_hierarchy(self) -> List[Observation]:
        return [self.capture_screen_observation()]

    def get_observation_manifest(self) -> LayaManifest:
        return LayaManifest(
            provider_name="AlphaMacAgent",
            version="1.0.0",
            capability_type=LayaCapabilityType.OBSERVATION,
            supported_actions=["BROWSER_OBSERVE", "NATIVE_INSPECT_WINDOW"],
        )

    def execute_ui_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        approval_token: ApprovalToken,
    ) -> Dict[str, Any]:
        allowed, reason = self.permission_gate.check_permission(
            ComputerActionType.COMPUTER_TASK,
            target=parameters.get("target", action),
            token=approval_token,
        )
        if not allowed:
            return {"ok": False, "error": reason, "error_code": "PERMISSION_DENIED"}

        req = ExecuteActionRequest(
            task_id=parameters.get("task_id", f"ui_{uuid.uuid4().hex[:6]}"),
            modality=MacModality(parameters.get("modality", "BROWSER")),
            action_type=MacActionType(action),
            locator=SemanticLocator.model_validate(parameters["locator"]) if "locator" in parameters else None,
            text=parameters.get("text"),
            url=parameters.get("url"),
            app_name=parameters.get("app_name"),
            dry_run=bool(parameters.get("dry_run", False)),
            consequential_confirmed_by_user=bool(parameters.get("consequential_confirmed_by_user", False)),
        )
        resp = self.execute_action(req)
        return resp.model_dump()

    def execute_terminal_action(
        self,
        command: str,
        approval_token: ApprovalToken,
        timeout_seconds: float = 30.0,
    ) -> Dict[str, Any]:
        # By strict Phase 4 security rules, arbitrary remote shell commands are prohibited on the Mac Agent API
        return {
            "ok": False,
            "error_code": "REMOTE_SHELL_FORBIDDEN",
            "error": "Unrestricted remote shell execution is prohibited by Mac Agent security policy.",
        }

    def get_execution_manifest(self) -> LayaManifest:
        return LayaManifest(
            provider_name="AlphaMacAgent",
            version="1.0.0",
            capability_type=LayaCapabilityType.EXECUTION,
            requires_approval_token=True,
            supported_actions=[a.value for a in MacActionType],
        )
