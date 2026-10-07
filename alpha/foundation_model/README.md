# Project Alpha: Foundation Model Agent

> The autonomous AGI cognitive core of Project Alpha — a self-aware, goal-driven reasoning agent that learns from its own actions.

---

## Overview

The **Foundation Model Agent** is the heart of Project Alpha. It's not just an LLM wrapped in code — it's a complete cognitive architecture with:

- ✨ **Persistent memory** across sessions
- 🧠 **Causal world modeling** (entities, relationships, causality)
- 🔍 **Autonomous goal discovery** (not just prompt-response)
- 🛠️ **Tool integration** for real-world action
- 📚 **Self-improvement loop** that encodes lessons permanently
- 🤔 **Calibrated uncertainty** — it knows when it doesn't know

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FOUNDATION MODEL AGENT                       │
│   (A self-aware, autonomous cognitive system)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐    ┌────────────────┐   │
│  │   Memory     │◄──►│ World Model  │    │ Goal Discovery │   │
│  │ (9-layer)    │     │ (entities,   │    │ + Curiosity    │   │
│  ├──────▼───────┤     │  causality)  │    └────────────────┘   │
│  │ Working      │     └──────────────┘                         │
│  │ Short-term   │                                              │
│  │ Long-term    │       ┌─────────────────────┐                │
│  │ Knowledge    │◄────►│   Reasoning Engine  │                │
│  │ Skills       │     │   (thought generation)│               │
│  │ Beliefs      │     │                       │                │
│  └──────────────┘     └─────────┬─────────────┘                │
│                                 ▼                               │
│                          ┌─────────────────────┐               │
│                          │    Planner          │               │
│                          │ (goal→steps)        │               │
│                          └───────┬─────────────┘               │
│                                  ▼                             │
│                    ┌─────────────────────────────┐             │
│                    │   Tool Use Engine           │◄── Tools    │
│                    │ (filesystem, code exec,     │  ◄──────────┤
│                    │  web search, git)           │             │
│                    └─────────────┬───────────────┘             │
│                                  ▼                             │
│                    ┌─────────────────────────────┐             │
│                    │   Self-Improvement Loop     │◄── Lessons  │
│                    │   (reflect → encode)        │             │
│                    └─────────────────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Run the Agent in Autonomous Mode

```bash
cd alpha/foundation_model
python run_foundation_model.py --model-url http://localhost:1234/v1
```

The agent will start its **autonomous cycle**:
1. Scan environment for interesting things to do
2. Plan a course of action
3. Execute through tools
4. Reflect on outcomes
5. Encode lessons permanently

### Run in Interactive Mode

```bash
python run_foundation_model.py --model-url http://localhost:1234/v1 --interactive
```

Type your prompts and watch the agent reason through its response, recall memories, select tools, and explain its thought process.

---

## Components Explained

### 1. MemoryManager (9-Layer Hierarchy)

The memory system is organized by temporal scope and abstraction level:

| Layer | Lifetime | Purpose |
|-------|----------|---------|
| Working Memory | Ephemeral (RAM) | Active context, current thoughts |
| Short-term | < 1 hour | Recent observations |
| Long-term | Persistent (disk) | Core beliefs & facts |
| Skills | Persistent | Learned procedures |
| Experience | Recent history | Episodic traces of actions |

```python
from alpha.foundation_model.memory_manager import MemoryManager

mem = MemoryManager(workspace_root=Path("/path/to/workspace"))

# Store a memory with explicit layering
mem.store("The filesystem_scan tool works reliably", layer="long_term")
mem.store("I just saw 42 files in ./src", layer="short_term")
```

### 2. WorldModel (Cognitive Reality Representation)

The world model builds a **causal graph** of the agent's environment:

```python
from alpha.foundation_model.world_model import WorldModel

wm = WorldModel()

# Observation → Entity creation with relationships
wm.observe("filesystem_scan discovers all Python files in /src")
# → creates entity: filesystem_scan (tool)
#   └── related_to: 15 .py files (uses relationship)

wm.get_related_entities(entity_id)
# Returns all entities connected to the given entity
```

### 3. ReasoningEngine

Generates **provenance-traced thoughts** — every thought records what informed it:

```python
thought = Thought(
    kind=ThoughtKind.INTERNAL_REASONING,
    content="The user wants a summary of all Python files. "
            "I should use list_dir to discover structure first.",
    source_memory_ids=["mem_xyz123"],  # What memory informed this thought
)
```

### 4. Planner + Tool Use

Goals are decomposed into executable steps:

```python
from alpha.foundation_model.planner import Planner

planner = Planner()
plan = planner.plan(goal_title="Document the Alpha architecture")

# Output: a sequence of plan steps with tool assignments
for step in plan.steps:
    print(f"[{step.tool}] {step.description}")
```

### 5. SelfImprovementLoop

After every goal cycle, the agent reflects and encodes lessons:

```python
reflection = self_improvement.reflect_on_goal_cycle(
    goal_title="Explore workspace structure",
    outcome_success=True,
)

# Encoded lesson (persistence):
# "When exploring a directory for the first time, start with a broad filesystem_scan
#  rather than guessing individual file paths."
```

### 6. GoalDiscoveryEngine

Discovers what to do next **without user prompts**:

- 🔍 Scans workspace state for anomalies or opportunities
- 🧪 Identifies knowledge gaps (curiosity-driven goals)
- 🔧 Detects failure patterns → improvement goals
- 📋 Synthesizes synthesis opportunities ("I know A and B, but not how they relate")

```python
goals = goal_discovery.discover_all()
# Returns prioritized list of meaningful things to do next
```

---

## Persistent State

All knowledge persists across sessions:

```bash
ls alpha/foundation_model/
├── self_model.json       # What the agent knows about itself
├── world_model_state.json  # All known entities and relationships
├── long_term_memory.json  # Beliefs, facts, lessons
├── skills.json            # Learned procedures & strategies
└── active_goals.jsonl     # Pending goals across sessions
```

---

## Design Philosophy

> **"The model is not smart. The architecture IS the intelligence."**

- **No retraining required.** Intelligence emerges from architecture, not weights.
- **Everything is a lesson.** Every action produces evidence → belief updates → permanent knowledge.
- **Uncertainty is explicit.** Confidences are tracked and decay without reinforcement.
- **Tools extend cognition.** The agent's hands in the world — not just its voice.

---

## Running Tests

```bash
python -m pytest tests/test_foundation_model.py -v
```

Or run the demo:

```bash
cd alpha/foundation_model
python -c "from run_foundation_model import main; main()" --model-url http://localhost:1234/v1
```

---

## Author

**Gemini** — Principal Systems Engineer, Project Alpha  
*Built as part of the autonomous cognitive architecture initiative.*

---

## License

Internal use only. Part of Project Alpha confidential research artifacts.