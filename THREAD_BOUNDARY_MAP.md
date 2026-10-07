# THREAD_BOUNDARY_MAP.md
## Project Alpha: Comprehensive Concurrency & Thread Boundary Architecture

**Architect:** Principal Systems Engineer (Gemini / Alpha Architecture Group)  
**Status:** ACTIVE & ENFORCED  
**Root Defect Addressed:** `RuntimeError: call_from_thread must run in a different thread from the app`

---

### 1. Executive Summary & Root Cause Investigation

#### 1.1 The Root Cause Defect
During autonomous execution in the Terminal Cognitive Console (TCC), the application encountered:
```
RuntimeError: The `call_from_thread` method must run in a different thread from the app
```

#### 1.2 Investigation & Trace Analysis
1. **Direct UI-Cognition Coupling:**
   In earlier iterations, the UI layer (`AlphaConsoleApp` in `alpha/ui/app.py`) directly owned cognitive execution. When `/autonomous` was invoked or `--autonomous` was passed at boot, the Textual UI scheduled:
   ```python
   self.run_worker(self._handle_autonomous_command(), group="autonomous", exclusive=True)
   ```
   Because `self._handle_autonomous_command()` was defined as an `async def` coroutine, Textual assigned it to run inside the **main UI asyncio event loop thread**.
   
2. **Synchronous Inference and Callbacks on Main Thread:**
   Inside `run_autonomous_cycle()`, synchronous model calls (`chat_completion`) and progress callbacks (`safe_post_ui`) were invoked.
   In `safe_post_ui`:
   ```python
   if getattr(self, "_thread_id", None) == threading.get_ident():
       callback(*args, **kwargs)
   else:
       self.call_from_thread(callback, *args, **kwargs)
   ```
   When callbacks nested, or when events were dispatched through logging listeners across varying asyncio task frames, `self.call_from_thread` was invoked from the same thread as the Textual app loop, triggering Textual's invariant check:
   ```python
   if self._thread_id == threading.get_ident():
       raise RuntimeError("The `call_from_thread` method must run in a different thread from the app")
   ```

3. **Fundamental Architectural Flaw:**
   The UI owned the cognitive lifecycle. When the UI blocked for model generation (which can take several seconds for local SLMs such as `gemma-4-e4b-it-ultra-uncensored-heretic`), the UI froze. If the UI closed, cognition ceased. If a callback threw an exception, the entire console crashed.

---

### 2. The Architectural Invariant Law

> **FIRST LAW OF ALPHA CONCURRENCY:**  
> The UI may never own cognition.  
> The UI may never own autonomous execution.  
> The UI is a decoupled visualization and telemetry subscriber client only.

```
+-------------------------------------------------------+
|                USER / CONSOLE TERMINAL                |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|              UI Client (TCC / Textual)                |
|  - Renders Active State & Live Streams                |
|  - Subscribes to Event Bus & Cognitive Feeds          |
|  - Pushes User Intent to Perception Bus               |
+-------------------------------------------------------+
                           |
                     (Event Bus)
                           v
+-------------------------------------------------------+
|            PerceptionBus & Event Pipeline             |
|  - Filesystem Changes                                 |
|  - Tool Outputs / Runtime Telemetry                   |
|  - Agent Messages & Memory Mutations                  |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|      Persistent Cognitive Runtime (Background)       |
|  - AwarenessManager (Continuous State Tracker)        |
|  - AutonomousThoughtEngine (Perceive -> Reflect)      |
|  - InternalCommentaryEngine (Real Model Inferences)   |
|  - SelfMonitoringAgent & DevelopmentSupervisor        |
+-------------------------------------------------------+
         |                     |                 |
         v                     v                 v
+-----------------+   +-----------------+   +------------------+
|  Memory System  |   |   World Model   |   |  Agent Society   |
| (Dense Vectors  |   | (Epistemology   |   | (18 Archetypes,  |
|  & Persistence) |   |  & Ontologies)  |   |  Deliberation)   |
+-----------------+   +-----------------+   +------------------+
         \                     |                 /
          \                    |                /
           v                   v               v
+-------------------------------------------------------+
|             Model Layer (Local Foundation)            |
|       http://localhost:1234/v1 (Gemma 4 & Nomic)      |
+-------------------------------------------------------+
```

---

### 3. Comprehensive Thread Identification & Boundary Map

| Thread Domain | Execution Mechanism | Thread Identity / Name | Permitted Operations | Forbidden Operations |
|---|---|---|---|---|
| **UI Thread** | Textual asyncio Event Loop | `MainThread` | UI rendering, widget mounting, terminal keybindings (`F12`, `ctrl+c`), reading decoupled event queue | Blocking I/O, synchronous HTTP inference calls, owning autonomous loops, direct SQLite writes |
| **Cognitive Runtime Thread** | Background Daemon Thread | `AlphaCognitiveRuntime` | Autonomous thought cycles, perception processing, orchestrating reflections, maintaining active cognitive state | Calling UI widget methods directly, blocking Textual event loop |
| **Perception Bus Thread** | Worker / Queue Thread | `AlphaPerceptionBus` | Ingesting filesystem, agent, and memory events; routing to subscribers | Heavy reasoning, synchronous blocking model calls |
| **Model Inference Workers** | ThreadPoolExecutor (max 4) | `AlphaModelWorker-*` | HTTP POST to `http://localhost:1234/v1/chat/completions`, streaming chunks, embeddings | Direct UI manipulation, state mutations without locks |
| **Memory & Storage Workers** | Synchronous with RLock | Caller Thread with RLock | SQLite queries, JSON vector indexing, cosine search ranking | Cross-thread mutation without locks |
| **Self-Monitoring & Supervisor** | Scheduled Periodic Workers | `AlphaMonitorWorker` | System metrics, dead code checks, reality validation, drift analysis | Mutating cognitive state without AwarenessManager |

---

### 4. Decoupled Communication Protocol (Eliminating `call_from_thread`)

To eliminate `call_from_thread` violations permanently:

1. **Inbound UI Queue (`queue.Queue`):**
   Cognitive Runtime, PerceptionBus, and Model Workers never directly invoke UI callbacks.
   Instead, they post telemetry records to a thread-safe `inbound_ui_queue`.

2. **UI Polling Pump (`_drain_inbound_events`):**
   The Textual UI executes a non-blocking interval timer (`self.set_interval(0.1, self._drain_inbound_events)`):
   ```python
   def _drain_inbound_events(self) -> None:
       while not self.ui_event_queue.empty():
           try:
               event = self.ui_event_queue.get_nowait()
               self._dispatch_event_to_widgets(event)
           except queue.Empty:
               break
   ```
   Because events are processed exclusively within the Textual app's own thread, **`call_from_thread` is never required**, eliminating thread assertion errors by design.

3. **Zero UI-to-Cognition Blocker:**
   User queries typed into TCC are posted to `PerceptionBus`. The Cognitive Runtime picks them up asynchronously. The UI remains responsive at 60 FPS regardless of local model inference duration.

---

### 5. Thread Safety Guarantees

1. **Re-entrant Locks on Shared State:**
   `CognitiveWorldModel`, `IdentityState`, and `MemoryStorage` protect internal state with `threading.RLock()`.
2. **Single Writer Principle for Cognitive Workspace:**
   `ACTIVE_COGNITIVE_STATE.json` can be read by any agent or thread, but can **only** be modified and written by `AwarenessManager`.
3. **Graceful Degradation:**
   If the UI is terminated, `AlphaCognitiveRuntime` continues running uninterrupted in the background. If the UI is re-attached, it reads current state from `ACTIVE_COGNITIVE_STATE.json` and resumes stream subscription.
