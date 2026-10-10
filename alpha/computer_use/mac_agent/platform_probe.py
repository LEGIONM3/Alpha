"""Platform, Architecture, Graphical Session, and TCC Permission Probe for macOS Agent.

Detects at runtime:
- Operating system and kernel (Darwin vs Windows/Linux)
- CPU architecture (Apple Silicon arm64 vs x86_64)
- Exact macOS version and build (via platform.mac_ver() and sw_vers)
- Graphical user session status (Aqua logged-in session vs root daemon / headless SSH)
- macOS TCC Privacy & Security permissions:
  - Accessibility (AXIsProcessTrusted)
  - Screen Recording (CGPreflightScreenCaptureAccess)
  - AppleEvents Automation (System Events probe)

Never assumes macOS version or permissions. Fails clearly and honestly when
required permissions or platform capabilities are absent.
"""

from __future__ import annotations

import ctypes
import logging
import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("alpha.computer_use.mac_agent.platform_probe")


class MacPermissionStatus(BaseModel):
    """Detailed status of macOS TCC permissions required for computer use."""
    accessibility_granted: bool = False
    screen_recording_granted: bool = False
    automation_granted: bool = False
    missing_permissions: List[str] = Field(default_factory=list)
    remediation_instructions: List[str] = Field(default_factory=list)


class MacPlatformReport(BaseModel):
    """Comprehensive runtime platform and session report."""
    system: str
    is_macos: bool
    architecture: str
    is_apple_silicon: bool
    macos_version: str = ""
    macos_build: str = ""
    macos_release_family: str = ""
    is_root_process: bool = False
    is_graphical_user_session: bool = False
    session_manager_type: str = "unknown"
    logged_in_user: str = ""
    playwright_available: bool = False
    permissions: MacPermissionStatus = Field(default_factory=MacPermissionStatus)
    compatibility_notes: List[str] = Field(default_factory=list)
    ready_for_browser: bool = False
    ready_for_native_gui: bool = False


def _detect_macos_release_family(version_str: str) -> str:
    """Maps macOS version string to release family without assuming version."""
    if not version_str:
        return "Non-macOS"
    parts = version_str.split(".")
    try:
        major = int(parts[0])
    except ValueError:
        return f"macOS ({version_str})"

    mapping = {
        11: "macOS 11 Big Sur",
        12: "macOS 12 Monterey",
        13: "macOS 13 Ventura",
        14: "macOS 14 Sonoma",
        15: "macOS 15 Sequoia",
        16: "macOS 16 / 26",
        26: "macOS 26 Tahoe",
    }
    return mapping.get(major, f"macOS {major} ({version_str})")


def _probe_sw_vers() -> Dict[str, str]:
    """Queries /usr/bin/sw_vers on macOS for authoritative product and build versions."""
    result = {"product_version": "", "build_version": ""}
    if sys.platform != "darwin" or not shutil.which("sw_vers"):
        return result
    try:
        ver_proc = subprocess.run(
            ["sw_vers", "-productVersion"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if ver_proc.returncode == 0:
            result["product_version"] = ver_proc.stdout.strip()

        build_proc = subprocess.run(
            ["sw_vers", "-buildVersion"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if build_proc.returncode == 0:
            result["build_version"] = build_proc.stdout.strip()
    except Exception as exc:
        logger.debug(f"sw_vers probe failed: {exc}")
    return result


def _check_is_root() -> bool:
    """Checks if the current process is running as root (UID 0)."""
    if hasattr(os, "geteuid"):
        return os.geteuid() == 0
    return False


def _probe_graphical_session(is_macos: bool) -> Tuple[bool, str]:
    """Checks whether the process runs inside the logged-in user's graphical session.

    On macOS, GUI automation must run inside the user's 'Aqua' session, never a root daemon.
    """
    if not is_macos:
        return True, "non_darwin_host"

    # Check launchctl managername on macOS
    if shutil.which("launchctl"):
        try:
            proc = subprocess.run(
                ["launchctl", "managername"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            if proc.returncode == 0:
                mgr = proc.stdout.strip()
                # "Aqua" indicates the logged-in graphical GUI session on macOS
                is_gui = mgr.lower() == "aqua"
                return is_gui, mgr
        except Exception as exc:
            logger.debug(f"launchctl managername check failed: {exc}")

    # Fallback: check WindowServer / SECURITYSESSIONID environment
    if os.environ.get("SECURITYSESSIONID") or os.environ.get("TERM_PROGRAM"):
        return True, "env_session"

    return False, "background_or_daemon"


def _probe_tcc_accessibility(is_macos: bool) -> bool:
    """Checks macOS TCC Accessibility permission via ApplicationServices.AXIsProcessTrusted()."""
    if not is_macos:
        return False

    try:
        app_services = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        trusted = bool(app_services.AXIsProcessTrusted())
        return trusted
    except Exception as exc:
        logger.debug(f"AXIsProcessTrusted ctypes check failed: {exc}")
        return False


def _probe_tcc_screen_recording(is_macos: bool) -> bool:
    """Checks macOS TCC Screen Recording permission via CGPreflightScreenCaptureAccess()."""
    if not is_macos:
        return False

    try:
        core_graphics = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        if hasattr(core_graphics, "CGPreflightScreenCaptureAccess"):
            core_graphics.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
            return bool(core_graphics.CGPreflightScreenCaptureAccess())
    except Exception as exc:
        logger.debug(f"CGPreflightScreenCaptureAccess check failed: {exc}")
    return False


def _probe_tcc_automation(is_macos: bool) -> bool:
    """Checks whether AppleEvents automation to System Events is permitted."""
    if not is_macos or not shutil.which("osascript"):
        return False

    try:
        proc = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to return UI elements enabled'],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        return proc.returncode == 0 and "true" in proc.stdout.strip().lower()
    except Exception:
        return False


def _check_playwright_installed() -> bool:
    """Verifies whether Playwright is importable in the active Python environment."""
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


class MacPlatformProbe:
    """Runtime environment, architecture, and permission verifier for the macOS agent."""

    def __init__(self, override_report: Optional[MacPlatformReport] = None):
        self._override_report = override_report

    def inspect_platform(self) -> MacPlatformReport:
        """Executes live inspection of OS, CPU architecture, user session, and TCC permissions."""
        if self._override_report is not None:
            return self._override_report

        sys_name = platform.system()
        is_macos = (sys.platform == "darwin") or (sys_name.lower() == "darwin")
        arch = platform.machine().lower()
        is_apple_silicon = is_macos and (arch in ("arm64", "aarch64"))

        mac_ver_tuple = platform.mac_ver()
        macos_ver = mac_ver_tuple[0] if mac_ver_tuple and mac_ver_tuple[0] else ""
        sw_info = _probe_sw_vers()
        if sw_info["product_version"]:
            macos_ver = sw_info["product_version"]
        macos_build = sw_info["build_version"]
        release_family = _detect_macos_release_family(macos_ver)

        is_root = _check_is_root()
        is_gui, session_mgr = _probe_graphical_session(is_macos)
        pw_avail = _check_playwright_installed()

        user_name = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

        # Probe TCC permissions
        ax_ok = _probe_tcc_accessibility(is_macos)
        sr_ok = _probe_tcc_screen_recording(is_macos)
        auto_ok = _probe_tcc_automation(is_macos)

        missing: List[str] = []
        remediation: List[str] = []

        if is_macos:
            if is_root:
                missing.append("NON_ROOT_USER_SESSION")
                remediation.append(
                    "Do not run the Mac agent as root (sudo/LaunchDaemon). Run as the logged-in desktop user (LaunchAgent / Aqua session)."
                )
            if not is_gui:
                missing.append("AQUA_GRAPHICAL_SESSION")
                remediation.append(
                    f"Process is in '{session_mgr}' session instead of 'Aqua'. Start the agent from a logged-in desktop session or LaunchAgent."
                )
            if not ax_ok:
                missing.append("ACCESSIBILITY")
                remediation.append(
                    "Grant Accessibility permission in System Settings -> Privacy & Security -> Accessibility for the terminal / Python executable."
                )
            if not sr_ok:
                missing.append("SCREEN_RECORDING")
                remediation.append(
                    "Grant Screen Recording permission in System Settings -> Privacy & Security -> Screen & System Audio Recording for screenshot capture."
                )
            if not auto_ok:
                missing.append("AUTOMATION_SYSTEM_EVENTS")
                remediation.append(
                    "Grant Automation permission (System Events) in System Settings -> Privacy & Security -> Automation."
                )
        else:
            missing.append("MACOS_DARWIN_HOST")
            remediation.append(
                f"Current host is {sys_name} ({arch}). Native macOS Accessibility/Quartz actuators require an Apple Silicon macOS host."
            )

        notes: List[str] = []
        if is_macos:
            if not is_apple_silicon:
                notes.append(f"Running on macOS with '{arch}' architecture (Intel/Rosetta) rather than native arm64.")
            if macos_ver:
                major_int = int(macos_ver.split(".")[0]) if macos_ver.split(".")[0].isdigit() else 0
                if major_int < 13:
                    notes.append(
                        f"Detected {release_family}. System Settings paths and ScreenCaptureKit APIs differ on macOS < 13."
                    )
                elif major_int >= 15:
                    notes.append(
                        f"Detected {release_family}. Periodic Screen Recording re-authorization prompts may be enforced by macOS TCC."
                    )
        else:
            notes.append(
                f"Running in cross-platform mode on {sys_name} ({arch}). Playwright browser execution is active; native macOS GUI actuation is disabled."
            )

        perm_status = MacPermissionStatus(
            accessibility_granted=ax_ok,
            screen_recording_granted=sr_ok,
            automation_granted=auto_ok,
            missing_permissions=missing,
            remediation_instructions=remediation,
        )

        ready_browser = pw_avail and (not is_root)
        ready_native = is_macos and (not is_root) and is_gui and ax_ok

        return MacPlatformReport(
            system=sys_name,
            is_macos=is_macos,
            architecture=arch,
            is_apple_silicon=is_apple_silicon,
            macos_version=macos_ver,
            macos_build=macos_build,
            macos_release_family=release_family,
            is_root_process=is_root,
            is_graphical_user_session=is_gui,
            session_manager_type=session_mgr,
            logged_in_user=user_name,
            playwright_available=pw_avail,
            permissions=perm_status,
            compatibility_notes=notes,
            ready_for_browser=ready_browser,
            ready_for_native_gui=ready_native,
        )
