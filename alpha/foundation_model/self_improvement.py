"""Self-Improvement Loop — The Foundation Model learns from its own actions.

This module implements the agent's ability to reflect on past actions, extract
lessons, and permanently update its capabilities and knowledge base.

The self-improvement loop operates in a tight cycle:
    
    Action → Outcome → Reflection → Encoding → Next Iteration
    
    ┌──────────────┐      ┌──────────┐     ┌─────────┐    ┌───────────┐
    │   Take an    │→      │ Evaluate │→    │  Reflect│→   │   Encode  │
    │    Action    │      │ Result   │     │         │    │   Lesson  │
    └──────┬───────┘      └──────────┘     └────┬────┘    └─────▲─────┘
           │                                   │                │
           ▼                                   │                │
    ┌────────────────┐                     ┌───▼────────┐       │
    │  Update Skills │◄────────────────────│   New      │       │
    │   & Beliefs    │                     │ Knowledge   │       │
    └────────────────┘                     └─────────────┘       │
                                                                │
           ┌────────────────────────────────────────────────────┘
           │
           ▼ (Repeat with improved capabilities)
    
Core Principles:
1. Every action generates a lesson opportunity — nothing is wasted
2. Lessons are encoded as reusable knowledge, not just discarded notes
3. The agent tracks its own failure modes to avoid repeating them
4. Proficiency in skills increases through repeated successful use

Author: Gemini (Alpha Principal Systems Engineer)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from alpha.foundation_model.types import Thought, Belief, Skill


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ReflectionOutput(BaseModel):
    """Structured output of a reflection process.

    Contains both the explicit lesson learned and diagnostic information
    about what went well or poorly in the execution.
    """
    success: bool  # Did this action achieve its stated goal?
    
    # What worked well (to reinforce)
    strengths: List[str] = field(default_factory=list)
    
    # What failed or could be improved (to learn from)
    weaknesses: List[str] = field(default_factory=list)
    
    # The distilled lesson — an actionable principle for the future
    distilled_lesson: str = ""
    
    # How confident are we in this lesson? (0.0 to 1.0)
    confidence_in_lesson: float = 0.7
    
    # Which thought(s) led directly to a successful/unsuccessful outcome
    attribution_thought_ids: List[str] = field(default_factory=list)


class SelfImprovementLoop:
    """The agent's continuous learning mechanism.

    After every goal cycle completes (success or failure), the self-improvement
    loop:
    
    1. Evaluates the outcome against success criteria
    2. Reflects on which thoughts/actions led to success/failure
    3. Encodes lessons into persistent memory (Skills, Beliefs)
    4. Updates its self-model with new capabilities or limitations discovered
    
    This creates a compounding effect: each iteration is informed by all prior
    iterations' lessons.
    
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self._workspace_root = Path(workspace_root) if workspace_root else Path.cwd() / "alpha"
        
        # Persistent lesson storage
        self._lessons_path = self._workspace_root / "lessons.jsonl"
        
        # The agent's evolving model of its own capabilities
        self.self_model: Dict[str, Any] = {
            "known_capabilities": [],
            "known_limitations": ["Cannot directly modify source code files (read-only filesystem access)"],
            "tools_mastered": 0,
        }

    def reflect_on_goal_cycle(self, 
                              goal_title: str,
                              thoughts: List[Thought],
                              outcome_success: bool,
                              tool_results: Optional[List[Any]] = None,
                              unexpected_observation: Optional[str] = None) -> ReflectionOutput:
        """Reflect on a completed goal cycle and extract lessons.

        Args:
            goal_title: What the agent was trying to accomplish
            thoughts: The full chain of thoughts that led to the outcome
            outcome_success: Did the overall goal succeed?
            tool_results: Results from any tools executed during this cycle
            unexpected_observation: Anything surprising that happened
            
        Returns:
            A structured reflection containing lessons and diagnostics.
        """
        
        # Step 1: Evaluate — categorize what went well/poorly
        
        strengths = self._analyze_strengths(thoughts, outcome_success)
        weaknesses = self._analyze_weaknesses(
            thoughts, tool_results, unexpected_observation, outcome_success
        )
        
        # Step 2: Distill — extract an actionable principle
        distilled_lesson = self._distill_lesson(
            strengths=strengths, 
            weaknesses=weaknesses,
            success=outcome_success
        )
        
        # Step 3: Attribute — link the lesson to specific thoughts
        attribution_thought_ids = self._attribute_causality(thoughts, outcome_success)

        return ReflectionOutput(
            success=outcome_success,
            strengths=strengths,
            weaknesses=weaknesses,
            distilled_lesson=distilled_lesson,
            confidence_in_lesson=self._compute_confidence(
                thoughts, 
                len(strengths), 
                len(weaknesses)
            ),
            attribution_thought_ids=[t.id for t in attribution_thought_ids],
        )

    def _analyze_strengths(self, thoughts: List[Thought], success: bool) -> List[str]:
        """Identify which aspects of the reasoning/execution were effective."""
        strengths = []
        
        if success:
            # Success gives us positive reinforcement signals
            for thought in thoughts[-3:]:  # Look at the last few thoughts (decision points)
                if hasattr(thought, 'kind') and thought.kind.value == "tool_selection":
                    strengths.append(
                        f"Selected tool correctly in a successful execution."
                    )
                elif hasattr(thought, 'confidence'):
                    strengths.append(f"High-confidence decision ({thought.confidence:.1%}) was correct.")

        return strengths if strengths else ["No specific pattern identified — success may be due to luck or general competence."]

    def _analyze_weaknesses(self, 
                           thoughts: List[Thought], 
                           tool_results: Optional[List[Any]],
                           unexpected_observation: Optional[str],
                           success: bool) -> List[str]:
        """Identify failure modes and areas for improvement."""
        weaknesses = []
        
        # If failed, analyze what went wrong
        if not success and tool_results:
            error_thoughts = [t for t in thoughts 
                            if hasattr(t, 'kind') and t.kind.value == "execution"
                            and getattr(t, 'error_message', None)]
            
            for et in error_thoughts:
                weaknesses.append(f"Error in execution: {getattr(et, 'error_message', 'Unknown')}")

        # If there was an unexpected observation, that's a knowledge gap
        if unexpected_observation:
            weaknesses.append(
                f"Surprised by: '{unexpected_observation[:100]}...' "
                f"— indicates incomplete model of this domain."
            )

        return weaknesses

    def _distill_lesson(self, strengths: List[str], 
                       weaknesses: List[str], success: bool) -> str:
        """Create a concise, actionable principle from the reflection."""
        
        if success and len(weaknesses) == 0:
            # Reinforce successful patterns
            return (f"Successfully achieved goal. Pattern to reinforce: "
                    f"'{strengths[0]}'." if strengths else 
                   "Success achieved — no specific pattern identified.")

        if weaknesses:
            # Failure = opportunity for learning
            primary_weakness = weaknesses[0][:120] + "..." if len(weaknesses[0]) > 120 else weaknesses[0]
            
            return (f"Failed to achieve goal due to: '{primary_weakness}' "
                    f"Suggestion: {self._generate_fix_suggestion(primary_weakness)}.")

        # Success with some issues
        return (f"Goal achieved but with imperfections. "
                f"Impact of weaknesses: {'; '.join(weaknesses[:2])}. ")

    def _compute_confidence(self, thoughts: List[Thought], 
                           num_strengths: int, 
                           num_weaknesses: int) -> float:
        """How confident should we be in this lesson?"""
        
        # More evidence → higher confidence
        thought_count = len(thoughts)
        
        # Multiple independent successes increase confidence
        if success and num_strengths >= 2:
            base_confidence = 0.85
        
        # Failure with clear attribution also gives high confidence (we learned what NOT to do)
        elif num_weaknesses >= 1:
            base_confidence = 0.9

        else:
            # Ambiguous outcome → lower confidence lesson
            base_confidence = 0.6

        # Decay slightly with age of the lesson
        return min(0.95, max(0.3, base_confidence * 0.9))

    def _attribute_causality(self, thoughts: List[Thought], success: bool) -> List['Thought']:
        """Identify which specific thoughts caused the outcome."""
        
        # Look for the last tool-selection thought — that's often the decision point
        attribution = []
        reversed_thoughts = list(reversed(thoughts))
        
        for t in reversed_thoughts:
            if hasattr(t, 'kind') and t.kind.value == "tool_selection":
                attribution.append(t)
            elif hasattr(t, 'kind') and t.kind.value == "internal_reasoning":
                # This thought might have led to a poor decision
                attribution.append(t)

        return list(reversed(attribution))[:3]  # Top 3 causal thoughts

    def encode_lesson(self, lesson_text: str, 
                     skill_name: Optional[str] = None,
                     confidence: float = 0.8) -> bool:
        """Persist a lesson to the agent's long-term knowledge base."""
        
        try:
            # Append to persistent lessons file
            with open(self._lessons_path, "a") as f:
                entry = {
                    "timestamp": utc_now().isoformat(),
                    "lesson": lesson_text,
                    "skill_context": skill_name or "general",
                    "confidence": confidence,
                }
                f.write(json.dumps(entry) + "\n")

            print(f"\n  📝 Lesson encoded to persistence: {lesson_text[:80]}...")
            
            # Also update the self-model if this is a capability-related lesson
            if skill_name:
                current = set(self.self_model["known_capabilities"])
                new = set(current) | {skill_name}
                self.self_model["known_capabilities"] = list(new)
                self.self_model["tools_mastered"] += 1

            return True

        except Exception as e:
            print(f"  ⚠️  Failed to encode lesson (will be lost on session end): {e}")
            return False

    def load_prior_lessons(self) -> List[Dict]:
        """Load previously saved lessons from disk."""
        if not self._lessons_path.exists():
            return []

        lessons = []
        with open(self._lessons_path, "r") as f:
            for line in f:
                try:
                    lessons.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        # Sort by date (newest first)
        lessons.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return lessons

    def retrieve_lessons_about(self, topic: str, limit: int = 10) -> List[Dict]:
        """Find lessons relevant to a given topic."""
        all_lessons = self.load_prior_lessons()
        
        topic_keywords = set(topic.lower().split())
        scored = []
        
        for lesson in all_lessons:
            text_lower = (lesson.get("lesson", "") + " " + 
                         str(lesson.get("skill_context", ""))).lower()
            
            overlap = len(topic_keywords & set(text_lower.split()))
            score = overlap / max(len(topic_keywords), 1) * lesson.get("confidence", 0.5)
            
            if score > 0:
                scored.append((score, lesson))

        # Sort by relevance and confidence
        scored.sort(key=lambda x: -x[0])
        return [l for _, l in scored[:limit]]

    def get_self_model_summary(self) -> str:
        """Generate a human-readable summary of the agent's self-model."""
        
        capabilities_str = ", ".join(self.self_model["known_capabilities"][-5:]) if \
            len(self.self_model["known_capabilities"]) > 5 else " ".join(
                self.self_model["known_capabilities"]
            ) or "none identified yet"

        return (f"""Self-Model Summary
{'=' * 50}
Capabilities known: {capabilities_str}
Total tools mastered: {self.self_model['tools_mastered']}
Limitations acknowledged: {len(self.self_model['known_limitations'])}
  
Recent lessons stored: {(Path(self._lessons_path).read_text().count('\n') if 
                         (self._lessons_path.exists()) else 0)}```)

# =============================================================================
# Main Demo
# =============================================================================


if __name__ == "__main__":
    print("=== Self-Improvement Loop Demo ===\n")

    simulator = SelfImprovementLoop()

    # Simulate a goal cycle
    print("--- Goal: Explore the workspace ---")
    
    thoughts = [Thought(kind="internal_reasoning", content="I need to scan the filesystem"),
                Thought(kind="tool_selection", content="Use list_dir tool on current directory"),
                Thought(kind="execution", content="Executing: list_dir(.): SUCCESS - found 15 items")]

    outcome = simulator.reflect_on_goal_cycle(
        goal_title="Explore workspace structure",
        thoughts=thoughts,
        outcome_success=True,
        unexpected_observation=None,
    )

    print(f"Reflection complete:")
    print(f"  Success: {outcome.success}")
    print(f"  Strengths found: {len(outcome.strengths)}")
    print(f"  Weaknesses found: {len(outcome.weaknesses)}")
    print(f"\nDistilled Lesson:\n  '{outcome.distilled_lesson}'")
