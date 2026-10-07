# CURRENT_TRUTH_LAYER.md
## Epistemology & Truth Layer Architecture

**Authored by:** Chief Cognitive Architect  
**Subsystem:** `alpha/world_model/epistemology/`  
**Date:** October 2026  

---

### 1. Foundational Epistemic Invariant

> **No belief may exist without empirical evidence.**  
> Alpha does not store unverified assertions as facts; it maintains confidence-weighted **Beliefs** grounded in verifiable evidence chains.

---

### 2. Evidence Architecture

1. **Evidence Registry (`EvidenceRegistry`):**
   - Catalogs all observations, execution results, test logs, and sensory data.
   - Core fields: `evidence_id`, `statement`, `polarity` (`SUPPORTING`, `CONTRADICTING`, `NEUTRAL`), `strength` (`WEAK`, `MODERATE`, `STRONG`), `source_type`, `source_id`, `timestamp`.
2. **Evidence Ranking & Aggregation (`EvidenceRankingSystem`, `EvidenceAggregator`):**
   - Weights evidence by credibility (e.g. formal proof / deterministic execution = 1.0, peer consensus = 0.8, single sensory observation = 0.6).
   - Computes composite evidential mass before updating belief states.

---

### 3. Belief Lifecycle: Evolution, Decay, and Falsification

Every belief possesses an active lifecycle managed by `BeliefSystem`:
1. **Formation:**
   - Requires non-empty `evidence_ids` or verified `sources`.
   - Attempting to form a belief without evidence raises `ValueError("Epistemological constraint violated: No orphan beliefs allowed")`.
2. **Strengthening:**
   - As new supporting evidence arrives, confidence increases asymptotically toward 1.0 via $\Delta c = \delta \times (1.0 - c)$.
3. **Weakening & Contradiction Resolution:**
   - Contradicting evidence immediately penalizes confidence ($\Delta c = -0.25$) and records a contradiction trace.
   - If contradicting evidence exceeds supporting evidence, the belief undergoes epistemic review.
4. **Temporal Decay:**
   - Unverified beliefs subject to decay over elapsed virtual time: $c(t) = c_0 \cdot e^{-\lambda t}$.
5. **Death (Falsification & Retirement):**
   - If confidence falls below 0.05, the belief transitions to `LifecycleState.DEAD` with recorded autopsy notes.
