# ALPHA RUNTIME ARCHITECTURE AUDIT

## Executive Summary

This audit examines the current Alpha Runtime architecture to determine where strategic cognition resides and how it can be properly centralized in the Foundation Model.

---

## CURRENT ARCHITECTURE ANALYSIS

### Component Inventory

| Component | Responsibility | Cognitive Category |
|-----------|---------------|-------------------|
| ObservationEngine | Fetches data from sources (files, APIs, web) | Storage / Execution |
| KnowledgeGapDetector | Compares observations against belief model to find mismatches | Tactical Thinking |
| QuestionGenerator | Generates questions about gaps using template-based rules | Strategic Thinking ⚠️ |
| ResearchEngine | Executes searches and queries across data sources | Execution / Storage |
| HypothesisEngine | Formulates hypotheses from gap + question pairs | Strategic Thinking ⚠️ |
| GoalDiscoveryEngine | Selects which hypotheses to pursue based on pre-defined scoring rules | Strategic Thinking ⚠️ |
| RuntimeCycle | Orchestrates the cycle through all components | Tactical Thinking |

---

## FINDINGS: Where Does Cognition Reside?

### ❌ Current Distribution (INCORRECT)

```
┌─────────────────────────────────────────────────────────┐
│                    CURRENT ARCHITECTURE                  │
├──────────────────┬─────────────┬──────────────┬───────────┤
│ ObservationEng   │ KnowledgeGap│ ResearchEngr │ Storage  │  ← EXECUTION only
│ (fetches data)   │ Detector    │ (executes tools│         │
├──────────────────┼─────────────┴──────────────┼───────────┤
│ QuestionGenr     │ HypothesisEng   │ GoalDiscvry │ Runtime  │  ← TACTICAL + STRATEGIC
│ (template rules) │ Engine         │ Engine       │ Cycle    │  ← PROBLEM: Strategy in runtime!
├──────────────────┼─────────────────────────────┴──────────┤
│                  │                   Foundation Model      │
│   (No cognitive  │                = NOT INVOLVED           │
│    role defined) │                                         │
└──────────────────┴─────────────────────────────────────────┘
```

**The Problem:** The current architecture treats question generation, hypothesis formulation, and goal selection as rule-based operations executed by the runtime. The Foundation Model is not the *driver* of cognition — it is merely a tool invoked at specific checkpoints.

### ✅ Correct Distribution (TARGET STATE)

```
┌─────────────────────────────────────────────────────────┐
│              TARGET ARCHITECTURE                         │
├──────────────────┬─────────────┬──────────────┬───────────┤
│ ObservationEng   │ KnowledgeGap│ ResearchEngr │ Storage  │  ← EXECUTION only
│ (fetches data)   │ Detector    │ (executes tools│         │
├──────────────────┼─────────────┴──────────────┼───────────┤
│                  │                   Foundation Model      │  ← STRATEGIC COGNITION
│   Runtime Core   │                CuriosityDirector        │
│   (orchestration)│                = THE BRAIN              │
└──────────────────┴─────────────────────────────┬──────────┘
                                                  │
                     ┌─────────────────────────────┼─────────────────────────────┐
                     ▼                             ▼                             ▼
              Investigation Targets         Research Plans              Priority Rankings
              (what to investigate)          (how/where)                (order of pursuit)
```

---

## DETAILED COMPONENT ANALYSIS

### 1. ObservationEngine → Execution / Storage ✅

**Current Role:** Fetches observations from configured sources.

**Classification:** Pure execution layer. No decision-making occurs here. It observes but does not interpret.

**Verdict:** Correctly placed in runtime. No changes needed.

---

### 2. KnowledgeGapDetector → Tactical Thinking ⚠️

**Current Role:** Compares incoming observations against stored beliefs, identifies mismatches.

**Classification:** **Tactical** — performs a comparison operation defined by the system. It does NOT decide *what* gaps matter or *why* they matter. That decision (which gap is worth investigating) should be strategic.

**Verdict:** Acceptable as-is for now. The gap *detection* itself is tactical; the gap *prioritization* is what's misplaced elsewhere.

---

### 3. QuestionGenerator → Strategic Thinking ❌

**Current Role:** Generates questions using template-based rules (e.g., "Why did X happen?", "What if Y changed?").

**Classification:** **STRATEGIC**. This is where the system decides *what to ask*. Template-based generation is brittle, context-blind, and cannot adapt to novel situations. The Foundation Model should be generating these questions based on:
- The specific contradiction observed
- The domain context of the belief being challenged
- The epistemic state (how certain we are)
- The potential downstream value of the answer

**Verdict:** MUST move to Foundation Model. Template-based question generation is a failure mode — it produces generic questions that rarely yield novel insights.

---

### 4. ResearchEngine → Execution / Storage ✅

**Current Role:** Executes searches, queries databases, calls APIs, reads files.

**Classification:** Pure execution layer. It does not decide *what* to search for or *where*. Those decisions come from the strategic layer (QuestionGenerator).

**Verdict:** Correctly placed in runtime. No changes needed.

---

### 5. HypothesisEngine → Strategic Thinking ❌

**Current Role:** Combines a question + gap information using rule-based pattern matching to produce hypotheses.

**Classification:** **STRATEGIC**. This is the heart of scientific reasoning: forming testable explanations for anomalies. A rule-based system will only ever produce hypotheses that match pre-defined templates — it cannot discover genuinely novel connections. The Foundation Model, with its world model and causal reasoning capabilities, should generate hypotheses by considering:
- Mechanisms that could explain the gap
- Analogies from other domains
- Counterfactual extrapolations
- Multi-variable interactions

**Verdict:** MUST move to Foundation Model entirely.

---

### 6. GoalDiscoveryEngine → Strategic Thinking ❌

**Current Role:** Scores hypotheses using a pre-defined scoring rubric (e.g., "novelty score," "feasibility score") and selects the top-K for investigation.

**Classification:** **STRATEGIC**. This is *meta-cognition*: deciding what to pursue next. The current implementation uses static weights on fixed criteria. A truly autonomous agent must dynamically weigh:
- Epistemic value (how much would this reduce uncertainty?)
- Opportunity cost (what are we giving up by not investigating this?)
- Temporal urgency (does this change as time passes?)
- Resource constraints (can we actually investigate this right now?)

**Verdict:** MUST move to Foundation Model. The scoring function itself should be a reasoning task, not a pre-defined formula.

---

### 7. RuntimeCycle → Tactical Thinking ✅

**Current Role:** Orchestrates the cycle: observe → detect gap → ask question → hypothesize → select goal → research → update.

**Classification:** **Tactical**. It executes a predefined sequence of operations. It does not decide *when* to stop, *which* branch to take when there are multiple paths, or *how long* any phase should last.

**Verdict:** Acceptable as the orchestrator layer. It is the "spine" — the skeleton that runs but doesn't think. The brain (curiosity/strategic reasoning) moves out of it into a dedicated cognitive module.

---

## THE CORE PROBLEM IDENTIFIED

The current architecture suffers from **cognitive dislocation**: strategic decisions about *what to investigate* are made by components whose sole job is to execute the cycle, not to think strategically.

This creates:
- **Brittleness** — template-based question generation fails on novel situations
- **Short-sightedness** — no ability to recognize when a line of inquiry has gone stale or when an unexpected opportunity has emerged
- **Inflexibility** — cannot pivot based on surprising evidence because the "decision" points are fixed

---

## THE SOLUTION: CuriosityDirector

The solution is a single, unified strategic reasoning module driven by the Foundation Model that receives:

1. **Observations** — raw data from the world (observations engine)
2. **World Model** — current state of knowledge and beliefs
3. **Beliefs** — structured representations of what we know
4. **Contradictions** — explicit mismatches between belief and observation
5. **Confidence Scores** — quantified uncertainty in each belief

And produces:

1. **Investigation Targets** — what specific questions to ask
2. **Research Plans** — concrete steps to gather evidence for/against hypotheses
3. **Priority Rankings** — ordered list of which paths to pursue first
4. **Autonomous Goals** — higher-order objectives that emerge from the situation

This module is NOT a rule engine. It is a cognitive agent that *thinks* about what it should know, why it matters, and how to find out.

---

## ARCHITECTURAL SHIFT SUMMARY

```
BEFORE: Heuristic Rule Engine → Fragile, brittle, template-bound
AFTER:  Foundation Model Reasoning → Adaptive, generative, world-model aware
```

The shift is from **"run these rules on this data"** to **"reason about what you don't know and how to learn it."**

---

## NEXT STEPS

1. Implement the CuriosityDirector as a Foundation Model-driven cognitive module
2. Replace heuristic components with lightweight orchestration that delegates to the Director
3. Run 50 autonomous cycles measuring genuine exploratory behavior vs. scripted loops
4. Compare quality of generated questions, hypotheses, and goals against template-based baselines

**The goal is not just "making things smarter" but making Alpha an *agent* rather than a calculator.**

---
*Audit completed by Alpha Foundation Intelligence | 2026-10-07*