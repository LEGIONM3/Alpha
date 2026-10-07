# NEXT_ENGINEERING_PRIORITIES.md
## Strategic Engineering Priorities for Project Alpha

**Authored by:** Chief Systems Engineer & Chief Cognitive Architect  
**Date:** October 2026  

---

### Priority 1: Persistent DuckDB/SQLite Knowledge Graph Storage
- **Objective:** Migrate the in-memory NetworkX knowledge graph into an embedded, high-performance SQLite/DuckDB relational schema (`nodes`, `edges`, `attributes`).
- **Benefit:** Guarantees instantaneous, zero-overhead disk persistence across process termination without relying on manual JSON snapshot exports.

---

### Priority 2: Multi-Persona Model Deliberation Pool
- **Objective:** Hook the 18 specialized cognitive archetypes (`ResearchAgent`, `ArchitectAgent`, `RiskAgent`, `SecurityAgent`, `CriticAgent`) into dedicated `PromptGenome` profiles, so council debates consist of real, diverse foundation model deliberations.
- **Benefit:** Elevates council consensus from rule-based aggregation into genuine cognitive multi-perspective synthesis.

---

### Priority 3: Autonomous Idle-Time Curiosity Daemon
- **Objective:** Deploy a background task scheduler that triggers `run_autonomous_research_loop.py` whenever system load drops below 10%, generating hypotheses from newly logged experiences.
- **Benefit:** Fulfills Phase 6 autonomous research vision: knowledge discovery without direct human prompting.

---

### Priority 4: Dynamic Context Window Compactor (KV-Cache Optimization)
- **Objective:** Implement AST-guided semantic token pruning for codebases and memory logs, maximizing context density within Gemma 4's 8,192-token ceiling.
- **Benefit:** Allows Alpha to analyze multi-file refactors and 50+ step execution traces within a single coherent context window.
