# MODEL_USAGE_AUDIT.md
## Deep Audit: Model-Centric Reasoning vs. Heuristic Logic in Project Alpha

**Executed by:** Chief Cognitive Architect & Chief Failure Investigator  
**Audit Target:** All 8 major cognitive reasoning pathways  
**Date:** October 2026  

---

### Executive Summary

A comprehensive line-by-line audit of Project Alpha's reasoning subsystems was conducted to determine whether each subsystem performs **real foundation model inference** (`http://localhost:1234/v1`) or relies on **hardcoded heuristics, string templates, or mock generators**.

The investigation revealed that while Alpha possesses world-class structural scaffolds (DAGs, ontologies, state machines, and multi-agent protocols), the reasoning logic inside several core pipelines was purely heuristic.

---

### Subsystem Reasoning Reality Audit

| Subsystem Domain | Primary File | Current Reasoning Engine | Model Invocation? | Audit Findings & Technical Detail |
| :--- | :--- | :--- | :--- | :--- |
| **1. Planning** | `alpha/planner/planner.py` | Heuristic topological converter | **NO (Heuristic)** | Transforms `TaskTree` into `ExecutionPlan` using static topological ordering, hardcoded complexity multipliers (150/300/500/800 tokens), and static fallback strings. Does not query the foundation model to optimize step sequences. |
| **2. Goal Decomposition** | `alpha/decomposer/decomposer.py` | Fixed 3-Phase Template Scaffold | **NO (Heuristic)** | If `structured_steps` not provided, applies a static 3-phase decomposition scaffold: SubGoal 1 (Analysis), SubGoal 2 (Execution), SubGoal 3 (Verification). Ignores domain nuances. |
| **3. Reflection** | `alpha/reflection/engine.py` | Rule-based rubric matcher | **NO (Heuristic)** | Evaluates output non-emptiness and checks for chatty conversational prefixes (`"here is the"`, `"sure,"`). Does not use the model for deep semantic critique or contract reasoning. |
| **4. Knowledge Synthesis** | `alpha/world_model/synthesis/synthesis_engine.py` | Hardcoded string interpolation | **NO (Heuristic)** | Returns fixed template strings (`"{lead_domain} is to upstream inputs as {other_domain} is to cognitive equilibrium"`). Fails to perform genuine cross-domain inductive synthesis. |
| **5. Hypothesis Generation**| `alpha/research/hypotheses/generator.py` | Static template string generator | **NO (Heuristic)** | Iterates over observations and generates boilerplate hypotheses (`"Controlled intervention will eliminate latency spikes within 2 cycles."`). |
| **6. Decision Making** | `alpha/agents/deliberation/council.py` | Heuristic consensus scoring | **NO (Heuristic)** | Multi-agent council tallies numeric fitness weights and red/blue vote counts. Agent positions were simulated rather than model-synthesized. |
| **7. Semantic Memory** | `alpha/tools/discovery.py`, `alpha/memory/` | 128-d hash projection | **NO (Synthetic Vector)** | Projected character n-grams via `hash(tok) % 128` instead of using the local embedding model `text-embedding-nomic-embed-text-v1.5`. (Upgraded via `EmbeddingService`). |
| **8. World Updates** | `alpha/world_model/model.py` | Deterministic graph updates | **HYBRID (Appropriate)** | Ontological state transitions and graph edges are deterministic (by design, guaranteeing provenance and preventing hallucinated entity corruption). |

---

### Remediation Blueprint: Elevating the Model to Primary Cognitive Engine

To transition Alpha from a heuristic scaffold into a truly intelligent cognitive system:
1. **Model-Assisted Decomposer:** When decomposing complex goals, query `gemma-4-e4b` with a structured `json_schema` to produce domain-specific DAG subgoals and tasks.
2. **Model-Assisted Planner:** Use `gemma-4-e4b` to analyze dependencies, forecast bottlenecks, and tailor specific validation contracts and fallback strategies.
3. **Model-Assisted Reflection:** Query `gemma-4-e4b` to critique outputs against task objectives and extract distilled operational lessons.
4. **Model-Assisted Synthesis:** Query `gemma-4-e4b` to synthesize novel principles and analogies across disparate knowledge premises.
5. **Real Embeddings Everywhere:** Permanently wire `EmbeddingService` into tool discovery and memory retrieval.
