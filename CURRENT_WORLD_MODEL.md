# CURRENT_WORLD_MODEL.md
## Cognitive World Model: Reality-Based Intelligence Reference

**Authored by:** Chief Cognitive Architect  
**Subsystem:** `alpha/world_model/`  
**Date:** October 2026  

---

### 1. Architectural Philosophy

Project Alpha does not treat foundation model memory as an unstructured bag of words or unranked vector store. Instead, Alpha models external and internal reality through an explicit, grounded **Cognitive World Model**.

Intelligence transitions from *Memory-Based* to *Reality-Based*:
- Facts are replaced by confidence-calibrated **Beliefs** backed by verifiable evidence.
- Correlations are transformed into **Causal Links** supporting Pearl-style counterfactual reasoning.
- State is modeled across **12 cognitive dimensions** and **4 temporal modes** (Current, Historical, Future, and Simulated).

---

### 2. Universal Ontology: 25 Canonical Entity Types

1. `Person` — External human users and stakeholders.
2. `Organization` — Operational teams and administrative entities.
3. `Project` — Multi-task cognitive initiatives (e.g. `Project Alpha Phase 4`).
4. `Agent` — Autonomous cognitive entities across 18 archetypes.
5. `Skill` — Reusable composable procedural competencies.
6. `Tool` — Executable operational primitives in isolated sandboxes.
7. `Task` — Discrete units of work with contracts and dependencies.
8. `Goal` — High-level objectives guiding agent behavior.
9. `Memory` — Raw episodic records of prior operations.
10. `Experience` — Structured execution traces with lessons.
11. `Document` — Architectural specifications, ADRs, and guidelines.
12. `Concept` — High-order abstract generalizations.
13. `Rule` — Operational constraints and heuristics.
14. `Belief` — Confidence-weighted empirical propositions.
15. `Observation` — Direct sensory, telemetry, or execution data.
16. `Event` — Point-in-time state changes on timelines.
17. `Capability` — High-level capabilities provided by agents, models, or tools.
18. `Resource` — Bounded assets (tokens, memory, worker threads, budget).
19. `Risk` — Potential failure modes with probability and severity.
20. `Decision` — Formally approved choices with recorded rationales.
21. `Hypothesis` — Scientific or operational conjectures undergoing testing.
22. `Theory` — Synthesized, validated, and replicated principles.
23. `Prediction` — Forecasted future states or performance estimates.
24. `Simulation` — Isolated sandbox branches for safe counterfactual testing.
25. `Relationship` — Semantic, causal, or hierarchical links between entities.

---

### 3. The 14 Canonical Relationship Types

- `depends_on`: Prerequisites and blocking dependencies.
- `causes`: Directional causal mechanisms with calibrated strengths.
- `supports`: Evidential grounding for beliefs and theories.
- `contradicts`: Refuting evidence or conflicting beliefs.
- `created_by`: Originating actor provenance.
- `belongs_to`: Hierarchical parent-child clustering.
- `derived_from`: Lineage of synthesized concepts or rules.
- `improves`: Performance evolution links.
- `replaces`: Version supercession and deprecation.
- `uses`: Operational tool and capability consumption.
- `validates`: Deterministic verification and testing links.
- `contains`: Structural encapsulation.
- `references`: Citation and documentation links.
- `related_to`: Generic bidirectional semantic association.

---

### 4. World State Engine & Reality Sandbox

The `WorldStateEngine` captures synchronized snapshots across all 12 dimensions:
- **Current State:** The active operational truth.
- **Historical State:** Point-in-time checkpoints enabling time-travel debugging.
- **Future State:** Forward-projected task completion and risk realization.
- **Simulated State:** Reality sandbox branches (`WorldSimulationEngine`) for safe counterfactual experimentation with guaranteed zero leakage into production.
