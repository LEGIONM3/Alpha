# CURRENT_LIMITATIONS.md
## Known Architectural Limitations, Trade-offs, and Bounded Scope

**Authored by:** Chief Failure Investigator & Chief Systems Engineer  
**Date:** October 2026  

---

### 1. Model Latency & Reasoning Token Budgets
- **Symptom:** Because `gemma-4-e4b-it-ultra-uncensored-heretic` is a deep-thinking model, it generates 400-600 tokens of internal chain-of-thought (`reasoning_content`) before emitting response text.
- **Limitation:** Complex JSON generation requests require a minimum token budget of 1,000 to 1,200 tokens. Setting `max_tokens < 300` results in output truncated in the thinking phase (`finish_reason: length`).
- **Operational Rule:** All cognitive queries must allocate `max_tokens >= 800` to accommodate internal deliberation.

---

### 2. Context Window Ceiling (8,192 Tokens)
- **Limitation:** The local model instance enforces an 8,192-token context limit.
- **Mitigation:** Alpha employs `TieredKnowledgeSystem` and `ContextCompressor` to prune redundant observations and inject only high-relevance axioms, keeping prompt sizes within 2,000 - 3,500 tokens.

---

### 3. Server-Side Single-Tenant Contention
- **Limitation:** The local LM Studio server executes on a single consumer GPU / CPU thread pool.
- **Observation:** While 8 concurrent threads executed efficiently during benchmarks, sustained high-concurrency loads (> 16 concurrent requests) cause linear queue latency growth.
- **Mitigation:** The `ToolInvocationEngine` and multi-agent scheduler bound concurrency to `max_workers = 4 - 8`.

---

### 4. Persistence Synchronization
- **Limitation:** The NetworkX knowledge graph operates in-memory; graph node updates must be serialized periodically into persistent snapshots.
- **Mitigation:** State snapshots are captured and persisted at boot, after major discovery cycles, and prior to shutdown in `data/world_state_bootstrap.json`.
