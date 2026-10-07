"""The Reasoning Engine — Foundation Model's cognitive core.

This module implements the agent's reasoning capabilities:
- Thought generation (internal monologue)
- Planning and task decomposition
- Belief updating via Bayesian inference
- Strategic tool selection

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    REASONING ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │  Belief State    │◄───────►│  Evidence Processor │     │
│  │  (confidence)      │          │  (calibration)       │     │
│  └──────────────────┘         └──────────────────────┘     │
│           ▲                            │                     │
│           │            ┌───────────────▼───────────────┐    │
│           │            │   Uncertainty Manager         │    │
│           ▼            │   (When to ask? When to know?)│    │
│  ┌──────────────────┐  │                             │     │
│  │  Strategy       │◄──┴─────► ┌──────────────────┐ │     │
│  │  Selector       │           │   Reasoning      │ │     │
│  │                 │           │   Style Engine    │ │     │
│  └──────────────────┘           │ (deep, shallow,   │ │     │
│                                 │  system-2, etc.)  │ │     │
│           ▲                            ▼                     │
│           │              ┌─────────────▼─────────────┐       │
│           └──────────────►│   Tool Selector          │       │
│                           │   (which tool for this?)  │       │
└─────────────────────────────────────────────────────────────┘

Core Principles:
1. Every thought has provenance — trace what informed it
2. Confidence is always explicit and calibratable
3. The agent knows when it doesn't know (calibrated uncertainty)
4. Beliefs decay over time without reinforcement

Author: Gemini (Alpha Principal Systems Engineer)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from alpha.foundation_model.types import (
    Thought, ThoughtKind, Belief, Skill, Goal, PlannerCapability, PlanningState
)
from alpha.foundation_model.memory_manager import MemoryManager


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UncertaintyManager(BaseModel):
    """Manages when to seek information vs. when to act with existing knowledge.

    Implements a formal uncertainty model that answers:
    - "How confident am I about this conclusion?"
    - "What additional evidence would change my mind?"
    - "When should I delegate to external tools for verification?"
    
    Uses Bayesian updating principles and calibrated confidence bounds.
    """

    current_beliefs: Dict[str, Belief] = Field(default_factory=dict)
    minimum_confidence_threshold: float = 0.7
    information_gain_threshold: float = 0.15
    
    def register_belief(self, belief: Belief) -> None:
        self.current_beliefs[belief.id] = belief

    def get_uncertainty(self, belief_id: str) -> float:
        """Return uncertainty (1 - confidence) for a given belief."""
        if belief_id not in self.current_beliefs:
            return 0.5  # Unformed beliefs are maximally uncertain
        
        b = self.current_beliefs[belief_id]
        # Uncertainty is the complement of confidence, bounded at 0.5
        return max(0.0, min(1.0 - b.confidence, 1.0))

    def should_query(self, uncertainty: float) -> bool:
        """Should we seek more information before acting?"""
        return uncertainty > self.minimum_confidence_threshold

    def compute_information_gain(self, new_evidence_strength: float) -> float:
        """Estimate how much a potential evidence source would shift confidence."""
        # Rough Bayesian update approximation
        current_uncertainty = 1.0 - sum(v.confidence for v in self.current_beliefs.values()) / max(len(self.current_beliefs), 1)
        
        if new_evidence_strength < 0.3:
            return 0.05 * new_evidence_strength
        elif new_evidence_strength < 0.6:
            return 0.1 + 0.2 * (new_evidence_strength - 0.3)
        else:
            return min(0.4, 0.1 + new_evidence_strength * 0.5)


class ReasoningStyle(BaseModel):
    """Defines how the agent should reason about a given task."""

    name: str = "balanced"
    
    # How many intermediate steps to show in reasoning
    depth: int = 3
    
    # Confidence threshold before acting (higher = more conservative)
    action_confidence_threshold: float = 0.7
    
    # Whether to use chain-of-thought style explicit reasoning
    use_explicit_reasoning: bool = True


class ReasoningEngine:
    """The agent's cognitive core — generates thoughts, plans actions, updates beliefs.

    The engine maintains a belief state over the world and uses this to guide
    reasoning and action selection. It is explicitly uncertain about what it knows
    and seeks additional evidence when necessary.

    The architecture follows a cyclic pattern:
    
        Observe → Recall Relevant Memory → Reason (generate thoughts) 
              ↓                            │
              ▼                           ┌─┘
         Update Beliefs ←──────────────────│
              ↑                            │
              └──── Action taken ◄──────────┘
    """

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory = memory_manager or MemoryManager()
        
        # Core belief state — what the agent "knows" about reality
        self.beliefs: Dict[str, Belief] = {}
        
        # Uncertainty management
        self.uncertainty_manager = UncertaintyManager()

        # Current reasoning style configuration
        self._current_style: Optional[ReasoningStyle] = None
        
        # Tool selection state (which tools have been tried)
        self._tried_tools_in_session: set = set()

    def reason_about(self, stimulus: str, context: Optional[str] = None) -> List[Thought]:
        """Generate a chain of thoughts in response to a stimulus.
        
        This is the primary cognitive function — given input (user prompt,
        observation, goal), produce a sequence of internal thoughts that
        lead to an action or decision.

        The reasoning process:
        1. Recall relevant memories from long-term storage
        2. Update beliefs based on new information
        3. Generate intermediate reasoning steps
        4. Select a tool/action if confidence is sufficient
        
        Args:
            stimulus: The input the agent is responding to
            context: Optional additional context (previous thoughts, goal state)
            
        Returns:
            A list of Thoughts representing the cognitive process, ordered chronologically.
        """
        from alpha.foundation_model.tool_use_engine import ToolUseEngine
        
        thoughts = []
        
        # Step 1: Contextual awareness — what do I already know?
        relevant_memories = self.memory.retrieve(stimulus, limit=3)
        
        thought_awareness = Thought(
            kind=ThoughtKind.MEMORY_RECALL,
            content=f"Recall: Found {len(relevant_memories)} relevant memories. "
                    f"Key insights: {', '.join([m.summary or m.content[:50] for m in relevant_memories]) if relevant_memories else 'No prior knowledge.'}",
            source_memory_ids=[r.id for r in relevant_memories],
        )
        thoughts.append(thought_awareness)
        
        # Step 2: Update beliefs based on new evidence
        updated_beliefs = self._update_belief_from_stimulus(stimulus, relevant_memories)
        if any(b.confidence > 0.9 for b in updated_beliefs):
            thought_belief_update = Thought(
                kind=ThoughtKind.BELIEF_UPDATE,
                content=f"Belief strengthened: {[b.content[:80] for b in updated_beliefs]}"[0],
            )
            thoughts.append(thought_belief_update)
        
        # Step 3: Select reasoning strategy based on task complexity
        if self._current_style is None:
            style = self._select_reasoning_style(stimulus, relevant_memories)
            self._current_style = style
        
        thought_strategy = Thought(
            kind=ThoughtKind.INTERNAL_REASONING,
            content=f"Selecting reasoning strategy: {style.name}. "
                    f"(Depth={style.depth}, confidence_threshold={style.action_confidence_threshold})",
        )
        thoughts.append(thought_strategy)
        
        # Step 4: Generate intermediate reasoning steps
        if self._current_style.use_explicit_reasoning:
            reason_steps = self._generate_intermediate_reasoning(stimulus, style=style)
            thoughts.extend(reason_steps)
        
        # Step 5: Check uncertainty and decide on tool use or action
        uncertainty_decision = self._evaluate_uncertainty(thoughts, stimulus)
        thought_uncertainty = Thought(
            kind=ThoughtKind.INTERNAL_REASONING,
            content=uncertainty_decision.reasoning,
            confidence=1.0 - uncertainty_decision.uncertainty,
        )
        thoughts.append(thought_uncertainty)
        
        # Step 6: Tool selection if applicable
        tool_choice = self._select_tool_for_task(stimulus)
        thought_tool = Thought(
            kind=ThoughtKind.TOOL_SELECTION,
            content=f"Selected tool(s): {tool_choice.tool_names}",
            confidence=1.0 - uncertainty_decision.uncertainty,
        )
        thoughts.append(thought_tool)
        
        return thoughts

    def _update_belief_from_stimulus(self, stimulus: str, memories: List[Any]) -> List[Belief]:
        """Update belief state based on new stimulus and retrieved memories."""
        updated = []
        
        # Check if existing beliefs are supported or contradicted by new info
        for memory in memories:
            content = memory.content.lower()
            
            # Update confidence of relevant beliefs
            for belief_id, belief in list(self.beliefs.items()):
                if "memory" not in str(belief):  # Skip self-referential updates
                    # Simple relevance check — in production use embeddings
                    relevance = sum(1 for word in content.split() if word in stimulus.lower().split())
                    
                    if relevance >= 2:
                        # Bayesian-like update: evidence supports this belief
                        new_confidence = min(0.95, belief.confidence + 0.1 * relevance)
                        
                        # Create updated belief record
                        old_belief = Belief.model_validate(belief.model_dump(mode="json"))
                        new_belief = Belief.model_validate({**old_belief.model_dump(mode="json"),
                                                               "confidence": new_confidence,
                                                               "last_updated": utc_now()})
                        
                        self.beliefs[belief_id] = new_belief
                        updated.append(new_belief)
        
        return updated

    def _select_reasoning_style(self, stimulus: str, memories: List[Any]) -> ReasoningStyle:
        """Select an appropriate reasoning style for the task."""
        keywords = stimulus.lower()
        
        if any(kw in keywords for kw in ["prove", "verify", "check", "validate", "confirm"]):
            return ReasoningStyle(name="rigorous_verification")
        
        if any(kw in keywords for kw in ["plan", "schedule", "organize", "break down"]):
            return ReasoningStyle(name="structured_planning")
        
        if any(kw in keywords for kw in ["find", "search", "explore", "discover"]):
            return ReasoningStyle(name="exploratory_breadth_first")
        
        if any(kw in keywords for kw in ["why", "cause", "reason", "explain why"]):
            return ReasoningStyle(name="causal_explanation")
        
        if any(kw in keywords for kw in ["list", "enumerate", "show all"]):
            return ReasoningStyle(name="exhaustive_enumeration")
        
        return ReasoningStyle(name="balanced")

    def _generate_intermediate_reasoning(self, stimulus: str, style: ReasoningStyle) -> List[Thought]:
        """Generate intermediate reasoning steps (the agent's 'internal monologue')."""
        thoughts = []
        
        # Break down the problem into components
        thought_decomposition = Thought(
            kind=ThoughtKind.INTERNAL_REASONING,
            content=f"Breaking down '{stimulus}' into components: "
                    f"(1) Understand constraints, (2) Identify resources available, "
                    f"(3) Evaluate tradeoffs.",
            confidence=0.85,
        )
        thoughts.append(thought_decomposition)
        
        # Consider multiple hypotheses if applicable
        thought_alternatives = Thought(
            kind=ThoughtKind.INTERNAL_REASONING,
            content="Considering alternative approaches: "
                    f"Approach A (direct), Approach B (via intermediate step)",
            confidence=0.6,  # Lower confidence — these are just being considered
        )
        thoughts.append(thought_alternatives)
        
        return thoughts

    def _evaluate_uncertainty(self, all_thoughts: List[Thought], stimulus: str) -> Tuple[float, str]:
        """Evaluate uncertainty about the next action and decide whether to act or gather more info."""
        # Calculate overall confidence from thought chain
        avg_confidence = sum(t.confidence for t in all_thoughts if hasattr(t, 'confidence')) / max(len(all_thoughts), 1)
        
        uncertainty = 1.0 - avg_confidence
        
        if uncertainty < self.uncertainty_manager.minimum_confidence_threshold:
            reasoning = f"Confidence high ({avg_confidence:.2f}) — proceeding with action."
        elif uncertainty < 0.85:
            reasoning = f"Moderate uncertainty ({avg_confidence:.2f}) — using conservative strategy, " \
                       f"may verify via tool call after initial attempt."
        else:
            reasoning = f"Low confidence ({avg_confidence:.2f}) — should gather more information before acting. " \
                        f"Suggesting knowledge-seeking action."
        
        return UncertaintyManagerUpdate(uncertainty=uncertainty, reasoning=reasoning)

    def _select_tool_for_task(self, stimulus: str) -> ToolSelectionResult:
        """Select which tool(s) to use given a task description."""
        keywords = stimulus.lower()
        
        # Map task descriptions to tools (simplified mapping — in production this is learned)
        if any(kw in keywords for kw in ["list", "directory", "folder", "file"]):
            return ToolSelectionResult(
                tool_names=["filesystem_scan"],
                parameters={"path": ".", "depth_limit": 5},
            )
        
        if any(kw in keywords for kw in ["read", "content", "text"]):
            return ToolSelectionResult(
                tool_names=["read_file_lines"],
                parameters={"path": "..."},
            )
        
        if any(kw in keywords for kw in ["search", "find information", "research"]):
            return ToolSelectionResult(
                tool_names=["web_search"],
                parameters={"query": stimulus},
            )
        
        # Default: no tool needed, respond with internal knowledge
        return ToolSelectionResult(
            tool_names=[],
            reasoning="Task can be handled without external tools.",
        )

    def update_planning_state(self, goal_id: str, current_step_index: int) -> None:
        """Update the planner's tracking of which step we're on."""
        pass  # Would integrate with Planner class in full implementation


class ToolSelectionResult(BaseModel):
    """Output of tool selection decision."""
    tool_names: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""


class UncertaintyManagerUpdate(BaseModel):
    """Result from uncertainty evaluation."""
    uncertainty: float
    reasoning: str


if __name__ == "__main__":
    # Demo of the reasoning engine in action
    mem_mgr = MemoryManager()
    reasoner = ReasoningEngine(memory_manager=mem_mgr)
    
    stimulus = "Explore the Alpha project directory and generate a summary"
    
    thoughts = reasoner.reason_about(stimulus, context="Initial task from user")
    
    print("=== REASONING TRACE ===\n")
    for i, thought in enumerate(thoughts, 1):
        confidence_str = f"[{thought.confidence:.2f}]" if hasattr(thought, 'confidence') else ""
        source = f" ← {thought.source_memory_ids}" if thought.source_memory_ids else ""
        
        print(f"{i:2}. [{thought.kind.value:25s}] {confidence_str}{source}")
        print(f"    └─ {thought.content[:100]}{'...' if len(thought.content) > 100 else ''}\n")