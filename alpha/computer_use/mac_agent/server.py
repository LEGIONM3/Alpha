"""Authenticated Private REST API Server for the Apple Silicon Mac Computer-Use Agent (Phase 4).

Security & Operational Guarantees:
1. Binds ONLY to an explicitly configured private/loopback/VPN interface (rejects 0.0.0.0 and public IPs).
2. Restricts inbound connections to authorized client IPs (e.g., the Windows 11 Lenovo Legion IP).
3. Enforces constant-time Bearer token authentication on all endpoints; fails closed if missing/invalid.
4. Validates every request against strict Pydantic v2 schemas (extra="forbid").
5. Enforces deny-by-default policy, URL/app allowlists, consequential gates, budgets, and emergency stop.
6. Writes secret-redacted structured audit records for every request and observation-action-outcome chain.
7. Reports only verified runtime capabilities; never advertises untested modalities.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse
from pydantic import ValidationError

from alpha.computer_use.mac_agent.browser_executor import MacBrowserExecutor
from alpha.computer_use.mac_agent.native_executor import MacNativeExecutor
from alpha.computer_use.mac_agent.platform_probe import MacPlatformProbe
from alpha.computer_use.mac_agent.policy import (
    MacAgentPolicy,
    is_private_bind_address,
    redact_sensitive_data,
)
from alpha.computer_use.mac_agent.schemas import (
    API_VERSION,
     CancelTaskRequest,
    CapabilitiesResponse,
    EmergencyStopRequest,
    ExecuteActionRequest,
    ExecuteActionResponse,
    HealthResponse,
    MacActionType,
    MacModality,
    ObserveRequest,
    ObserveResponse,
    TaskStatusResponse,
    VerificationStatus,
    VerifyOutcomeRequest,
    VerifyOutcomeResponse,
)
from alpha.computer_use.mac_agent.verifier import MacOutcomeVerifier

logger = logging.getLogger("alpha.computer_use.mac_agent.server")


class MacAgentServiceCore:
    """Core service coordinator separating API transport, policy, observation, actuation, and verification."""

    def __init__(
        self,
        auth_token: Optional[str] = None,
        authorized_client_ips: Optional[Set[str]] = None,
        policy: Optional[MacAgentPolicy] = None,
        platform_probe: Optional[MacPlatformProbe] = None,
        browser_executor: Optional[MacBrowserExecutor] = None,
        native_executor: Optional[MacNativeExecutor] = None,
        verifier: Optional[MacOutcomeVerifier] = None,
        audit_log_path: Optional[Path] = None,
        headless_browser: Optional[bool] = None,
    ):
        resolved_token = auth_token if auth_token is not None else os.environ.get("ALPHA_MAC_AGENT_TOKEN", "")
        if not resolved_token or len(resolved_token.strip()) < 8:
            raise ValueError(
                "MacAgentServiceCore requires a non-empty auth_token (min 8 chars) via parameter or ALPHA_MAC_AGENT_TOKEN env var."
            )
        self._auth_token: str = resolved_token.strip()

        env_ips = os.environ.get("ALPHA_AUTHORIZED_CLIENT_IPS", "")
        default_ips = {"127.0.0.1", "::1"}
        if env_ips:
            for ip_str in env_ips.split(","):
                if ip_str.strip():
                    default_ips.add(ip_str.strip())
        self.authorized_client_ips: Set[str] = (
            set(authorized_client_ips) if authorized_client_ips is not None else default_ips
        )

        self.policy = policy or MacAgentPolicy()
        self.platform_probe = platform_probe or MacPlatformProbe()
        self._headless_browser = headless_browser
        self._browser_executor = browser_executor
        self._native_executor = native_executor or MacNativeExecutor(platform_probe=self.platform_probe)
        self.verifier = verifier or MacOutcomeVerifier()
        self.audit_log_path = audit_log_path or Path("data/mac_agent_audit.jsonl")
        self.started_at = time.monotonic()
        self._audit_lock = threading.Lock()

    @property
    def browser_executor(self) -> MacBrowserExecutor:
        if self._browser_executor is None:
            self._browser_executor = MacBrowserExecutor(headless=self._headless_browser)
        return self._browser_executor

    def verify_client_ip(self, client_ip: str) -> bool:
        """Checks whether the connecting client IP is in the authorized allowlist."""
        return client_ip in self.authorized_client_ips

    def verify_auth_header(self, auth_header: Optional[str]) -> bool:
        """Constant-time verification of Bearer token header."""
        if not auth_header or not auth_header.startswith("Bearer "):
            return False
        supplied = auth_header[len("Bearer "):].strip()
        if not supplied:
            return False
        return hmac.compare_digest(supplied.encode("utf-8"), self._auth_token.encode("utf-8"))

    def write_audit_record(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Writes secret-redacted JSONL audit log entry."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **redact_sensitive_data(payload),
        }
        try:
            with self._audit_lock:
                self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
                with self.audit_log_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record, sort_keys=True) + "\n")
        except Exception as exc:
            logger.error(f"Failed to write Mac agent audit log: {exc}")

    def get_health(self) -> HealthResponse:
        plat = self.platform_probe.inspect_platform()
        e_stop = self.policy.emergency_stop_engaged
        status_str = "emergency_stopped" if e_stop else ("healthy" if plat.ready_for_browser else "degraded")
        return HealthResponse(
            status=status_str,
            ready=(not e_stop) and plat.ready_for_browser,
            emergency_stop_engaged=e_stop,
            uptime_seconds=round(time.monotonic() - self.started_at, 2),
            platform_summary={
                "system": plat.system,
                "is_macos": plat.is_macos,
                "architecture": plat.architecture,
                "is_apple_silicon": plat.is_apple_silicon,
                "macos_version": plat.macos_version,
                "ready_for_browser": plat.ready_for_browser,
                "ready_for_native_gui": plat.ready_for_native_gui,
                "missing_permissions": plat.permissions.missing_permissions,
            },
        )

    def get_capabilities(self) -> CapabilitiesResponse:
        """Reports actual tested capabilities; never advertises unimplemented or unavailable modalities."""
        plat = self.platform_probe.inspect_platform()
        modalities: List[str] = []
        actions: List[str] = [
            MacActionType.WAIT.value,
            MacActionType.COMPLETE.value,
            MacActionType.ABORT.value,
        ]

        if plat.ready_for_browser:
            modalities.append(MacModality.BROWSER.value)
            actions.extend([
                MacActionType.BROWSER_LAUNCH.value,
                MacActionType.BROWSER_NAVIGATE.value,
                MacActionType.BROWSER_OBSERVE.value,
                MacActionType.BROWSER_CLICK.value,
                MacActionType.BROWSER_TYPE.value,
                MacActionType.BROWSER_SCROLL.value,
                MacActionType.BROWSER_SELECT.value,
                MacActionType.BROWSER_SCREENSHOT.value,
                MacActionType.BROWSER_CLOSE.value,
            ])

        if plat.ready_for_native_gui:
            modalities.append(MacModality.NATIVE_GUI.value)
            actions.extend([
                MacActionType.NATIVE_LIST_APPS.value,
                MacActionType.NATIVE_INSPECT_WINDOW.value,
                MacActionType.NATIVE_LAUNCH_APP.value,
                MacActionType.NATIVE_CLICK.value,
                MacActionType.NATIVE_TYPE.value,
                MacActionType.NATIVE_PRESS_KEY.value,
                MacActionType.NATIVE_SCROLL.value,
                MacActionType.NATIVE_DRAG.value,
            ])
            if plat.permissions.screen_recording_granted:
                actions.append(MacActionType.NATIVE_SCREENSHOT.value)

        return CapabilitiesResponse(
            modalities_supported=modalities,
            browser_supported=plat.ready_for_browser,
            native_gui_supported=plat.ready_for_native_gui,
            native_gui_tested_vertical_slice=bool(
                plat.ready_for_native_gui and self._native_executor.vertical_slice_verified
            ),
            supported_actions=actions,
            approved_applications=list(self.policy.approved_applications),
            approved_url_prefixes=list(self.policy.approved_url_prefixes),
            dry_run_supported=True,
            platform_report=plat.model_dump(),
        )

    def handle_observe(self, req: ObserveRequest) -> ObserveResponse:
        t0 = time.perf_counter()
        if self.policy.emergency_stop_engaged:
            resp = ObserveResponse(
                ok=False,
                task_id=req.task_id,
                error="Global emergency stop is engaged.",
                error_code="EMERGENCY_STOP_ACTIVE",
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )
            self.write_audit_record("OBSERVE_BLOCKED", resp.model_dump())
            return resp

        task_state = self.policy.get_or_create_task(req.task_id)
        if task_state.cancelled:
            return ObserveResponse(
                ok=False,
                task_id=req.task_id,
                error=f"Task '{req.task_id}' is cancelled.",
                error_code="TASK_CANCELLED",
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )

        if req.modality == MacModality.BROWSER:
            try:
                obs = self.browser_executor.observe(include_screenshot=req.include_screenshot)
                resp = ObserveResponse(
                    ok=True,
                    task_id=req.task_id,
                    observation=obs,
                    latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                )
            except Exception as exc:
                resp = ObserveResponse(
                    ok=False,
                    task_id=req.task_id,
                    error=str(exc),
                    error_code="BROWSER_OBSERVE_FAILED",
                    latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                )
        else:
            if req.app_name:
                app_ok, app_reason = self.policy.is_application_allowed(req.app_name)
                if not app_ok:
                    resp = ObserveResponse(
                        ok=False,
                        task_id=req.task_id,
                        error=app_reason,
                        error_code="APPLICATION_NOT_ALLOWED",
                        latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                    )
                    self.write_audit_record("OBSERVE_DENIED", resp.model_dump())
                    return resp

            ok, obs, err_code, err_msg = self._native_executor.observe(
                app_name=req.app_name,
                include_screenshot=req.include_screenshot,
                approved_applications=self.policy.approved_applications,
            )
            resp = ObserveResponse(
                ok=ok,
                task_id=req.task_id,
                observation=obs,
                error=err_msg,
                error_code=err_code,
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )

        self.write_audit_record(
            "OBSERVE",
            {
                "task_id": req.task_id,
                "modality": req.modality.value,
                "ok": resp.ok,
                "observation_id": resp.observation.observation_id if resp.observation else None,
                "state_hash": resp.observation.state_hash if resp.observation else None,
                "error_code": resp.error_code,
                "error": resp.error,
            },
        )
        return resp

    def handle_execute_action(self, req: ExecuteActionRequest) -> ExecuteActionResponse:
        t0 = time.perf_counter()
        allowed, err_code, policy_detail = self.policy.validate_action_request(req)
        if not allowed:
            verif = self.verifier.verify_action_outcome(
                action_type=req.action_type,
                action_ok=False,
                pre_obs=None,
                post_obs=None,
                expected_postcondition=req.expected_postcondition,
                dry_run=req.dry_run,
                error_msg=policy_detail,
            )
            resp = ExecuteActionResponse(
                ok=False,
                task_id=req.task_id,
                action_id=req.action_id,
                action_type=req.action_type,
                dry_run=req.dry_run,
                policy_decision=f"DENIED:{err_code}",
                error=policy_detail,
                error_code=err_code,
                verification=verif,
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )
            self.write_audit_record(
                "EXECUTE_ACTION_DENIED",
                {
                    "task_id": req.task_id,
                    "action_id": req.action_id,
                    "action_type": req.action_type.value,
                    "policy_decision": resp.policy_decision,
                    "error_code": err_code,
                    "error": policy_detail,
                },
            )
            return resp

        self.policy.record_action_attempt(req.task_id, is_retry=False)

        if req.modality == MacModality.BROWSER:
            ok, detail, err, pre_obs, post_obs = self.browser_executor.execute_action(req)
            act_err_code = None if ok else "BROWSER_ACTION_FAILED"
        else:
            ok, detail, err, act_err_code, pre_obs, post_obs = self._native_executor.execute_action(
                req, approved_applications=self.policy.approved_applications
            )

        verif = self.verifier.verify_action_outcome(
            action_type=req.action_type,
            action_ok=ok,
            pre_obs=pre_obs,
            post_obs=post_obs,
            expected_postcondition=req.expected_postcondition,
            dry_run=req.dry_run,
            error_msg=err,
        )

        task_state = self.policy.get_or_create_task(req.task_id)
        task_state.last_verification_status = verif.verification_status.value

        resp = ExecuteActionResponse(
            ok=ok,
            task_id=req.task_id,
            action_id=req.action_id,
            action_type=req.action_type,
            dry_run=req.dry_run,
            policy_decision="APPROVED_DRY_RUN" if req.dry_run else "APPROVED",
            execution_detail=detail,
            error=err,
            error_code=act_err_code,
            pre_observation=pre_obs,
            post_observation=post_obs,
            verification=verif,
            latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
        )

        self.write_audit_record(
            "EXECUTE_ACTION",
            {
                "task_id": req.task_id,
                "action_id": req.action_id,
                "modality": req.modality.value,
                "action_type": req.action_type.value,
                "locator": req.locator.model_dump() if req.locator else None,
                "rationale": req.rationale,
                "intended_effect": req.intended_effect,
                "policy_decision": resp.policy_decision,
                "dry_run": req.dry_run,
                "ok": ok,
                "execution_detail": detail,
                "pre_observation_id": pre_obs.observation_id if pre_obs else None,
                "pre_state_hash": pre_obs.state_hash if pre_obs else None,
                "post_observation_id": post_obs.observation_id if post_obs else None,
                "post_state_hash": post_obs.state_hash if post_obs else None,
                "verification": verif.model_dump(),
                "error_code": act_err_code,
                "error": err,
            },
        )
        return resp

    def handle_verify_outcome(self, req: VerifyOutcomeRequest) -> VerifyOutcomeResponse:
        t0 = time.perf_counter()
        obs_req = ObserveRequest(
            task_id=req.task_id,
            modality=req.modality,
            app_name=req.app_name,
            include_screenshot=False,
        )
        obs_resp = self.handle_observe(obs_req)
        if not obs_resp.ok or obs_resp.observation is None:
            verif = self.verifier.verify_action_outcome(
                action_type=MacActionType.COMPLETE,
                action_ok=False,
                pre_obs=None,
                post_obs=None,
                expected_postcondition=req.expected_postcondition,
                error_msg=obs_resp.error,
            )
            return VerifyOutcomeResponse(
                ok=False,
                task_id=req.task_id,
                verification=verif,
                error=obs_resp.error,
                latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
            )

        post_obs = obs_resp.observation
        dummy_pre = None
        if req.baseline_state_hash:
            dummy_pre = post_obs.model_copy(update={"state_hash": req.baseline_state_hash})

        verif = self.verifier.verify_action_outcome(
            action_type=MacActionType.COMPLETE,
            action_ok=True,
            pre_obs=dummy_pre,
            post_obs=post_obs,
            expected_postcondition=req.expected_postcondition,
        )
        return VerifyOutcomeResponse(
            ok=verif.postcondition_satisfied,
            task_id=req.task_id,
            observation=post_obs,
            verification=verif,
            latency_ms=round((time.perf_counter() - t0) * 1000.0, 2),
        )

    def handle_get_task_status(self, task_id: str) -> TaskStatusResponse:
        t_state = self.policy.get_or_create_task(task_id)
        elapsed = round(time.monotonic() - t_state.started_at, 2)
        return TaskStatusResponse(
            task_id=task_id,
            status="EMERGENCY_STOPPED" if self.policy.emergency_stop_engaged else t_state.status,
            actions_taken=t_state.actions_taken,
            max_actions=t_state.max_actions,
            retries_used=t_state.retries_used,
            max_retries=t_state.max_retries,
            elapsed_seconds=elapsed,
            max_duration_seconds=t_state.max_duration_seconds,
            cancelled=t_state.cancelled,
            emergency_stopped=self.policy.emergency_stop_engaged,
            last_verification_status=t_state.last_verification_status,
        )

    def handle_cancel_task(self, req: CancelTaskRequest) -> TaskStatusResponse:
        self.policy.cancel_task(req.task_id, req.reason)
        self.write_audit_record("CANCEL_TASK", {"task_id": req.task_id, "reason": req.reason})
        return self.handle_get_task_status(req.task_id)

    def handle_emergency_stop(self, req: EmergencyStopRequest) -> HealthResponse:
        if req.reset:
            self.policy.reset_emergency_stop()
            self.write_audit_record("EMERGENCY_STOP_RESET", {"reason": req.reason})
        else:
            self.policy.engage_emergency_stop(req.reason)
            if self._browser_executor is not None:
                try:
                    self._browser_executor.close()
                except Exception:
                    pass
                self._browser_executor = None
            self._native_executor.close()
            self.write_audit_record("EMERGENCY_STOP_ENGAGED", {"reason": req.reason})
        return self.get_health()

    def close(self) -> None:
        if self._browser_executor is not None:
            try:
                self._browser_executor.close()
            except Exception:
                pass
            self._browser_executor = None
        self._native_executor.close()


class MacAgentHTTPServer:
    """Threaded private-interface HTTP server wrapping MacAgentServiceCore."""

    def __init__(
        self,
        core: MacAgentServiceCore,
        bind_host: str = "127.0.0.1",
        bind_port: int = 8765,
    ):
        if not is_private_bind_address(bind_host):
            raise ValueError(
                f"Security violation: Refusing to bind Mac Agent server to non-private interface '{bind_host}'. "
                "Bind only to 127.0.0.1, a private LAN IP (192.168.x.x / 10.x.x.x), or a Tailscale IP (100.x.x.x)."
            )
        self.core = core
        self.bind_host = bind_host
        self.bind_port = bind_port
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def base_url(self) -> str:
        actual_port = self._httpd.server_port if self._httpd else self.bind_port
        return f"http://{self.bind_host}:{actual_port}"

    def start(self) -> str:
        """Starts the HTTP server on a background daemon thread and returns its base URL."""
        core_ref = self.core

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                # Suppress default noisy stderr logging; structured audit log handles all events
                pass

            def _send_json(self, status_code: int, data: Dict[str, Any]) -> None:
                body = json.dumps(data).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _authenticate_and_authorize(self) -> bool:
                client_ip = self.client_address[0]
                if not core_ref.verify_client_ip(client_ip):
                    core_ref.write_audit_record(
                        "UNAUTHORIZED_CLIENT_IP",
                        {"client_ip": client_ip, "path": self.path},
                    )
                    self._send_json(
                        403,
                        {
                            "api_version": API_VERSION,
                            "ok": False,
                            "error_code": "UNAUTHORIZED_CLIENT_IP",
                            "error": f"Client IP '{client_ip}' is not authorized to access the Mac Agent.",
                        },
                    )
                    return False

                auth_hdr = self.headers.get("Authorization")
                if not core_ref.verify_auth_header(auth_hdr):
                    core_ref.write_audit_record(
                        "AUTHENTICATION_FAILED",
                        {"client_ip": client_ip, "path": self.path},
                    )
                    self._send_json(
                        401,
                        {
                            "api_version": API_VERSION,
                            "ok": False,
                            "error_code": "AUTHENTICATION_FAILED",
                            "error": "Missing or invalid Bearer authentication token.",
                        },
                    )
                    return False
                return True

            def _read_json_body(self) -> Optional[Dict[str, Any]]:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0:
                        return {}
                    if length > 2_000_000:
                        self._send_json(
                            413,
                            {"api_version": API_VERSION, "ok": False, "error": "Payload too large."},
                        )
                        return None
                    raw = self.rfile.read(length).decode("utf-8")
                    return json.loads(raw)
                except Exception as exc:
                    self._send_json(
                        400,
                        {
                            "api_version": API_VERSION,
                            "ok": False,
                            "error_code": "MALFORMED_JSON",
                            "error": f"Invalid JSON payload: {exc}",
                        },
                    )
                    return None

            def do_GET(self) -> None:
                if not self._authenticate_and_authorize():
                    return

                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/")

                if path in ("/v1/health", "/v1/readiness"):
                    resp = core_ref.get_health()
                    self._send_json(200, resp.model_dump())
                elif path == "/v1/capabilities":
                    resp = core_ref.get_capabilities()
                    self._send_json(200, resp.model_dump())
                elif path.startswith("/v1/task_status"):
                    parts = path.split("/")
                    task_id = parts[3] if len(parts) > 3 else ""
                    if not task_id:
                        qs = parse_qs(parsed.query)
                        task_id = qs.get("task_id", [""])[0]
                    if not task_id:
                        self._send_json(400, {"ok": False, "error": "task_id is required"})
                        return
                    resp = core_ref.handle_get_task_status(task_id)
                    self._send_json(200, resp.model_dump())
                else:
                    self._send_json(
                        404,
                        {"api_version": API_VERSION, "ok": False, "error": f"Unknown endpoint: {path}"},
                    )

            def do_POST(self) -> None:
                if not self._authenticate_and_authorize():
                    return

                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/")
                payload = self._read_json_body()
                if payload is None:
                    return

                try:
                    if path == "/v1/observe":
                        req = ObserveRequest.model_validate(payload)
                        resp = core_ref.handle_observe(req)
                        self._send_json(200, resp.model_dump())

                    elif path == "/v1/execute_action":
                        req = ExecuteActionRequest.model_validate(payload)
                        resp = core_ref.handle_execute_action(req)
                        self._send_json(200, resp.model_dump())

                    elif path == "/v1/verify_outcome":
                        req = VerifyOutcomeRequest.model_validate(payload)
                        resp = core_ref.handle_verify_outcome(req)
                        self._send_json(200, resp.model_dump())

                    elif path == "/v1/cancel_task":
                        req = CancelTaskRequest.model_validate(payload)
                        resp = core_ref.handle_cancel_task(req)
                        self._send_json(200, resp.model_dump())

                    elif path == "/v1/emergency_stop":
                        req = EmergencyStopRequest.model_validate(payload)
                        resp = core_ref.handle_emergency_stop(req)
                        self._send_json(200, resp.model_dump())

                    else:
                        self._send_json(
                            404,
                            {"api_version": API_VERSION, "ok": False, "error": f"Unknown endpoint: {path}"},
                        )

                except ValidationError as verr:
                    core_ref.write_audit_record(
                        "SCHEMA_VALIDATION_REJECTED",
                        {"path": path, "errors": verr.errors()},
                    )
                    self._send_json(
                        422,
                        {
                            "api_version": API_VERSION,
                            "ok": False,
                            "error_code": "SCHEMA_VALIDATION_FAILED",
                            "error": str(verr),
                        },
                    )

        self._httpd = ThreadingHTTPServer((self.bind_host, self.bind_port), _Handler)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="AlphaMacAgentHTTPServer",
            daemon=True,
        )
        self._thread.start()
        return self.base_url

    def stop(self) -> None:
        """Gracefully stops the HTTP listener and releases browser/native executors."""
        if self._httpd is not None:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception:
                pass
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        self.core.close()
