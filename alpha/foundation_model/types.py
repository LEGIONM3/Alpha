"""Core types, enums, and base interfaces for the Foundation Model Agent."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

import json
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class ThoughtKind(str, Enum):
    """Classification of an agent's internal thought.
    
    Thoughts represent the internal cognitive steps of the Foundation Model Agent,
    capturing its reasoning process in a way that can be reflected upon and learned from.
    """
    OBSERVATION = "observation"           # Perceived state change or input
    INTERNAL_REASONING = "internal_reasoning"  # Silent contemplation
    MEMORY_RECALL = "memory_recall"       # Retrieving relevant past experiences
    PLANNING = "planning"                 # Deciding on an action sequence
    TOOL_SELECTION = "tool_selection"     # Choosing which tool to use
    EXECUTION = "execution"               # Executing a specific tool/action
    SELF_REFLECTION = "self_reflection"   # Meta-cognitive evaluation of own reasoning
    BELIEF_UPDATE = "belief_update"       # Revising a belief based on new evidence
    GOAL_DISCOVERY = "goal_discovery"     # Discovering a meaningful goal to pursue
    LEARNING = "learning"                 # Encoding a learned lesson into long-term memory


class Thought(BaseModel):
    """A single thought unit in the agent's cognitive trace.
    
    Captures the complete provenance of a cognitive step, enabling full
    retroactive self-analysis and continuous learning.
    """
    id: str = Field(default_factory=lambda: f"thought_{utc_now().strftime('%Y%m%d%H%M%S%f')}")
    kind: ThoughtKind
    content: str
    timestamp: datetime = Field(default_factory=utc_now)
    confidence: float = 0.7  # How confident the agent is in this thought
    
    # Provenance tracking — enables full causal attribution of cognitive outcomes
    parent_thought_id: Optional[str] = None
    source_memory_ids: List[str] = Field(default_factory=list)  # Which memories informed this thought
    evidence_sources: List[str] = Field(default_factory=list)   # Tool calls, observations informing this
    
    class Config:
        json_schema_extra = {
            "example": {
                "kind": "internal_reasoning",
                "content": "The user wants to understand the current state of Alpha's workspace. "
                           "I should scan the directory structure and identify what systems are active.",
                "confidence": 0.92,
            }
        }


class Belief(BaseModel):
    """A confidence-weighted belief about reality, with evidence provenance.
    
    Unlike a simple fact, a Belief carries:
    - A confidence score (0.0 to 1.0) calibrated by evidence weight
    - Evidence sources that can be inspected and challenged
    - Epistemic metadata: how the belief was formed, when it last changed,
      what would cause it to be revised or discarded
    
    This is the Foundation Model's epistemic foundation — a world model
    where certainty is never absolute.
    """
    id: str = Field(default_factory=lambda: f"belief_{utc_now().strftime('%Y%m%d%H%M%S%f')}")
    content: str  # The proposition being believed (as natural language)
    
    # Epistemic strength
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence_weight: float = Field(default=0.0, ge=0.0, le=1.0)  # How strongly evidence supports this
    
    # Epistemic provenance — the 'how' and 'when' of belief formation
    formed_at: datetime = Field(default_factory=utc_now)
    last_updated: datetime = Field(default_factory=utc_now)
    source_bayes_factor: float = 1.0  # Bayesian update factor from new evidence
    
    # What would make me change my mind? (falsifiability criterion)
    falsifiers: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Alpha's foundation model runs locally on gemma-4-e4b-it-ultra at localhost:1234",
                "confidence": 0.98,
                "evidence_weight": 0.95,
                "source_bayes_factor": 12.0,
            }
        }


class Skill(BaseModel):
    """A learned capability that the agent can execute.
    
    Skills are not static — they evolve through practice and failure.
    This captures the 'I have learned how to do X' aspect of intelligence.
    """
    name: str = Field(..., description="Name of the skill (e.g., 'web_search', 'code_execution')")
    proficiency_level: float = Field(default=0.5, ge=0.0, le=1.0)  # 0.0 = novice, 1.0 = master
    
    # Skill metadata
    learned_at: datetime = Field(default_factory=utc_now)
    last_practiced: Optional[datetime] = None
    
    # Performance metrics from use
    total_invocations: int = 0
    success_rate: float = 0.0
    average_latency_ms: float = 0.0
    common_failures: List[str] = Field(default_factory=list)
    
    # The 'how' — encoded procedure or strategy for executing this skill
    execution_strategy: str = ""  # Natural language description of how the agent executes this
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "web_search",
                "proficiency_level": 0.85,
                "total_invocations": 42,
                "success_rate": 0.927,
                "execution_strategy": "1) Parse query for intent and entities. "
                                  "2) Choose appropriate search engine (duckduckgo for general, "
                                  "google for web pages). 3) Extract structured data using regex patterns. "
                                  "4) Validate extracted facts by cross-referencing multiple sources.",
            }
        }


class Goal(BaseModel):
    """An autonomous goal discovered or set by the agent.
    
    Goals are not assigned externally — they emerge through:
    - Environmental observation (what does this world need?)
    - Self-initiated curiosity (what do I want to know more about?)
    - User requests
    - Reflection on past failures ("I should never make this mistake again")
    """
    id: str = Field(default_factory=lambda: f"goal_{utc_now().strftime('%Y%m%d%H%M%S%f')}")
    title: str  # Short human-readable goal name
    description: str  # Full specification of what success looks like
    
    # Goal lifecycle
    created_at: datetime = Field(default_factory=utc_now)
    discovered_by: Optional[str] = None  # "internal_reasoning", "user_request", etc.
    
    status: GoalStatus = Field(default=GoalStatus.PENDING)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Map the project architecture",
                "description": "Explore the entire Alpha codebase and generate a comprehensive "
                              "document describing all modules, their responsibilities, and interconnections.",
                "status": "pending"
            }
        }


class GoalStatus(str, Enum):
    """Lifecycle stage of an autonomous goal."""
    DISCOVERED = "discovered"   # A meaningful goal has been identified but not yet pursued
    PENDING = "pending"         # Ready to be pursued; waiting for resources or conditions
    IN_PROGRESS = "in_progress" # Currently being worked on by the agent
    COMPLETED = "completed"     # Successfully achieved
    ABANDONED = "abandoned"     # No longer meaningful (superseded, impossible)


class Tool(BaseModel):
    """A capability the Foundation Model can invoke in the world.
    
    Tools are the agent's hands — its interface to reality through which
    it acts and gathers evidence about itself and its environment.
    """
    name: str = Field(..., description="Tool identifier (e.g., 'filesystem_scan', 'web_search')")
    display_name: str  # Human-readable name
    
    # Capabilities the tool provides
    capabilities: List[str] = Field(default_factory=list)
    
    # Parameters accepted by this tool
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Tool metadata for planning and selection
    requires_execution: bool = False  # Does this require actual code execution?
    rate_limit_requests_per_minute: int = 60
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "filesystem_scan",
                "display_name": "Explore Directory Structure",
                "capabilities": ["discovery", "navigation", "file_inspection"],
                "parameters": {"path": str, "depth_limit": int},
                "requires_execution": True,
            }
        }


class PlannerCapability(str, Enum):
    """Types of planning the agent can perform."""
    SEQUENTIAL = "sequential"           # A → B → C
    BRANCHING = "branching"             # A → {B, C} → D
    ITERATIVE = "iterative"             # For each item in collection: do X
    CONDITIONAL = "conditional"         # If condition met then Y else Z
    PARALLEL = "parallel"               # Do A and B simultaneously


class PlanningState(BaseModel):
    """The agent's current plan and its execution progress."""
    goal_id: str
    plan_steps: List[Dict[str, Any]]  # Ordered list of steps with their status
    current_step_index: int = -1
    state_history: List[Dict[str, Any]]  # For rollback and learning from past plans
    
    class Config:
        json_schema_extra = {
            "example": {
                "goal_id": "goal_abc123",
                "plan_steps": [
                    {"id": "step_1", "tool": "filesystem_scan", "path": ".", "status": "completed"},
                    {"id": "step_2", "tool": "read_file_lines", "path": "alpha/__init__.py", "status": "in_progress"}
                ],
                "current_step_index": 1,
            }
        }


class SelfModel(BaseModel):
    """The agent's self-model — what it knows about itself.
    
    This is the Foundation Model's introspection: its beliefs about its own
    capabilities, limitations, memories, and identity. It evolves as the agent
    learns what it can and cannot do.
    """
    # Core identity facts (static)
    name: str = "Alpha-Foundation-Model"
    version: str = "1.0.0"
    
    # Capabilities — which tools and cognitive abilities does this agent have?
    known_capabilities: List[str] = Field(default_factory=list)  # e.g., ["reasoning", "tool_use"]
    
    # Limitations — what does the agent know it cannot do?
    known_limitations: List[str] = Field(default_factory=list)   # Critical for safe operation
    
    # Self-beliefs
    self_beliefs: Dict[str, Belief] = Field(default_factory=dict)  # {"I am an AI": confidence}
    
    # Memory metadata
    total_memories_stored: int = 0
    longest_memory_span_days: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alpha-Foundation-Model",
                "version": "1.0.0",
                "known_capabilities": ["reasoning", "tool_use", "planning", "self_reflection"],
                "known_limitations": [
                    "Cannot modify my own source code directly (no write access to /alpha/foundation_model)",
                    "Reasoning is approximate and can contain errors",
                    "Memory retrieval may miss relevant memories"
                ],
            }
        }


class Planner(ABC):
    """Abstract interface for a planning strategy.
    
    Different planners use different heuristics for decomposing goals into actionable plans.
    The foundation model selects the best planner for each goal based on the task's characteristics.
    """
    
    @abstractmethod
    def plan(self, goal: Goal) -> PlanningState:
        """Decompose a high-level goal into executable steps."""
        pass


class ToolUseEngine(ABC):
    """Abstract interface for executing tools and interacting with the world."""
    
    @abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a single tool call with full error handling."""
        pass
    
    @abstractmethod
    def batch_execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple tools in parallel (where safe)."""
        pass


class MemoryProvider(ABC):
    """Abstract interface for persistent memory storage.
    
    The Foundation Model's long-term knowledge base — where lessons, skills, and world model
    beliefs are stored persistently across sessions.
    """
    
    @abstractmethod
    def store(self, record_type: str, content: Any) -> str:
        """Store a new memory or belief."""
        pass
    
    @abstractmethod
    def retrieve(self, query_embedding: List[float], limit: int = 10) -> List[Any]:
        """Retrieve most relevant memories for a given concept."""
        pass
    
    @abstractmethod
    def list_all(self, record_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all stored records of a given type."""
        pass


class ReasoningEngine(ABC):
    """Abstract interface for the cognitive reasoning engine.
    
    The Foundation Model's 'brain' — where thoughts are generated,
    plans are formulated, and beliefs are updated based on evidence.
    """
    
    @abstractmethod
    def reason(self, context: str) -> List[Thought]:
        """Generate a chain of thoughts in response to a stimulus."""
        pass
    
    @abstractmethod
    def update_belief(self, belief_id: str, new_evidence: Dict[str, Any]) -> Belief:
        """Bayesian belief updating with evidence accumulation."""
        pass


class GoalDiscoveryEngine(ABC):
    """Abstract interface for autonomous goal discovery.
    
    The engine that discovers what the agent should do next — not from user prompts,
    but from observing the world and identifying meaningful patterns or opportunities.
    """
    
    @abstractmethod
    def discover_goals(self) -> List[Goal]:
        """Scan the environment and identify interesting goals to pursue."""
        pass


class SelfImprovementLoop(ABC):
    """Abstract interface for continuous self-improvement.
    
    After each action, the agent reflects on what happened and encodes lessons
    into its long-term memory, improving future performance.
    """
    
    @abstractmethod
    def reflect(self, goal: Goal, outcome: Any, thoughts: List[Thought]) -> str:
        """Produce a reflective analysis of this completed action."""
        pass
    
    @abstractmethod
    def encode_lesson(self, lesson_text: str) -> None:
        """Encode a learned insight into persistent memory."""
        pass


class FoundationModelAgent(ABC):
    """Abstract interface for the complete Foundation Model Agent.
    
    This is the outermost interface — the agent as experienced by the world.
    It exposes a high-level `act()` method that encapsulates all cognition, planning,
    tool use, and self-improvement into one coherent loop.
    """
    
    @abstractmethod
    def act(self, context: Optional[str] = None) -> str:
        """The agent's primary interface.
        
        Given an optional context (user input, observation), the agent reasons, plans,
        acts through tools, and returns a response. The entire process is logged as
        thoughts for self-reflection and learning.
        """
        pass
    
    @abstractmethod
    def get_self_model(self) -> SelfModel:
        """Return the agent's current model of itself."""
        pass