# PROJECT ALPHA — PHASE 0: REPOSITORY AND ENVIRONMENT BASELINE AUDIT FOR APPLE SILICON MAC AGENT

**Date:** October 10, 2026
**Host System (Controller):** Windows 11 (`AMD64`), Lenovo Legion
**Target Remote System (Actuator):** Apple Silicon MacBook Air M2 (`arm64` / macOS)
**Repository:** `<LOCAL_ALPHA_WORKSPACE>`
**Baseline Branch:** `phase-m-remediation` (`0bc3ec5`)
**Feature Branch:** `feature/mac-agent-m2-setup`

---

## 1. Git Repository & Commit Lineage

- **Baseline Commit History (Top 5 prior to feature branch):**
  - `0bc3ec5` — Phase N: Implement real Laya closed-loop computer use and independent verification
  - `ea0fb8d` — feat(phase-m1): runtime integrity audit, discrepancy resolution, and readiness gate certification
  - `53fb196` — feat(phase-m): Autonomous Software Remediation and Verified Self-Improvement
  - `f5faf9c` — feat(reality-learning): transform Alpha into evidence-driven system with Qwen 3.8 sole strategic reasoner and complete 100-cycle validation
  - `311dffe` — chore: baseline project alpha checkpoint
- **Working Tree Status:** Uncommitted state/telemetry files and historical phase reports in the working tree are strictly preserved and excluded from the `feature/mac-agent-m2-setup` commit.

---

## 2. Live Model Endpoint & Cognitive Authority Verification

- **Probed Endpoint:** `http://127.0.0.1:1235/v1` (resolved dynamically via `resolve_default_model_endpoint()` across ports 1234 and 1235).
- **HTTP Status:** `200 OK`
- **Active Models Hosted in LM Studio:**
  1. `qwen3.8-9b-heretic-uncensored` (Sole Strategic & Action Reasoning Authority)
  2. `text-embedding-nomic-embed-text-v1.5` (Embedding Provider)

---

## 3. Existing Interfaces Identified for Reuse

To ensure architectural unity and avoid duplicate planners, safety systems, or evidence graphs, the following existing Alpha interfaces were audited and selected for direct integration:

### 3.1 Cognitive Runtime & Loop Orchestration
- **`AlphaRuntimeCycle`** ([`alpha/runtime_cycle.py`](alpha/runtime_cycle.py)): Orchestrates the primary `Observe -> Research -> Hypothesize -> Verify -> Revise Beliefs -> Discover Goals -> Act -> Learn` cycle.
- **`LayaClosedLoopRuntime`** ([`alpha/computer_use/closed_loop.py`](alpha/computer_use/closed_loop.py)): Executes bounded multi-step computer-use tasks (`ComputerUseTask`), queries `QwenStrategicReasoner` for `ModelActionProposal` JSON outputs, enforces permissions/budgets, actuates, acquires independent post-action observations, computes `PostActionVerification`, and persists `ComputerUseTrajectory` records.

### 3.2 Laya Contracts & Tool Routing
- **`ILayaObservationTool`**, **`ILayaResearchTool`**, **`ILayaExecutionTool`**, and **`LayaContractRegistry`** ([`alpha/computer_use/contracts.py`](alpha/computer_use/contracts.py)): Formal capability provider contracts.
- **`ComputerUseTool`** ([`alpha/computer_use/computer_use_tool.py`](alpha/computer_use/computer_use_tool.py)) & **`LayaComputerInterface`** ([`alpha/computer_use/laya.py`](alpha/computer_use/laya.py)): Existing local computer-use bridge.
- **`LayaToolRouter`** ([`alpha/computer_use/router.py`](alpha/computer_use/router.py)): Routes `CognitiveActionIntent` objects.

### 3.3 Permission & Safety Gateways
- **`PermissionGate`**, **`ApprovalToken`**, and **`ComputerActionType`** ([`alpha/computer_use/permissions.py`](alpha/computer_use/permissions.py)): Distinguishes open passive sensory actions from restricted mutative actions (`WRITE`, `EXECUTE`, `DELETE`, `MODIFY_CONFIG`, `COMPUTER_TASK`), verifying cryptographic token hashes and expiration bounds.

### 3.4 Epistemic Lineage, Trajectory Persistence & Verification
- **`EvidenceGraph`** ([`alpha/evidence_graph/graph.py`](alpha/evidence_graph/graph.py)): Persists `EvidenceNode`, `ObservationNode`, `FindingNode`, `HypothesisNode`, `Belief`, `GoalNode`, `ActionNode`, `OutcomeNode`, and `LearningNode` to `data/evidence_graph.json`.
- **Trajectory Storage**: Atomic JSON trajectories in `data/trajectories/{task_id}_{run_id}.json` and JSONL appends in `data/decision_audit_trail.jsonl`.

---

## 4. Network & Physical Host Topology

- **Controller Host:** Windows 11 Lenovo Legion (example private LAN IP `192.168.1.50` or Tailscale IP `100.64.0.50`, Loopback `127.0.0.1`).
- **Remote Target:** Apple Silicon MacBook Air M2 (separate physical computer; example private LAN IP `192.168.1.100` or Tailscale IP `100.64.0.100`).
- **Integration Strategy:**
  - Create a modular, self-contained macOS agent package (`alpha/computer_use/mac_agent/`) that runs inside the logged-in macOS user's graphical Aqua session and exposes a versioned (`/v1`), authenticated, private-interface-bound REST API.
  - Extend `LayaClosedLoopRuntime` and `ComputerUseTool` on the Legion to support `MAC_BROWSER` and `MAC_NATIVE` modalities via `MacComputerUseClient`, reusing Qwen deliberation, `PermissionGate`, `EvidenceGraph`, and trajectory persistence without touching the Legion's physical mouse or keyboard.
  - Because the development shell is running on the Windows 11 Legion and no remote Mac IP is currently reachable in the test environment, all platform-independent components, security policies, API endpoints, client-server protocols, and real Playwright Chromium closed-loop workflows are tested live over loopback/private HTTP, while native Darwin/Aqua/AXUIElement tests are clearly isolated and marked `NOT RUN` (`SKIPPED`) on Windows.
