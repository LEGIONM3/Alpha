# WHAT_EXISTS.md
## Inventory of Discovered Architectural Components

**Audit Completed:** October 2026  

1. **Foundational Codebase:**
   - 256 Python modules across 22 architectural packages in `alpha/`.
   - 145/145 existing automated unit and integration tests passing.
2. **Local Model Endpoints:**
   - LLM: `gemma-4-e4b-it-ultra-uncensored-heretic` at `http://localhost:1234/v1` (4B thinking model with SSE streaming, tool calling, and JSON schema).
   - Embedding: `text-embedding-nomic-embed-text-v1.5` at `http://localhost:1234/v1/embeddings` (768 dimensions).
3. **Identity & Governance:**
   - Source of truth `alpha_identity.md` with complete mission, values, 5 constitutional articles, 5 constraints, and 4 non-negotiables.
   - `alpha/core/identity.py`: `IdentityLoader`, `IdentityValidator`, `IdentityHashGenerator`, `IdentityDriftDetector`, `ConstitutionEngine`, `IdentityPersistence`.
   - `alpha/agents/governance/governance.py`: 6-stage `ChangeGovernanceSystem`.
4. **Cognitive World Model:**
   - `alpha/world_model/`: 25 entity classes, 14 relation classes, NetworkX knowledge graph, causal engine, 12-dimension world state, temporal timeline, reality sandbox simulation.
   - `alpha/world_model/self_model/`: dynamic introspection answering 10 existential questions.
5. **Truth Layer & Epistemology:**
   - `EvidenceRegistry`, `EvidenceRankingSystem`, `BeliefSystem` enforcing zero orphan beliefs.
6. **Model Intelligence & Scaffolding:**
   - `OpenAICompatibleClient`, `ModelGateway`, `ModelRegistry`, `PromptGenome`, `PromptEvolutionEngine`, `ContextLayoutEngine`, `ContextCompressor`.
7. **Embeddings & Memory:**
   - `EmbeddingService` in `alpha/memory/embedding_service.py` with caching and cosine similarity ranking.
   - `TieredKnowledgeSystem` in `alpha/knowledge/tiered_loader.py` (Tiers 0, 1, 2, 3).
8. **Universal Tools & Sandboxes:**
   - `ToolRegistry`, `ToolSandbox`, `SecureExecutionSandbox` (Python, Shell, Node, Rust), AST verification engines, Git and API intelligence tools.
9. **Boot Sequence:**
   - `alpha_boot.py`: 10-stage fail-safe startup orchestrator.
