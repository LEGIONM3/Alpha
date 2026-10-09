"""Project Alpha: Foundation Model — The Autonomous AGI Core.

This module contains the complete cognitive architecture of Project Alpha's
Foundation Model — a self-aware, autonomous agent that can reason about itself,
use tools to interact with the world, discover and pursue goals autonomously,
and continuously improve its own cognition through reflection and learning.

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    FOUNDATION MODEL AGENT                         │
│  (Self-Aware, Autonomous, Tool-Augmented Cognitive System)       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Memory     │  │   Knowledge  │  │   World      │         │
│  │   Store      │  │   Base       │  │   Model      │         │
│  │              │  │              │  │   (Causal)   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                    │               │
│         ▼                  ▼                    ▼               │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              REASONING & PLANNING ENGINE                │    │
│  │   (Task Decomposition, Strategy Selection, Planning)   │    │
│  └───────────────────────┬────────────────────────────────┘    │
│                          │                                      │
│         ┌────────────────┼────────────────┐                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐        │
│  │   Tool      │  │   Goal      │  │   Self-          │        │
│  │   Use       │  │   Discovery │  │   Improvement    │        │
│  │   Engine    │  │   Engine    │  │   Loop           │        │
│  └─────────────┘  └─────────────┘  └──────────────────┘        │
│         ▲                │                                      │
│         │                ▼                                      │
│         └──────────┬─────┼────────────────────────────┐          │
│                    ▼   │                               │          │
│         ┌─────────────▼──────────────────────────────▼┐          │
│         │              EXECUTION LAYER                  │          │
│         │  (Tool Execution, Validation, Recovery)      │          │
│         └─────────────┬────────────────────────────────┘          │
├───────────────────────┼──────────────────────────────────────────┤
│         Perception    │           Reflection                    │
│         Bus           │  (Continuous self-monitoring, meta-     │
│                        │   cognition, belief revision)          │
└───────────────────────┴─────────────────────────────────────────┘

Usage:
    from alpha.foundation_model import FoundationModelAgent
    agent = FoundationModelAgent(
        workspace_root=Path("/path/to/workspace"),
        model_url="http://localhost:1234/v1",
        identity_path="alpha_identity.md"
    )
    # Start autonomous goal discovery and pursuit
    agent.start()

Author: Gemini (Alpha Principal Systems Engineer)
"""

from pathlib import Path
from typing import Optional

from alpha.foundation_model.agent import FoundationModelAgent
from alpha.foundation_model.reasoning_engine import ReasoningEngine
from alpha.foundation_model.knowledge_store import KnowledgeStore
from alpha.foundation_model.memory_manager import MemoryManager
from alpha.foundation_model.goal_discovery import GoalDiscoveryEngine
from alpha.foundation_model.tool_use_engine import ToolUseEngine
from alpha.foundation_model.self_improvement import SelfImprovementLoop
from alpha.foundation_model.planner import Planner
from alpha.foundation_model.world_model import WorldModel

__version__ = "1.0.0"
__all__ = [
    "FoundationModelAgent",
    "ReasoningEngine",
    "KnowledgeStore",
    "MemoryManager",
    "GoalDiscoveryEngine",
    "ToolUseEngine",
    "SelfImprovementLoop",
    "Planner",
    "WorldModel",
]

__author__ = "Gemini <alpha@project-alpha.ai>"
__description__ = "Project Alpha Foundation Model — Autonomous AGI Cognitive Engine"