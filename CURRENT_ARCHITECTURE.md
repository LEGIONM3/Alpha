# CURRENT_ARCHITECTURE.md
## Definitive Architectural Reference: Project Alpha

**Authored by:** Chief Cognitive Architect & Chief Systems Engineer  
**System State:** Fully Operational Cognitive Operating System  
**Foundation Model:** `gemma-4-e4b-it-ultra-uncensored-heretic` (`http://localhost:1234/v1`)  
**Embedding Model:** `text-embedding-nomic-embed-text-v1.5` (768 dimensions)  
**Date:** October 2026  

---

### 1. High-Level System Architecture

Alpha is structured into five integrated cognitive tiers:

```
+-----------------------------------------------------------------------------------+
|                           TIER 0: INVARIANT GOVERNANCE                            |
|     alpha_identity.md | ConstitutionEngine | Non-Negotiables | Drift Detection     |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|                        TIER 1: COGNITIVE WORLD MODEL                              |
|   Universal Ontology (25 Entities) | Bidirectional Knowledge Graph (14 Relations) |
|      Truth Layer (Evidence + Beliefs) | Causal Engine | World State Engine        |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|                    TIER 2: MULTI-AGENT & DELIBERATION CIVILIZATION                |
|      18 Specialized Archetypes | Priority Mailbox | Blackboard Context            |
|       Council Deliberation | Red/Blue Adversarial Team | Change Governance        |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|                    TIER 3: MODEL INTELLIGENCE & AMPLIFICATION                     |
|     OpenAICompatibleClient (30s) | ModelGateway | Evolved Prompt Genomes          |
|    Context Layout Engine | EmbeddingService (768-d) | Scientific Discovery Loops  |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|                    TIER 4: UNIVERSAL TOOL EXECUTION FABRIC                        |
|   ToolRegistry | SecureExecutionSandbox (Python/Shell) | Deterministic Validators |
|         Filesystem Intelligence | Git Intelligence | API Gateway                  |
+-----------------------------------------------------------------------------------+
```

---

### 2. Core Subsystem Responsibilities

1. **Identity & Constitution (`alpha/core/identity.py`, `alpha_identity.md`):**
   - Immovable foundation specifying Alpha's mission, values, 5 constitutional articles, and 4 non-negotiables.
   - Enforced by `ConstitutionEngine`, generating Tier-0 system prompt headers and blocking illicit actions.
2. **Cognitive World Model (`alpha/world_model/`):**
   - 25 ontological entity types, 14 semantic relationship types, causal graphs, and multi-temporal states.
   - Replaces bare episodic retrieval with reality-grounded causal simulation.
3. **Truth Layer & Epistemology (`alpha/world_model/epistemology/`):**
   - Grounded belief formation requiring ranked empirical evidence.
   - Strict invariant: zero orphan beliefs permitted.
4. **Foundation Model Amplification (`alpha/model_intelligence/`):**
   - Direct integration with local endpoint `http://localhost:1234/v1`.
   - Accommodates reasoning tokens (`reasoning_content`), normalizes structured schemas, and provides genetic prompt evolution.
5. **Embedding & Memory Architecture (`alpha/memory/embedding_service.py`):**
   - 768-dimensional dense vector embeddings generated via `text-embedding-nomic-embed-text-v1.5`.
   - In-memory cosine search backed by persistent disk cache in `data/embedding_cache.json`.
6. **Change Governance (`alpha/agents/governance/`):**
   - 6-stage change gate: Proposal -> Multi-Agent Review -> Canary Simulation -> Executive Approval -> Deployment -> Rollback.
7. **Cognitive Boot Sequence (`alpha_boot.py`):**
   - 10-stage sequential startup ensuring all subsystems validate before entering `OPERATIONAL` state.
