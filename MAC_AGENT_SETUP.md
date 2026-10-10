# PROJECT ALPHA — APPLE SILICON MAC AGENT INSTALLATION & SETUP GUIDE

This guide documents the step-by-step installation, macOS TCC permission setup, private network configuration, startup, shutdown, and troubleshooting procedures for running the Alpha Mac Computer-Use Agent on your Apple Silicon MacBook Air M2 and connecting it to Project Alpha on your Windows 11 Lenovo Legion.

---

## 1. Prerequisites & Tested Environment

### 1.1 Apple Silicon MacBook (Actuator Host)
- **Hardware:** Apple Silicon Mac (`M1` / `M2` / `M3` / `M4`, `arm64` architecture).
- **OS:** macOS 13 Ventura, macOS 14 Sonoma, macOS 15 Sequoia, or newer (detected dynamically at runtime via `sw_vers` and `platform.mac_ver()`).
- **Session:** Must be logged into a standard macOS desktop (`Aqua`) session. **Never** run the agent as `root` or as a system-wide `/Library/LaunchDaemons` service.
- **Python Compatibility:**
  - **Supported:** Python 3.11+ (`arm64` native build required on Apple Silicon).
  - **Verified Controller / Protocol / Playwright Version:** Tested on **Python 3.12.10** (`pytest 9.1.1`, `pydantic 2.13.5`, `playwright 1.63.0`) on the Windows 11 Lenovo Legion.
  - **Unverified on Windows Host:** Physical macOS Darwin/Aqua/AXUIElement native GUI integration tests (`TestRealAppleSiliconMacNativeIntegration`) require physical Apple Silicon hardware and must be executed directly on the MacBook after installation.
- **Network:** Connected to the same private encrypted overlay (e.g., **Tailscale** `100.x.y.z`) or isolated private LAN (`192.168.x.y`) as the Windows 11 Lenovo Legion.

### 1.2 Windows 11 Lenovo Legion (Alpha Controller Host)
- **Role:** Runs Project Alpha orchestration and `QwenStrategicReasoner` (`qwen3.8-9b-heretic-uncensored`).
- **LM Studio:** Active on `http://127.0.0.1:1234/v1` or `http://127.0.0.1:1235/v1`.

---

## 2. Installation on the Apple Silicon MacBook Air M2

1. **Clone (or fetch) the `feature/mac-agent-m2-setup` branch onto the MacBook:**
   - **Fresh clone:**
     ```bash
     mkdir -p ~/Projects
     git clone --branch feature/mac-agent-m2-setup <PRIVATE_REPOSITORY_URL> ~/Projects/Alpha
     cd ~/Projects/Alpha
     ```
   - **If `~/Projects/Alpha` already exists (safe fetch without overwriting local work):**
     ```bash
     cd ~/Projects/Alpha
     git status --short
     git fetch origin feature/mac-agent-m2-setup
     git switch feature/mac-agent-m2-setup
     git pull --ff-only origin feature/mac-agent-m2-setup
     ```

2. **Verify native `arm64` Python 3.11+ and create a fresh virtual environment:**
   ```bash
   uname -m
   # Expected output: arm64

   python3 --version
   # Expected output: Python 3.11.x or Python 3.12.x (tested with 3.12.10)

   python3 -c "import platform; assert platform.machine() == 'arm64', f'Expected arm64 Python, got {platform.machine()}'"

   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements-mac-agent.txt
   ```

3. **Install Playwright Chromium browser binaries:**
   ```bash
   python -m playwright install chromium
   ```

---

## 3. Granting Required macOS TCC Permissions

macOS enforces strict Transparency, Consent, and Control (TCC) privacy boundaries. Do not attempt to bypass TCC. Grant permissions explicitly in **System Settings**:

1. **Accessibility Permission (Required for Native UI Inspection & Clicking):**
   - Open **System Settings → Privacy & Security → Accessibility**.
   - Enable the toggle for your terminal application (**Terminal.app** / **iTerm.app**) or the Python binary running the agent.

2. **Screen & System Audio Recording Permission (Required for Native Screenshots):**
   - Open **System Settings → Privacy & Security → Screen & System Audio Recording**.
   - Enable the toggle for your terminal application.
   - *Note (macOS 15 Sequoia+):* macOS may periodically prompt to re-confirm screen recording access.

3. **Automation Permission (Required for `System Events` Window Inspection):**
   - Open **System Settings → Privacy & Security → Automation**.
   - Under your terminal app, ensure **System Events** is enabled.

4. **Verify Permissions with the Diagnostic Probe:**
   ```bash
   python -m alpha.computer_use.mac_agent.cli --check-only
   ```
   Verify that the JSON output shows:
   - `"is_macos": true`
   - `"is_apple_silicon": true`
   - `"is_root_process": false`
   - `"is_graphical_user_session": true`
   - `"ready_for_browser": true`
   - `"ready_for_native_gui": true`

5. **Run the Verification Suite on the MacBook (including Native Apple Silicon Tests):**
   ```bash
   pytest tests/test_mac_agent_verification.py -v -rs
   ```

---

## 4. Private Network & Credential Configuration

### 4.1 Generate a Strong Shared Secret (Outside Source Control)
On the MacBook (or Legion), generate a random 32-byte hex token:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Store this token in an environment variable (`ALPHA_MAC_AGENT_TOKEN`) on both machines. **Never commit this token to Git.**

### 4.2 Identify Private Interface Addresses (Configuration Examples)
- **Recommended (Tailscale VPN Overlay — Example IPs):**
  - MacBook Tailscale IP (example): `100.64.0.100`
  - Lenovo Legion Tailscale IP (example): `100.64.0.50`
- **Alternative (Private Local LAN — Example IPs):**
  - MacBook LAN IP (example): `192.168.1.100`
  - Lenovo Legion LAN IP (example): `192.168.1.50`

---

## 5. Starting and Stopping the Mac Agent

### 5.1 Manual Interactive Startup (Inside Logged-in macOS Terminal)
Replace the example IPs and token placeholder below with your actual private network values:
```bash
cd ~/Projects/Alpha
source .venv/bin/activate

export ALPHA_MAC_AGENT_TOKEN="<EXAMPLE_64_CHAR_SHARED_SECRET_DO_NOT_COMMIT>"
export ALPHA_AUTHORIZED_CLIENT_IPS="127.0.0.1,192.168.1.50"
export ALPHA_MAC_BIND_HOST="192.168.1.100"
export ALPHA_MAC_BIND_PORT="8765"

python -m alpha.computer_use.mac_agent.cli --bind-host "$ALPHA_MAC_BIND_HOST" --port "$ALPHA_MAC_BIND_PORT"
```
- By default on macOS, Playwright Chromium launches as a **visible window** (`headless=False`) in an isolated browser profile (`alpha_mac_browser_profile_*`) so you can watch every action live on the MacBook screen while your Lenovo Legion's physical mouse and keyboard remain completely untouched.

### 5.2 Optional User LaunchAgent (Auto-Start on Desktop Login)
If you want the agent to start automatically when you log into your MacBook desktop, place a plist in `~/Library/LaunchAgents/com.alpha.mac_agent.plist` (**never** in `/Library/LaunchDaemons`) and replace `<YOUR_MACOS_USERNAME>` with your macOS username:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.alpha.mac_agent</string>
    <key>LimitLoadToSessionType</key>
    <string>Aqua</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/&lt;YOUR_MACOS_USERNAME&gt;/Projects/Alpha/.venv/bin/python</string>
        <string>-m</string>
        <string>alpha.computer_use.mac_agent.cli</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/&lt;YOUR_MACOS_USERNAME&gt;/Projects/Alpha</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

### 5.3 Graceful Shutdown & Emergency Stop
- **Graceful Shutdown:** Press `Ctrl+C` (`SIGINT`) or send `SIGTERM` to the agent process. It cleanly closes the managed Chromium instance and any spawned test apps.
- **Emergency Stop from the Lenovo Legion (Example IP):**
  ```python
  import os
  from alpha.computer_use.mac_agent import MacComputerUseClient

  client = MacComputerUseClient(
      base_url=os.environ["ALPHA_MAC_AGENT_URL"],  # e.g. "http://192.168.1.100:8765"
      auth_token=os.environ["ALPHA_MAC_AGENT_TOKEN"],
  )
  client.emergency_stop(reason="Operator halt")
  ```

---

## 6. Connecting from the Windows 11 Lenovo Legion

On the Windows 11 Lenovo Legion, set the environment variables in PowerShell (using your MacBook's private IP and shared secret):
```powershell
$env:ALPHA_MAC_AGENT_URL="http://192.168.1.100:8765"  # Example MacBook private IP
$env:ALPHA_MAC_AGENT_TOKEN="<EXAMPLE_64_CHAR_SHARED_SECRET_DO_NOT_COMMIT>"
```

Execute a closed-loop Mac browser task from Alpha on the Legion:
```python
from alpha.computer_use.closed_loop import ComputerUseTask, LayaClosedLoopRuntime
from alpha.computer_use.mac_agent import MacComputerUseClient

mac_client = MacComputerUseClient()
runtime = LayaClosedLoopRuntime(mac_client=mac_client)

task = ComputerUseTask(
    goal="Navigate to local documentation and verify heading",
    modality="MAC_BROWSER",
    target_url="http://localhost:8000/index.html",
    expected_postcondition={"dom_contains": "Documentation Ready"},
    max_steps=4,
)
trajectory = runtime.execute_task(task)
print(trajectory.status, trajectory.final_verification)
```

---

## 7. Troubleshooting

| Symptom / Error Code | Cause | Resolution |
|:---|:---|:---|
| `ValueError: Refusing to bind Mac Agent server to non-private interface '0.0.0.0'` | Attempted to bind to wildcard or public interface. | Specify the MacBook's specific private LAN (`192.168.x.x`), Tailscale (`100.x.x.x`), or loopback (`127.0.0.1`) IP. |
| `HTTP 403 UNAUTHORIZED_CLIENT_IP` | The Legion's IP is not in `ALPHA_AUTHORIZED_CLIENT_IPS`. | Add the Legion's private IP to `ALPHA_AUTHORIZED_CLIENT_IPS` on the MacBook and restart the agent. |
| `HTTP 401 AUTHENTICATION_FAILED` | Missing or mismatched `ALPHA_MAC_AGENT_TOKEN`. | Ensure identical Bearer tokens are configured via environment variables on both the Legion and the MacBook. |
| `MISSING_ACCESSIBILITY_PERMISSION` | Terminal / Python lacks macOS Accessibility access. | Enable in **System Settings → Privacy & Security → Accessibility** and restart the terminal. |
| `AQUA_SESSION_REQUIRED` | Started over a headless SSH session without an active desktop login. | Log into the MacBook GUI desktop and launch the agent inside the Aqua session. |
