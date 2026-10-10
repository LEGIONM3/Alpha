# PROJECT ALPHA — APPLE SILICON MAC AGENT VERIFICATION & TEST REPORT

**Date:** October 10, 2026
**Execution Host:** Windows 11 (`AMD64`), Lenovo Legion (`Python 3.12.10`, `pytest 9.1.1`)
**Reasoning Endpoint:** `http://127.0.0.1:1235/v1` (`qwen3.8-9b-heretic-uncensored` via LM Studio)
**Test Suite File:** [`tests/test_mac_agent_verification.py`](tests/test_mac_agent_verification.py)

---

## 1. Executive Summary

The Verification Campaign (Phase 7) separates platform-independent & live local HTTP/Playwright/Qwen acceptance tests from native physical macOS (`arm64` / `Aqua` / `AXUIElement`) hardware integration tests:

- **Mac Agent Acceptance & Closed-Loop Tests (`TestMacAgentAcceptanceAndClosedLoop`)**: **14 / 14 PASSED**
- **Phase N Closed-Loop Regression Suite (`TestPhaseNClosedLoopExecution`)**: **11 / 11 PASSED**
- **Physical Apple Silicon macOS Native GUI Integration Tests (`TestRealAppleSiliconMacNativeIntegration`)**: **3 / 3 SKIPPED (`NOT RUN` on Windows 11 host)**

**Total Executed:** **25 PASSED, 0 FAILED, 3 NOT RUN (SKIPPED)**.

---

## 2. Exact Test Commands Executed

### 2.1 CLI Platform & Permission Diagnostic Probe
```powershell
python -m alpha.computer_use.mac_agent.cli --check-only
```
**Observed Output (Windows 11 Controller Host, user redacted):**
```json
{
  "system": "Windows",
  "is_macos": false,
  "architecture": "amd64",
  "is_apple_silicon": false,
  "macos_version": "",
  "macos_build": "",
  "macos_release_family": "Non-macOS",
  "is_root_process": false,
  "is_graphical_user_session": true,
  "session_manager_type": "non_darwin_host",
  "logged_in_user": "<redacted-local-user>",
  "playwright_available": true,
  "permissions": {
    "accessibility_granted": false,
    "screen_recording_granted": false,
    "automation_granted": false,
    "missing_permissions": [
      "MACOS_DARWIN_HOST"
    ],
    "remediation_instructions": [
      "Current host is Windows (amd64). Native macOS Accessibility/Quartz actuators require an Apple Silicon macOS host."
    ]
  },
  "ready_for_browser": true,
  "ready_for_native_gui": false
}
```

### 2.2 Full Verification & Regression Test Command
```powershell
python -m pytest tests/test_mac_agent_verification.py tests/test_phase_n_closed_loop.py -v -rs
```

---

## 3. Detailed Acceptance Test Results (`tests/test_mac_agent_verification.py`)

| # | Test Name | Requirement Verified | Status |
|:--|:---|:---|:---:|
| **01** | `test_01_schema_validation_rejects_malformed_requests` | Rejects malformed JSON (`HTTP 400`), extra fields (`HTTP 422`), and coordinate locators missing `coordinate_fallback_reason`. | **PASSED** |
| **02** | `test_02_authentication_rejects_missing_or_invalid_credentials` | Rejects missing or invalid Bearer tokens with `HTTP 401 AUTHENTICATION_FAILED`. | **PASSED** |
| **03** | `test_03_unknown_action_types_and_remote_shell_rejected` | Rejects unknown action types (`ARBITRARY_SHELL_EXEC`) with `HTTP 422` and blocks `execute_terminal_action` with `REMOTE_SHELL_FORBIDDEN`. | **PASSED** |
| **04** | `test_04_agent_reports_missing_permissions_honestly` | Reports `native_gui_supported=False` when macOS Accessibility is missing and fails closed with `MISSING_ACCESSIBILITY_PERMISSION` (`FALSIFIED`). | **PASSED** |
| **05** | `test_05_browser_launch_and_local_page_navigation` | Launches Chromium with isolated profile (`alpha_mac_browser_profile_*`) and navigates to allowed local test page (`VERIFIED`). | **PASSED** |
| **06** | `test_06_real_browser_form_fill_and_submit` | Fills text input by semantic label, selects dropdown option, clicks Submit button by semantic role/name, and captures screenshot (`VERIFIED`). | **PASSED** |
| **07** | `test_07_browser_resulting_state_independently_verified` | Independently inspects post-submission DOM state via `/v1/verify_outcome`, confirming `pre_state_hash != post_state_hash` and `VERIFIED` status. | **PASSED** |
| **08** | `test_08_deliberate_failed_action_and_dry_run_truthful_reporting` | Deliberate missing button click returns `ok=False` and `FALSIFIED`; dry-run mode returns `INCONCLUSIVE` with `state_changed=False`. | **PASSED** |
| **09** | `test_09_cancellation_and_emergency_stop_prevent_further_actions` | `/v1/cancel_task` blocks task actions with `TASK_CANCELLED`; `/v1/emergency_stop` halts all tasks with `EMERGENCY_STOP_ACTIVE`. | **PASSED** |
| **10** | `test_10_timeouts_and_action_budgets_obey_configured_limits` | Enforces `max_actions_per_task=2` (`ACTION_BUDGET_EXHAUSTED` on 3rd action) and `max_retries_per_task=1`. | **PASSED** |
| **11** | `test_11_audit_records_contain_chain_and_redact_secrets` | Verifies `mac_agent_audit.jsonl` contains `pre_observation_id`, `pre_state_hash`, `post_observation_id`, `post_state_hash`, `verification`, and scrubs secrets to `[REDACTED_SECRET]`. | **PASSED** |
| **12** | `test_12_legion_to_mac_private_connection_and_qwen_closed_loop` | Connects `MacComputerUseClient` to `MacAgentHTTPServer` and runs `LayaClosedLoopRuntime` (`modality="MAC_BROWSER"`) with live `QwenStrategicReasoner` (`qwen3.8-9b-heretic-uncensored`), persisting trajectory and `EvidenceGraph` nodes. | **PASSED** |
| **13** | `test_13_mac_rejects_unauthorized_client_ip_and_public_bind` | Refuses `0.0.0.0` and `8.8.8.8` bind addresses (`ValueError`) and rejects unauthorized client IPs with `HTTP 403 UNAUTHORIZED_CLIENT_IP`. | **PASSED** |
| **14** | `test_14_restarting_service_preserves_safe_defaults_and_consequential_gate` | Fresh service restart enforces `deny_by_default=True`, blocks unapproved URLs (`URL_NOT_ALLOWED`), blocks `Terminal` (`APPLICATION_NOT_ALLOWED`), and blocks `"Delete Account Permanently"` without `consequential_confirmed_by_user=True`. | **PASSED** |

---

## 4. Physical Apple Silicon macOS Native Integration Tests (`NOT RUN` on Windows 11)

In strict compliance with Phase 7 rules, the following native macOS tests require physical Apple Silicon macOS hardware with an active `Aqua` desktop session and were **NOT RUN** on the Windows 11 Lenovo Legion:

| # | Test Name | Target Verification on Physical Mac | Status on Windows 11 |
|:--|:---|:---|:---:|
| **N1** | `test_mac_native_01_apple_silicon_arm64_and_aqua_session_detection` | Live Darwin kernel, `arm64` CPU, non-root UID, and `Aqua` session detection. | **NOT RUN (`SKIPPED`)** |
| **N2** | `test_mac_native_02_harmless_test_app_launch_click_and_independent_verification` | Launches `AlphaMacTestApp`, clicks `"Increment Counter"` via `System Events` Accessibility, and verifies `"Status: Mutated | Counter: 1"`. | **NOT RUN (`SKIPPED`)** |
| **N3** | `test_mac_native_03_native_screenshot_capture_with_tcc_permission` | Captures native macOS screen image via `/usr/sbin/screencapture -x` with TCC Screen Recording permission. | **NOT RUN (`SKIPPED`)** |

### Command to Execute Native Tests on the Apple Silicon MacBook Air M2
Once the repository is cloned onto the Apple Silicon MacBook and Accessibility + Screen Recording permissions are granted (see [`MAC_AGENT_SETUP.md`](MAC_AGENT_SETUP.md)):
```bash
pytest tests/test_mac_agent_verification.py -k "TestRealAppleSiliconMacNativeIntegration" -v
```
