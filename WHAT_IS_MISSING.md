# WHAT_IS_MISSING.md
## Remaining Architectural Gaps and Unimplemented Frontiers

**Audit Completed:** October 2026  

---

### 1. Model-Centric Agent Deliberation Synthesis
- **Current State:** The `CouncilDeliberationSystem` and `CompetitiveReasoningEngine` have full message routing, priority mailboxes, and voting structures, but individual agent perspectives in multi-round red/blue competitions are still largely scaffolded rather than invoking independent model personas for every turn.
- **Missing Frontier:** Fully streaming multi-agent deliberation where Director, Architect, Critic, and Risk agents run concurrent live model generations with distinct system prompts and temperature profiles.

---

### 2. Autonomous Background Curiosity Daemon
- **Current State:** The autonomous research loop runs cleanly when triggered (`run_autonomous_research_loop.py`), formulating hypotheses, executing experiments, and committing beliefs.
- **Missing Frontier:** A standing background daemon that continuously monitors telemetry anomalies and automatically spawns hypothesis exploration loops during system idle cycles.

---

### 3. Native Graph Database Backing
- **Current State:** The Universal Knowledge Graph operates via in-memory NetworkX with periodic JSON snapshot serialization (`data/world_state_bootstrap.json`).
- **Missing Frontier:** Native SQLite/DuckDB persistent graph table storage with index-accelerated SPARQL/Cypher-like graph traversals for scaling beyond 100,000 entities.

---

### 4. Dynamic Quantization Telemetry
- **Current State:** Alpha measures latency and token usage via `GatewayTelemetry`.
- **Missing Frontier:** Real-time GPU VRAM and memory bandwidth monitoring exposed directly into `SystemObserver`.
