"""Playwright-Controlled Chromium Browser Executor for the Mac Agent (Phase 2).

Features:
- Dedicated single-thread Playwright worker dispatcher (safe across multi-threaded HTTP requests).
- Isolated browser profile by default (never copies personal browser profiles, cookies, or credentials).
- Visible window by default on macOS Aqua sessions; configurable headless mode for automated tests.
- Semantic-first element resolution (role, label, text, placeholder, test_id, element_id, css) with
  logged fallback reasons if coordinates are ever used.
- Structured DOM / accessibility observation with SHA-256 state fingerprinting and untrusted content wrapping.
"""

from __future__ import annotations

import base64
from concurrent.futures import Future
import hashlib
import json
import logging
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

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
    SemanticLocator,
)

logger = logging.getLogger("alpha.computer_use.mac_agent.browser_executor")


_DOM_INVENTORY_JS = """
() => {
    const interactiveSelector = 'a, button, input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="menuitem"], [role="tab"], h1, h2, h3, p, span, label';
    const nodes = Array.from(document.querySelectorAll(interactiveSelector));
    const items = [];
    let idx = 0;
    for (const el of nodes) {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        const visible = rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
        if (!visible) continue;

        let alphaId = el.getAttribute('data-alpha-mac-id');
        if (!alphaId) {
            alphaId = el.id ? el.id : ('mac_el_' + idx);
            el.setAttribute('data-alpha-mac-id', alphaId);
        }
        idx += 1;

        const tag = el.tagName.toLowerCase();
        const role = el.getAttribute('role') || (
            tag === 'button' ? 'button' :
            tag === 'a' ? 'link' :
            tag === 'input' ? (el.type || 'textbox') :
            tag === 'select' ? 'combobox' :
            tag === 'textarea' ? 'textbox' :
            (tag === 'h1' || tag === 'h2' || tag === 'h3') ? 'heading' :
            tag
        );

        let labelText = '';
        if (el.id) {
            const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
            if (lbl) labelText = (lbl.innerText || lbl.textContent || '').trim();
        }
        if (!labelText && el.closest('label')) {
            labelText = (el.closest('label').innerText || '').trim();
        }

        const ariaLabel = el.getAttribute('aria-label') || '';
        const placeholder = el.getAttribute('placeholder') || '';
        const innerTxt = (el.innerText || el.textContent || '').trim().slice(0, 120);
        const name = (ariaLabel || labelText || innerTxt || placeholder || el.name || el.id || '').trim().slice(0, 120);
        const val = (el.value !== undefined && el.value !== null) ? String(el.value).slice(0, 120) : '';

        items.push({
            element_id: alphaId,
            role: role,
            name: name,
            label: labelText || ariaLabel || placeholder,
            value: val,
            tag: tag,
            visible: true,
            enabled: !el.disabled,
            bbox: [Math.round(rect.x), Math.round(rect.y), Math.round(rect.width), Math.round(rect.height)]
        });
        if (items.length >= 60) break;
    }
    const bodyText = (document.body ? (document.body.innerText || document.body.textContent || '') : '').trim().slice(0, 2000);
    return {
        elements: items,
        body_text: bodyText
    };
}
"""


class MacBrowserExecutor:
    """Thread-safe Playwright Chromium executor with isolated browser profile."""

    def __init__(
        self,
        headless: Optional[bool] = None,
        isolated_profile_dir: Optional[Path] = None,
        cdp_endpoint: Optional[str] = None,
        default_timeout_ms: int = 10000,
    ):
        # On macOS graphical sessions, default to visible browser (headless=False) unless specified
        if headless is None:
            self.headless = (sys.platform != "darwin")
        else:
            self.headless = bool(headless)

        self.isolated_profile_dir = isolated_profile_dir or Path(
            tempfile.mkdtemp(prefix="alpha_mac_browser_profile_")
        )
        self.cdp_endpoint = cdp_endpoint
        self.default_timeout_ms = default_timeout_ms

        self._cmd_queue: "queue.Queue[Optional[Tuple[Callable[[], Any], Future[Any]]]]" = queue.Queue()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="AlphaMacBrowserWorker",
            daemon=True,
        )
        self._closed = False
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Single-thread event loop owning the Playwright instance and browser context."""
        pw = None
        browser = None
        context = None
        page = None

        def ensure_page():
            nonlocal pw, browser, context, page
            if page is not None and not page.is_closed():
                return page
            from playwright.sync_api import sync_playwright
            if pw is None:
                pw = sync_playwright().start()
            if self.cdp_endpoint:
                browser = pw.chromium.connect_over_cdp(self.cdp_endpoint)
                context = browser.contexts[0] if browser.contexts else browser.new_context()
            else:
                self.isolated_profile_dir.mkdir(parents=True, exist_ok=True)
                browser = pw.chromium.launch(headless=self.headless)
                context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(self.default_timeout_ms)
            return page

        def close_all():
            nonlocal pw, browser, context, page
            for obj, method in ((page, "close"), (context, "close"), (browser, "close"), (pw, "stop")):
                if obj is not None:
                    try:
                        getattr(obj, method)()
                    except Exception:
                        pass
            page = None
            context = None
            browser = None
            pw = None

        while True:
            item = self._cmd_queue.get()
            if item is None:
                close_all()
                break
            fn, fut = item
            try:
                res = fn(ensure_page, close_all)
                fut.set_result(res)
            except Exception as exc:
                fut.set_exception(exc)

    def _dispatch(self, fn: Callable[[Any, Any], Any], timeout: float = 30.0) -> Any:
        if self._closed:
            raise RuntimeError("MacBrowserExecutor has been shut down.")
        fut: Future[Any] = Future()
        self._cmd_queue.put((fn, fut))
        return fut.result(timeout=timeout)

    def observe(self, include_screenshot: bool = False) -> MacObservationPayload:
        """Captures current URL, title, interactive semantic elements, visible text, and SHA-256 state hash."""
        def _do_observe(ensure_page: Any, _close_all: Any) -> MacObservationPayload:
            page = ensure_page()
            return self._observe_page_sync(page, include_screenshot=include_screenshot)

        return self._dispatch(_do_observe, timeout=20.0)

    def _observe_page_sync(self, page: Any, include_screenshot: bool = False) -> MacObservationPayload:
        url = page.url or "about:blank"
        try:
            title = page.title() or ""
        except Exception:
            title = ""

        try:
            inv = page.evaluate(_DOM_INVENTORY_JS)
        except Exception as exc:
            logger.debug(f"DOM inventory evaluation fallback: {exc}")
            inv = {"elements": [], "body_text": ""}

        raw_elements = inv.get("elements", [])
        body_text = redact_sensitive_text(inv.get("body_text", ""))
        envelope, injection_alerts = wrap_untrusted_environment_content(body_text)

        ui_elements: List[ObservedUIElement] = []
        for el in raw_elements:
            ui_elements.append(
                ObservedUIElement(
                    element_id=str(el.get("element_id", "")),
                    role=str(el.get("role", "generic")),
                    name=redact_sensitive_text(str(el.get("name", ""))),
                    label=redact_sensitive_text(str(el.get("label", ""))),
                    value=redact_sensitive_text(str(el.get("value", ""))),
                    tag=str(el.get("tag", "")),
                    visible=bool(el.get("visible", True)),
                    enabled=bool(el.get("enabled", True)),
                    bbox=el.get("bbox"),
                )
            )

        fingerprint_payload = {
            "url": url,
            "title": title,
            "body_text": body_text,
            "elements": [
                {"id": e.element_id, "role": e.role, "name": e.name, "value": e.value}
                for e in ui_elements
            ],
        }
        state_hash = hashlib.sha256(
            json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        screenshot_b64: Optional[str] = None
        if include_screenshot:
            try:
                png_bytes = page.screenshot(type="png", full_page=False)
                screenshot_b64 = base64.b64encode(png_bytes).decode("ascii")
            except Exception as exc:
                logger.warning(f"Browser screenshot capture failed: {exc}")

        return MacObservationPayload(
            modality=MacModality.BROWSER,
            url=url,
            page_title=title,
            active_application="Chromium",
            window_title=title or url,
            elements=ui_elements,
            visible_text_summary=body_text[:1000],
            untrusted_content_envelope=envelope,
            state_hash=state_hash,
            screenshot_base64=screenshot_b64,
            metadata={
                "isolated_profile_dir": str(self.isolated_profile_dir),
                "headless": self.headless,
                "prompt_injection_alerts": injection_alerts,
            },
        )

    def _resolve_playwright_locator(self, page: Any, loc: SemanticLocator) -> Any:
        """Resolves a SemanticLocator to a Playwright Locator object."""
        by = loc.by
        if by == LocatorStrategy.ROLE:
            role_name = loc.role or loc.value
            if loc.name:
                return page.get_by_role(role_name, name=loc.name, exact=loc.exact).first
            return page.get_by_role(role_name).first
        elif by == LocatorStrategy.LABEL:
            return page.get_by_label(loc.value or loc.name or "", exact=loc.exact).first
        elif by == LocatorStrategy.TEXT:
            return page.get_by_text(loc.value or loc.name or "", exact=loc.exact).first
        elif by == LocatorStrategy.PLACEHOLDER:
            return page.get_by_placeholder(loc.value or loc.name or "", exact=loc.exact).first
        elif by == LocatorStrategy.TEST_ID:
            return page.get_by_test_id(loc.value or loc.name or "").first
        elif by == LocatorStrategy.ELEMENT_ID:
            target_id = loc.value or loc.name or ""
            return page.locator(f'[data-alpha-mac-id="{target_id}"], #{target_id}').first
        elif by == LocatorStrategy.CSS:
            return page.locator(loc.value).first
        else:
            raise ValueError(f"Unsupported semantic locator strategy: {by}")

    def execute_action(
        self, req: ExecuteActionRequest
    ) -> Tuple[bool, str, Optional[str], MacObservationPayload, MacObservationPayload]:
        """Executes a browser action and returns (ok, detail, error, pre_obs, post_obs)."""
        timeout_ms = max(500, int(req.timeout_seconds * 1000))

        def _do_action(
            ensure_page: Any, close_all: Any
        ) -> Tuple[bool, str, Optional[str], MacObservationPayload, MacObservationPayload]:
            page = ensure_page()
            page.set_default_timeout(timeout_ms)
            pre_obs = self._observe_page_sync(page, include_screenshot=False)

            if req.dry_run:
                return (
                    True,
                    f"DRY_RUN: Validated {req.action_type.value} without mutating browser state.",
                    None,
                    pre_obs,
                    pre_obs,
                )

            act = req.action_type
            detail = ""
            error: Optional[str] = None
            ok = True

            try:
                if act == MacActionType.BROWSER_LAUNCH:
                    detail = f"Browser session active (isolated profile: {self.isolated_profile_dir.name})"

                elif act == MacActionType.BROWSER_NAVIGATE:
                    if not req.url:
                        raise ValueError("BROWSER_NAVIGATE requires 'url'.")
                    page.goto(req.url, timeout=timeout_ms, wait_until="domcontentloaded")
                    detail = f"Navigated to {req.url}"

                elif act == MacActionType.BROWSER_OBSERVE:
                    detail = "Observed active browser state"

                elif act == MacActionType.BROWSER_CLICK:
                    if not req.locator:
                        raise ValueError("BROWSER_CLICK requires 'locator'.")
                    if req.locator.by == LocatorStrategy.COORDINATES:
                        logger.warning(
                            f"Coordinate click fallback used at ({req.locator.x}, {req.locator.y}): "
                            f"{req.locator.coordinate_fallback_reason}"
                        )
                        page.mouse.click(float(req.locator.x or 0), float(req.locator.y or 0))
                        detail = (
                            f"Clicked coordinates ({req.locator.x}, {req.locator.y}) "
                            f"[Fallback reason: {req.locator.coordinate_fallback_reason}]"
                        )
                    else:
                        pw_loc = self._resolve_playwright_locator(page, req.locator)
                        pw_loc.click(timeout=timeout_ms)
                        detail = f"Clicked element via {req.locator.by.value}='{req.locator.value or req.locator.name or req.locator.role}'"

                elif act == MacActionType.BROWSER_TYPE:
                    if not req.locator:
                        raise ValueError("BROWSER_TYPE requires 'locator'.")
                    text_to_type = req.text or ""
                    if req.locator.by == LocatorStrategy.COORDINATES:
                        page.mouse.click(float(req.locator.x or 0), float(req.locator.y or 0))
                        page.keyboard.type(text_to_type)
                        detail = f"Typed text at coordinates ({req.locator.x}, {req.locator.y})"
                    else:
                        pw_loc = self._resolve_playwright_locator(page, req.locator)
                        pw_loc.fill(text_to_type, timeout=timeout_ms)
                        detail = f"Filled element via {req.locator.by.value}='{req.locator.value or req.locator.name}'"

                elif act == MacActionType.BROWSER_SELECT:
                    if not req.locator:
                        raise ValueError("BROWSER_SELECT requires 'locator'.")
                    pw_loc = self._resolve_playwright_locator(page, req.locator)
                    pw_loc.select_option(req.text or "", timeout=timeout_ms)
                    detail = f"Selected option '{req.text}' on {req.locator.by.value}"

                elif act == MacActionType.BROWSER_SCROLL:
                    direction = req.scroll_direction or "down"
                    amt = abs(int(req.scroll_amount or 300))
                    dx, dy = 0, amt
                    if direction == "up":
                        dy = -amt
                    elif direction == "left":
                        dx, dy = -amt, 0
                    elif direction == "right":
                        dx, dy = amt, 0
                    page.mouse.wheel(dx, dy)
                    time.sleep(0.1)
                    detail = f"Scrolled {direction} by {amt}px"

                elif act == MacActionType.BROWSER_SCREENSHOT:
                    detail = "Captured browser screenshot"

                elif act == MacActionType.BROWSER_CLOSE:
                    close_all()
                    return (
                        True,
                        "Closed managed browser session",
                        None,
                        pre_obs,
                        pre_obs,
                    )

                elif act == MacActionType.WAIT:
                    time.sleep(max(0.05, min(req.wait_ms / 1000.0, req.timeout_seconds)))
                    detail = f"Waited {req.wait_ms}ms"

                else:
                    raise ValueError(f"Unsupported browser action: {act.value}")

            except Exception as exc:
                ok = False
                error = str(exc)
                detail = f"Browser action {act.value} failed"

            post_obs = self._observe_page_sync(
                page,
                include_screenshot=req.capture_screenshot or (act == MacActionType.BROWSER_SCREENSHOT),
            )
            return ok, detail, error, pre_obs, post_obs

        return self._dispatch(_do_action, timeout=req.timeout_seconds + 5.0)

    def close(self) -> None:
        """Gracefully closes the browser session and stops the worker thread."""
        if not self._closed:
            self._closed = True
            self._cmd_queue.put(None)
            self._worker_thread.join(timeout=5.0)
