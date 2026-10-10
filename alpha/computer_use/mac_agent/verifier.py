"""Independent Outcome Verifier for the Mac Agent.

Enforces Alpha's strict epistemic invariant:
- Never mark an action VERIFIED merely because an API returned HTTP 200 or did not raise an exception.
- Requires independent post-action observation evidence (state hash comparison and explicit postconditions).
- Classifies outcomes honestly as VERIFIED, FALSIFIED, INCONCLUSIVE, or UNRESOLVED.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from alpha.computer_use.mac_agent.schemas import (
    MacActionType,
    MacObservationPayload,
    OutcomeVerificationDetail,
    VerificationStatus,
)


PASSIVE_OR_OBSERVATIONAL_ACTIONS = {
    MacActionType.BROWSER_LAUNCH,
    MacActionType.BROWSER_OBSERVE,
    MacActionType.BROWSER_SCREENSHOT,
    MacActionType.BROWSER_CLOSE,
    MacActionType.NATIVE_LIST_APPS,
    MacActionType.NATIVE_INSPECT_WINDOW,
    MacActionType.NATIVE_SCREENSHOT,
    MacActionType.WAIT,
    MacActionType.COMPLETE,
}


class MacOutcomeVerifier:
    """Independently verifies whether an action mutated the environment and met postconditions."""

    def verify_action_outcome(
        self,
        action_type: MacActionType,
        action_ok: bool,
        pre_obs: Optional[MacObservationPayload],
        post_obs: Optional[MacObservationPayload],
        expected_postcondition: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        error_msg: Optional[str] = None,
    ) -> OutcomeVerificationDetail:
        pre_hash = pre_obs.state_hash if pre_obs else ""
        post_hash = post_obs.state_hash if post_obs else ""
        state_changed = bool(pre_hash and post_hash and (pre_hash != post_hash))

        checks: Dict[str, bool] = {
            "action_ok": action_ok,
            "state_changed": state_changed,
        }

        if dry_run:
            return OutcomeVerificationDetail(
                verification_status=VerificationStatus.INCONCLUSIVE,
                state_changed=False,
                postcondition_satisfied=False,
                pre_state_hash=pre_hash,
                post_state_hash=post_hash,
                checks=checks,
                note="Dry-run mode: action was validated against policy but not executed.",
            )

        if not action_ok or post_obs is None:
            return OutcomeVerificationDetail(
                verification_status=VerificationStatus.FALSIFIED,
                state_changed=state_changed,
                postcondition_satisfied=False,
                pre_state_hash=pre_hash,
                post_state_hash=post_hash,
                checks=checks,
                note=f"Action execution failed: {error_msg or 'unknown error'}",
            )

        expected = expected_postcondition or {}
        all_expected_met = True

        if expected:
            if "url_contains" in expected:
                m = str(expected["url_contains"]) in (post_obs.url or "")
                checks["url_contains"] = m
                if not m:
                    all_expected_met = False

            if "title_contains" in expected:
                m = str(expected["title_contains"]) in (post_obs.page_title or post_obs.window_title or "")
                checks["title_contains"] = m
                if not m:
                    all_expected_met = False

            if "dom_contains" in expected:
                target_str = str(expected["dom_contains"])
                m = (target_str in (post_obs.visible_text_summary or "")) or any(
                    target_str in (el.name or "") or target_str in (el.value or "")
                    for el in post_obs.elements
                )
                checks["dom_contains"] = m
                if not m:
                    all_expected_met = False

            if "text_contains" in expected:
                target_str = str(expected["text_contains"])
                m = target_str in (post_obs.visible_text_summary or "")
                checks["text_contains"] = m
                if not m:
                    all_expected_met = False

            if "element_text" in expected:
                target_str = str(expected["element_text"])
                m = any(target_str in (el.name or "") for el in post_obs.elements)
                checks["element_text"] = m
                if not m:
                    all_expected_met = False

            if "element_value" in expected:
                target_val = str(expected["element_value"])
                m = any(target_val == (el.value or "") for el in post_obs.elements)
                checks["element_value"] = m
                if not m:
                    all_expected_met = False

            if "window_title_contains" in expected:
                m = str(expected["window_title_contains"]) in (post_obs.window_title or "")
                checks["window_title_contains"] = m
                if not m:
                    all_expected_met = False

            if "active_application" in expected:
                m = str(expected["active_application"]).lower() == (post_obs.active_application or "").lower()
                checks["active_application"] = m
                if not m:
                    all_expected_met = False

        is_passive = action_type in PASSIVE_OR_OBSERVATIONAL_ACTIONS

        if not is_passive and not state_changed:
            return OutcomeVerificationDetail(
                verification_status=VerificationStatus.FALSIFIED,
                state_changed=False,
                postcondition_satisfied=False,
                pre_state_hash=pre_hash,
                post_state_hash=post_hash,
                checks=checks,
                note=f"Motor action {action_type.value} reported ok, but produced zero observable UI/DOM state change.",
            )

        if expected:
            if all_expected_met and (state_changed or is_passive):
                return OutcomeVerificationDetail(
                    verification_status=VerificationStatus.VERIFIED,
                    state_changed=state_changed,
                    postcondition_satisfied=True,
                    pre_state_hash=pre_hash,
                    post_state_hash=post_hash,
                    checks=checks,
                    note="All expected postconditions independently verified in post-action observation.",
                )
            elif state_changed and not all_expected_met:
                return OutcomeVerificationDetail(
                    verification_status=VerificationStatus.INCONCLUSIVE,
                    state_changed=True,
                    postcondition_satisfied=False,
                    pre_state_hash=pre_hash,
                    post_state_hash=post_hash,
                    checks=checks,
                    note="Environment mutated after action, but target postcondition checks are not yet satisfied.",
                )
            else:
                return OutcomeVerificationDetail(
                    verification_status=VerificationStatus.FALSIFIED,
                    state_changed=state_changed,
                    postcondition_satisfied=False,
                    pre_state_hash=pre_hash,
                    post_state_hash=post_hash,
                    checks=checks,
                    note="Expected postconditions were not satisfied in post-action observation.",
                )

        # No explicit postcondition dict provided: verify based on observable state change (or passive observation)
        if state_changed or is_passive:
            return OutcomeVerificationDetail(
                verification_status=VerificationStatus.VERIFIED,
                state_changed=state_changed,
                postcondition_satisfied=True,
                pre_state_hash=pre_hash,
                post_state_hash=post_hash,
                checks=checks,
                note="Independently verified via post-action observation.",
            )

        return OutcomeVerificationDetail(
            verification_status=VerificationStatus.UNRESOLVED,
            state_changed=False,
            postcondition_satisfied=False,
            pre_state_hash=pre_hash,
            post_state_hash=post_hash,
            checks=checks,
            note="Action outcome unresolved.",
        )
