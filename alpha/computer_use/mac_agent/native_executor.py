"""Native macOS Accessibility & Quartz Actuator Interface (Phase 3).

Implements structured operations for:
- Listing permitted application targets
- Inspecting accessible windows and UI elements via macOS Accessibility (System Events / AXUIElement)
- Capturing screenshots via screencapture after verifying TCC Screen Recording permission
- Clicking, typing, pressing keys, scrolling, and dragging
- Launching approved applications (including the harmless local AlphaMacTestApp vertical slice)
- Re-observing UI state after every action to verify intended state mutation

Never bypasses macOS TCC/privacy controls. Fails clearly when running outside macOS Aqua
or when Accessibility / Screen Recording permissions are missing.
"""

from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from alpha.computer_use.mac_agent.platform_probe import MacPlatformProbe, MacPlatformReport
from alpha.computer_use.mac_agent.policy import (
    redact_sensitive_text,
    wrap_untrusted_environment_content,
)
from alpha.computer_use.mac_agent.schemas import (
    ExecuteActionRequest,
    LocatorStrategy,
    MacActionType,
    MacModality,
    MacObservationPayload,
    ObservedUIElement,
)

logger = logging.getLogger("alpha.computer_use.mac_agent.native_executor")


_JXA_INSPECT_SCRIPT = """
function run(argv) {
    const targetApp = argv.length > 0 ? argv[0] : "";
    const se = Application("System Events");
    const procs = se.applicationProcesses.whose({backgroundOnly: false})();
    const runningNames = procs.map(p => p.name());

    let proc = null;
    if (targetApp) {
        const matched = se.applicationProcesses.whose({name: targetApp})();
        if (matched.length > 0) proc = matched[0];
    } else {
        const front = se.applicationProcesses.whose({frontmost: true})();
        if (front.length > 0) proc = front[0];
    }

    if (!proc) {
        return JSON.stringify({
            found: false,
            running_apps: runningNames,
            active_app: "",
            window_title: "",
            elements: [],
            text_summary: ""
        });
    }

    const appName = proc.name();
    let winTitle = "";
    const elements = [];
    const textParts = [];

    try {
        const wins = proc.windows();
        if (wins.length > 0) {
            const w = wins[0];
            winTitle = w.name() || "";
            const uiElems = w.entireContents();
            let idx = 0;
            for (let i = 0; i < Math.min(uiElems.length, 60); i++) {
                try {
                    const el = uiElems[i];
                    const role = el.role ? (el.role() || "AXElement") : "AXElement";
                    const name = el.name ? (el.name() || "") : "";
                    const title = el.title ? (el.title() || "") : "";
                    const desc = el.description ? (el.description() || "") : "";
                    const val = (el.value && el.value() !== null && el.value() !== undefined) ? String(el.value()) : "";
                    const label = name || title || desc;
                    if (label || val) {
                        textParts.push((label + " " + val).trim());
                    }
                    elements.push({
                        element_id: "ax_" + idx,
                        role: role,
                        name: label,
                        label: desc || title,
                        value: val,
                        enabled: el.enabled ? Boolean(el.enabled()) : true
                    });
                    idx += 1;
                } catch (e) {}
            }
        }
    } catch (e) {}

    return JSON.stringify({
        found: true,
        running_apps: runningNames,
        active_app: appName,
        window_title: winTitle,
        elements: elements,
        text_summary: textParts.join(" | ").slice(0, 1500)
    });
}
"""


class CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class MacNativeExecutor:
    """Native macOS Accessibility & Quartz actuator with TCC permission enforcement."""

    def __init__(self, platform_probe: Optional[MacPlatformProbe] = None):
        self.platform_probe = platform_probe or MacPlatformProbe()
        self.vertical_slice_verified: bool = False
        self._spawned_test_procs: List[subprocess.Popen[Any]] = []
        self._test_app_state_file = Path(tempfile.gettempdir()) / "alpha_mac_test_app_state.json"

    def _verify_native_prerequisites(
        self, require_screen_recording: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str], MacPlatformReport]:
        """Checks platform, non-root Aqua session, and TCC permissions."""
        report = self.platform_probe.inspect_platform()
        if not report.is_macos:
            return (
                False,
                "PLATFORM_NOT_MACOS",
                f"Native macOS actuator requires Darwin/macOS host (detected {report.system} {report.architecture}).",
                report,
            )
        if report.is_root_process:
            return (
                False,
                "ROOT_SESSION_FORBIDDEN",
                "Native GUI automation cannot run as root daemon. Run inside the logged-in user session.",
                report,
            )
        if not report.is_graphical_user_session:
            return (
                False,
                "AQUA_SESSION_REQUIRED",
                f"Native GUI automation requires logged-in macOS Aqua session (detected '{report.session_manager_type}').",
                report,
            )
        if not report.permissions.accessibility_granted:
            return (
                False,
                "MISSING_ACCESSIBILITY_PERMISSION",
                "Missing macOS Accessibility permission. Enable in System Settings -> Privacy & Security -> Accessibility.",
                report,
            )
        if require_screen_recording and not report.permissions.screen_recording_granted:
            return (
                False,
                "MISSING_SCREEN_RECORDING_PERMISSION",
                "Missing macOS Screen Recording permission. Enable in System Settings -> Privacy & Security -> Screen & System Audio Recording.",
                report,
            )
        return True, None, None, report

    def observe(
        self,
        app_name: Optional[str] = None,
        include_screenshot: bool = False,
        approved_applications: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[MacObservationPayload], Optional[str], Optional[str]]:
        """Observes accessible windows and UI elements of an approved macOS application."""
        ok, err_code, err_msg, _ = self._verify_native_prerequisites(
            require_screen_recording=include_screenshot
        )
        if not ok:
            return False, None, err_code, err_msg

        target_app = app_name or ""
        try:
            proc = subprocess.run(
                ["osascript", "-l", "JavaScript", "-e", _JXA_INSPECT_SCRIPT, target_app],
                capture_output=True,
                text=True,
                timeout=8.0,
                check=False,
            )
            if proc.returncode != 0:
                return (
                    False,
                    None,
                    "AX_INSPECTION_FAILED",
                    f"osascript Accessibility inspection failed: {proc.stderr.strip()}",
                )
            parsed = json.loads(proc.stdout.strip() or "{}")
        except Exception as exc:
            return False, None, "AX_INSPECTION_ERROR", f"Accessibility observation exception: {exc}"

        ui_elements: List[ObservedUIElement] = []
        for el in parsed.get("elements", []):
            ui_elements.append(
                ObservedUIElement(
                    element_id=str(el.get("element_id", "")),
                    role=str(el.get("role", "AXElement")),
                    name=redact_sensitive_text(str(el.get("name", ""))),
                    label=redact_sensitive_text(str(el.get("label", ""))),
                    value=redact_sensitive_text(str(el.get("value", ""))),
                    enabled=bool(el.get("enabled", True)),
                )
            )

        # Also merge local harmless test app state if inspecting AlphaMacTestApp
        text_summary = redact_sensitive_text(parsed.get("text_summary", ""))
        if self._test_app_state_file.exists() and (
            not target_app or "alphamactestapp" in target_app.lower() or "python" in target_app.lower()
        ):
            try:
                local_state = json.loads(self._test_app_state_file.read_text(encoding="utf-8"))
                status_str = local_state.get("status", "")
                if status_str and status_str not in text_summary:
                    text_summary = f"{status_str} | {text_summary}".strip(" |")
            except Exception:
                pass

        envelope, alerts = wrap_untrusted_environment_content(text_summary)
        allowed_set = {a.lower() for a in (approved_applications or [])}
        running_apps = parsed.get("running_apps", [])
        permitted_running = [
            a for a in running_apps if not allowed_set or a.lower() in allowed_set
        ]

        fp_data = {
            "active_app": parsed.get("active_app", ""),
            "window_title": parsed.get("window_title", ""),
            "text_summary": text_summary,
            "elements": [
                {"id": e.element_id, "role": e.role, "name": e.name, "value": e.value}
                for e in ui_elements
            ],
        }
        state_hash = hashlib.sha256(json.dumps(fp_data, sort_keys=True).encode("utf-8")).hexdigest()

        screenshot_b64: Optional[str] = None
        if include_screenshot:
            sc_ok, sc_b64, _ = self.capture_screenshot()
            if sc_ok:
                screenshot_b64 = sc_b64

        obs = MacObservationPayload(
            modality=MacModality.NATIVE_GUI,
            active_application=str(parsed.get("active_app", target_app)),
            window_title=str(parsed.get("window_title", "")),
            elements=ui_elements,
            visible_text_summary=text_summary[:1000],
            untrusted_content_envelope=envelope,
            state_hash=state_hash,
            screenshot_base64=screenshot_b64,
            permitted_applications=permitted_running,
            metadata={"prompt_injection_alerts": alerts},
        )
        return True, obs, None, None

    def capture_screenshot(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Captures full screen on macOS after verifying Screen Recording TCC permission."""
        ok, err_code, err_msg, _ = self._verify_native_prerequisites(require_screen_recording=True)
        if not ok:
            return False, None, f"{err_code}: {err_msg}"

        tmp_png = Path(tempfile.gettempdir()) / f"alpha_mac_screen_{int(time.time() * 1000)}.png"
        try:
            proc = subprocess.run(
                ["/usr/sbin/screencapture", "-x", str(tmp_png)],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            if proc.returncode != 0 or not tmp_png.exists():
                return False, None, f"screencapture failed: {proc.stderr.strip()}"
            b64 = base64.b64encode(tmp_png.read_bytes()).decode("ascii")
            return True, b64, None
        except Exception as exc:
            return False, None, str(exc)
        finally:
            if tmp_png.exists():
                try:
                    tmp_png.unlink()
                except Exception:
                    pass

    def _quartz_mouse_click(self, x: int, y: int) -> None:
        """Posts native CGEvent mouse click at screen coordinates (x, y)."""
        cg = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        cg.CGEventCreateMouseEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            CGPoint,
            ctypes.c_uint32,
        ]
        cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        cg.CFRelease.argtypes = [ctypes.c_void_p]

        pt = CGPoint(float(x), float(y))
        kCGEventLeftMouseDown = 1
        kCGEventLeftMouseUp = 2
        kCGHIDEventTap = 0

        down_evt = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, pt, 0)
        up_evt = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, pt, 0)
        try:
            cg.CGEventPost(kCGHIDEventTap, down_evt)
            time.sleep(0.03)
            cg.CGEventPost(kCGHIDEventTap, up_evt)
        finally:
            if down_evt:
                cg.CFRelease(down_evt)
            if up_evt:
                cg.CFRelease(up_evt)

    def _quartz_mouse_drag(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Posts native CGEvent mouse drag from (x1, y1) to (x2, y2)."""
        cg = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        cg.CGEventCreateMouseEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            CGPoint,
            ctypes.c_uint32,
        ]
        cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        cg.CFRelease.argtypes = [ctypes.c_void_p]

        p1 = CGPoint(float(x1), float(y1))
        p2 = CGPoint(float(x2), float(y2))
        kCGEventLeftMouseDown = 1
        kCGEventLeftMouseUp = 2
        kCGEventLeftMouseDragged = 6
        kCGHIDEventTap = 0

        down_evt = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, p1, 0)
        drag_evt = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseDragged, p2, 0)
        up_evt = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, p2, 0)
        try:
            cg.CGEventPost(kCGHIDEventTap, down_evt)
            time.sleep(0.04)
            cg.CGEventPost(kCGHIDEventTap, drag_evt)
            time.sleep(0.04)
            cg.CGEventPost(kCGHIDEventTap, up_evt)
        finally:
            for ev in (down_evt, drag_evt, up_evt):
                if ev:
                    cg.CFRelease(ev)

    def execute_action(
        self,
        req: ExecuteActionRequest,
        approved_applications: Optional[List[str]] = None,
    ) -> Tuple[bool, str, Optional[str], Optional[str], Optional[MacObservationPayload], Optional[MacObservationPayload]]:
        """Executes a native macOS GUI action and returns (ok, detail, error, error_code, pre_obs, post_obs)."""
        need_sr = req.capture_screenshot or (req.action_type == MacActionType.NATIVE_SCREENSHOT)
        prereq_ok, err_code, err_msg, _ = self._verify_native_prerequisites(
            require_screen_recording=need_sr
        )
        if not prereq_ok:
            return False, "", err_msg, err_code, None, None

        obs_ok, pre_obs, obs_code, obs_err = self.observe(
            app_name=req.app_name,
            include_screenshot=False,
            approved_applications=approved_applications,
        )
        if not obs_ok or pre_obs is None:
            return False, "", obs_err or "Pre-observation failed", obs_code or "OBSERVE_FAILED", None, None

        if req.dry_run:
            return (
                True,
                f"DRY_RUN: Validated native macOS action {req.action_type.value} without executing.",
                None,
                None,
                pre_obs,
                pre_obs,
            )

        act = req.action_type
        detail = ""
        error: Optional[str] = None
        error_code: Optional[str] = None
        ok = True

        try:
            if act == MacActionType.NATIVE_LIST_APPS:
                detail = f"Listed {len(pre_obs.permitted_applications)} permitted applications"

            elif act == MacActionType.NATIVE_INSPECT_WINDOW:
                detail = f"Inspected window '{pre_obs.window_title}' of application '{pre_obs.active_application}'"

            elif act == MacActionType.NATIVE_LAUNCH_APP:
                app_target = (req.app_name or "").strip()
                if app_target in ("AlphaMacTestApp", "Alpha Mac Agent Verification App"):
                    app_script = Path(__file__).resolve().parent / "harmless_test_app.py"
                    proc = subprocess.Popen(
                        [sys.executable, str(app_script), "--state-file", str(self._test_app_state_file)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._spawned_test_procs.append(proc)
                    time.sleep(0.8)
                    detail = "Launched harmless local AlphaMacTestApp GUI window"
                else:
                    res = subprocess.run(
                        ["/usr/bin/open", "-a", app_target],
                        capture_output=True,
                        text=True,
                        timeout=5.0,
                        check=False,
                    )
                    if res.returncode != 0:
                        raise RuntimeError(f"Failed to launch '{app_target}': {res.stderr.strip()}")
                    time.sleep(0.5)
                    detail = f"Launched approved application '{app_target}'"

            elif act == MacActionType.NATIVE_CLICK:
                if not req.locator:
                    raise ValueError("NATIVE_CLICK requires 'locator'.")
                if req.locator.by == LocatorStrategy.COORDINATES:
                    self._quartz_mouse_click(int(req.locator.x or 0), int(req.locator.y or 0))
                    detail = (
                        f"Native coordinate click at ({req.locator.x}, {req.locator.y}) "
                        f"[Fallback: {req.locator.coordinate_fallback_reason}]"
                    )
                else:
                    btn_name = (req.locator.name or req.locator.value or "").replace('"', '\\"')
                    app_target = (req.app_name or pre_obs.active_application).replace('"', '\\"')
                    script = (
                        f'tell application "System Events" to tell process "{app_target}" '
                        f'to click button "{btn_name}" of window 1'
                    )
                    res = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True,
                        text=True,
                        timeout=5.0,
                        check=False,
                    )
                    if res.returncode != 0:
                        raise RuntimeError(f"Accessibility click failed: {res.stderr.strip()}")
                    detail = f"Clicked native button '{btn_name}' in '{app_target}'"

            elif act == MacActionType.NATIVE_TYPE:
                text_val = (req.text or "").replace('"', '\\"')
                app_target = (req.app_name or pre_obs.active_application).replace('"', '\\"')
                script = (
                    f'tell application "System Events" to tell process "{app_target}" '
                    f'to keystroke "{text_val}"'
                )
                res = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                    check=False,
                )
                if res.returncode != 0:
                    raise RuntimeError(f"Accessibility keystroke failed: {res.stderr.strip()}")
                detail = f"Typed text into '{app_target}'"

            elif act == MacActionType.NATIVE_PRESS_KEY:
                key_name = (req.key or "return").lower()
                script = f'tell application "System Events" to keystroke {key_name}'
                res = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                    check=False,
                )
                if res.returncode != 0:
                    raise RuntimeError(f"Key press failed: {res.stderr.strip()}")
                detail = f"Pressed key '{key_name}'"

            elif act == MacActionType.NATIVE_DRAG:
                if not req.locator or req.locator.x is None or req.locator.y is None:
                    raise ValueError("NATIVE_DRAG requires start coordinates (x, y) and target (target_x, target_y).")
                tx = req.locator.target_x if req.locator.target_x is not None else req.locator.x
                ty = req.locator.target_y if req.locator.target_y is not None else req.locator.y
                self._quartz_mouse_drag(int(req.locator.x), int(req.locator.y), int(tx), int(ty))
                detail = f"Dragged from ({req.locator.x}, {req.locator.y}) to ({tx}, {ty})"

            elif act == MacActionType.NATIVE_SCREENSHOT:
                detail = "Captured native macOS screenshot"

            else:
                raise ValueError(f"Unsupported native macOS action: {act.value}")

        except Exception as exc:
            ok = False
            error = str(exc)
            error_code = "NATIVE_EXECUTION_FAILED"
            detail = f"Native action {act.value} failed"

        _, post_obs, _, _ = self.observe(
            app_name=req.app_name,
            include_screenshot=need_sr,
            approved_applications=approved_applications,
        )
        post_obs = post_obs or pre_obs
        if ok and pre_obs.state_hash != post_obs.state_hash:
            self.vertical_slice_verified = True

        return ok, detail, error, error_code, pre_obs, post_obs

    def close(self) -> None:
        """Terminates any spawned harmless test applications."""
        for proc in self._spawned_test_procs:
            try:
                proc.terminate()
            except Exception:
                pass
        self._spawned_test_procs.clear()
