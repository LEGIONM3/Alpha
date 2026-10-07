"""Foundation Model Agent — The complete autonomous AGI agent.

This is Project Alpha's Foundation Model: a single, self-contained cognitive agent
that integrates reasoning, planning, tool use, memory, goals, and self-improvement
into one coherent system.

Architecture Overview:
┌───────────────────────────────────────────────────────────────────┐
│              FOUNDATION MODEL AGENT                                │
│  (The unified cognitive engine — "the brain" of Alpha)            │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │   PERCEPTION LAYER                                          │ │
│  │   ┌──────────────┐     ┌──────────────┐                    │ │
│  │   │ Perception   │────►│ Memory Mgr   │                    │ │
│  │   │ Bus (events) │     │ (recall)     │                    │ │
│  │   └──────────────┘     └──────────────┘                    │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │   COGNITION CORE                                           │ │
│  │   ┌──────────────┐    ┌──────────────┐                     │ │
│  │   │ Reasoning    │◄──►│ World Model  │                     │ │
│  │   │ Engine       │    │ (beliefs)     │                     │ │
│  │   └──────────────┘    └──────────────┘                     │ │
│  │        ▲                    ▼                               │ │
│  │        │              ┌──────────────┐                      │ │
│  │        └─────────────►│ Goal Discovery│                      │ │
│  │                        Engine         │                      │ │
│  │                                   ┌──▼──┐                   │ │
│  │                           ┌───────┘      │                      │
│  │   ┌───────────────────────┤Self-Improv. │                      │
│  │   │     Planner           │ Loop        │                      │
│  │   └───────────────────────┴─────────────┘                      │ │
│  └─────────────────────────────┬────────────────────────────────┘ │
│                                ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │      ACTION & EXECUTION LAYER                               │ │
│  │   ┌──────────┐    ┌──────────────┐     ┌──────────────┐   │ │
│  │   │ Tool Use │◄───►│  Self-Improv │◄───►│   Planner   │   │ │
│  │   │ Engine   │    │    Loop      │     │  (decomposition)││ │
│  │   └──────────┘    └──────────────┘     └──────────────┘   │ │
│  └─────────────────────────────┬───────────────────────────────┘ │
│                                ▼                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           PERSISTENT STORAGE LAYER                          │ │
│  │   • Knowledge Store    • Lessons Journal    • Goals State   │ │
│  │   • Self-Model         • World Model        • Skills DB     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                     │
└───────────────────────────────────────────────────────────────────┘

Core Principles:
1. The agent thinks in thoughts — each with provenance and confidence
2. It maintains an explicit world model that evolves through observation
3. It discovers goals autonomously, not just responds to prompts
4. Every action is a learning opportunity — lessons are encoded permanently
5. It knows what it doesn't know (calibrated uncertainty)

Usage:
    from alpha.foundation_model import FoundationModelAgent
    
    agent = FoundationModelAgent(
        workspace_root=Path("./alpha"),
        model_url="http://localhost:1234/v1",
        default_model="gemma-4-e4b-it-ultra-uncensored-heretic"
    )
    
    # The agent runs autonomously
    agent.start()

Author: Gemini (Alpha Principal Systems Engineer)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from alpha.foundation_model.types import Goal, ThoughtKind, Belief, Skill
from alpha.foundation_model.reasoning_engine import ReasoningEngine
from alpha.foundation_model.planner import Planner, PlanStepStatus
from alpha.foundation_model.tool_use_engine import ToolUseEngine
from alpha.foundation_model.self_improvement import SelfImprovementLoop
from alpha.foundation_model.goal_discovery import GoalDiscoveryEngine
from alpha.foundation_model.world_model import WorldModel
from alpha.foundation_model.memory_manager import MemoryManager


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# The Foundation Model Agent — Unified Cognitive Engine
# =============================================================================

class FoundationModelAgent:
    """The complete autonomous AGI agent.
    
    This class integrates all cognitive submodules into a single agent that:
    - Perceives its environment through observations
    - Reasons about what it perceives using a world model
    - Discovers meaningful goals autonomously
    - Plans how to achieve those goals
    - Executes actions through tool use
    - Reflects on outcomes and encodes lessons
    - Continuously improves itself
    
    The agent operates as an autonomous loop:
    
        Observe → Recall Memory → Reason → Plan → Act → Observe → Learn...
    
    It is designed to run for extended periods, persisting its knowledge
    across sessions and growing wiser with time.

    Args:
        workspace_root: Base path where the agent stores its persistent data.
        model_url: URL of the foundation model inference endpoint (for external reasoning).
        default_model: The primary LLM model to use for complex reasoning.
        thought_interval_seconds: How often the agent performs an autonomous reasoning cycle.
        enable_external_model: Whether to call an external model for heavy lifting.
    """

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        model_url: str = "http://localhost:1234/v1",
        default_model: str = "gemma-4-e4b-it-ultra-uncensored-heretic",
        thought_interval_seconds: float = 6.0,
        enable_external_model: bool = True,
    ):
        
        # Core configuration
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd() / "alpha"
        self.model_url = model_url.rstrip("/")
        self.default_model = default_model
        self.thought_interval = thought_interval_seconds

        # Persistent storage paths
        self._self_model_path = self.workspace_root / "foundation_model" / "self_model.json"
        self._goals_path = self.workspace_root / "foundation_model" / "active_goals.jsonl"

        # ─── CORE MODULES ───────────────────────────────────────────────

        # Memory: the agent's long-term knowledge and episodic experience
        self.memory_manager = MemoryManager(workspace_root=self.workspace_root)

        # World Model: how the agent understands reality (entities, relationships, causality)
        self.world_model = WorldModel(workspace_root=self.workspace_root)

        # Reasoning Engine: generates thoughts and updates beliefs
        self.reasoning_engine = ReasoningEngine(memory_manager=self.memory_manager)

        # Tool Use Engine: interface to the external world via tools
        self.tool_engine = ToolUseEngine()

        # Planner: decomposes goals into executable steps
        self.planner = Planner()

        # Self-Improvement Loop: encodes lessons from experience
        self.self_improvement = SelfImprovementLoop(workspace_root=self.workspace_root)

        # Goal Discovery Engine: finds meaningful things to do
        self.goal_discovery = GoalDiscoveryEngine(
            workspace_root=self.workspace_root,
            memory_manager=self.memory_manager,
        )

        # External model client (for heavy reasoning when enabled)
        self._external_model_client: Optional[Any] = None
        if enable_external_model:
            try:
                from alpha.model_intelligence.connector.client import OpenAICompatibleClient
                self._external_model_client = OpenAICompatibleClient(
                    base_url=self.model_url,
                    default_model=default_model,
                    timeout_seconds=40.0,
                    enable_mock_fallback=False,
                )
            except ImportError:
                print("[FoundationModelAgent] External model not available. Running in local mode.")

        # ─── STATE ──────────────────────────────────────────────────────

        self._current_goal: Optional[Goal] = None
        self._active_plan: Optional[Plan] = None  # type: ignore
        self._running: bool = False
        
        # The agent's view of itself (what it knows about its own capabilities)
        self.self_model: Dict[str, Any] = {
            "name": "Alpha-Foundation-Model",
            "version": "1.0.0",
            "capabilities": [
                "reasoning",      # Can reason through problems step by step
                "tool_use",       # Can execute tools in the environment
                "planning",       # Can decompose goals into steps
                "memory",         # Can retrieve relevant past experiences
                "self_reflection" # Can reflect on its own performance
            ],
            "limitations": [
                "Cannot directly modify source code files (read-only filesystem access)",
                "Reasoning is approximate and can contain errors",
                f"No direct network access beyond {self.model_url} endpoint",
            ],
            "tools_mastered_count": 0,
        }

        # Load prior knowledge from persistence
        self._load_prior_knowledge()

    def _load_prior_knowledge(self) -> None:
        """Load the agent's persistent state from disk."""
        
        # Load world model entities
        wm_path = self.workspace_root / "world_model_state.json"
        if wm_path.exists():
            try:
                with open(wm_path, "r") as f:
                    data = json.load(f)
                    for entity_data in data.get("entities", []):
                        from alpha.foundation_model.world_model import Entity
                        self.world_model.entities[entity_data["id"]] = Entity.model_validate(entity_data)
            except (json.JSONDecodeError, KeyError):
                pass

        # Load active goals
        with open(self._goals_path, "r") as f:
            for line in f:
                try:
                    goal_data = json.loads(line.strip())
                    from alpha.foundation_model.types import GoalStatus
                    goal = Goal(
                        id=goal_data.get("id", ""),
                        title=goal_data["title"],
                        description=goal_data["description"],
                        status=GoalStatus(goal_data["status"]),
                        created_at=datetime.fromisoformat(goal_data["created_at"]),
                    )
                except (json.JSONDecodeError, KeyError):
                    continue

    def save_state(self) -> None:
        """Save the agent's current state to disk."""
        
        # Save world model
        entities_data = [{"id": e.id, "name": e.name, "type": e.type, 
                         "description": e.description} for e in self.world_model.entities.values()]
        
        wm_path = self.workspace_root / "world_model_state.json"
        with open(wm_path, "w") as f:
            json.dump({"entities": entities_data}, f)

    # ─── AUTONOMOUS OPERATION ──────────────────────────────────────────

    def start(self) -> None:
        """Start the agent's autonomous reasoning loop.
        
        The agent enters a continuous cycle of:
        1. Checking for active goals
        2. Reasoning about what to do next
        3. Executing tools/plan steps
        4. Reflecting on outcomes and learning
        """
        self._running = True
        
        print("\n" + "=" * 60)
        print("  🚀 ALPHA FOUNDATION MODEL AGENT — Starting Autonomous Mode")
        print("=" * 60)
        print(f"\n  Model endpoint: {self.model_url}")
        print(f"  Workspace:      {self.workspace_root}")
        print(f"  Thought cycle:  every {self.thought_interval}s")
        print("-" * 60)

        self._main_loop()

    def stop(self) -> None:
        """Stop the autonomous reasoning loop."""
        self._running = False
        print("\n  ⏸️  Agent paused.")

    def _main_loop(self) -> None:
        """The main autonomous reasoning cycle.
        
        Each iteration:
        1. Check if there's an active goal and progress on it
        2. If no goal, discover new goals to pursue
        3. Reason about the next action using memory and world model
        4. Execute through tool use or internal reasoning
        5. Reflect and encode lessons
        """
        
        while self._running:
            try:
                # Step 1: Handle current goal execution
                if self._current_goal is not None:
                    result = self._execute_current_goal_cycle()

                    if result["completed"]:
                        print(f"\n  ✅ Goal completed: {self._current_goal.title}")
                        self.goal_discovery.mark_completed(self._current_goal.id)
                        
                        # Move to next goal
                        new_goals = [g for g in self.goal_discovery.discover_all() 
                                    if g.status != GoalStatus.COMPLETED]
                        if not new_goals:
                            print("  → No more pending goals. Waiting for input...")
                            time.sleep(self.thought_interval)
                            continue
                        
                        # Pick the highest-priority goal
                        self._current_goal = max(new_goals, key=lambda g: g.id)  # Simplified priority
                        self._start_new_plan()

                    else:
                        print(f"\n  🔁 Continuing with: {self._current_goal.title}")
                
                elif not any(g.status == GoalStatus.PENDING for g in 
                            [g for g in self.goal_discovery.discover_all()]):
                    # No active or pending goals — idle state
                    print("\n  💤 Agent is idle. Waiting for input...")
                    time.sleep(self.thought_interval)

            except KeyboardInterrupt:
                print("\n  ⚠️  Interrupted by user.")
                break
            except Exception as e:
                print(f"\n  ❌ Error in main loop: {e}")
                self.reasoning_engine._uncertainty_manager.register_belief(
                    Belief(id="loop_error", content=f"Main loop error: {str(e)}")
                )

    def _execute_current_goal_cycle(self) -> Dict[str, Any]:
        """Execute one cycle of working toward the current goal."""
        
        if self._current_goal is None:
            return {"completed": False}

        # Get the plan for this goal
        plan = self.planner.plan(goal_title=self._current_goal.title)
        self._active_plan = plan

        # Execute plan step by step
        completed_steps, outputs = self.planner.execute_plan(plan)

        # Step 2: Reflect on what happened
        outcome = {
            "success": True if completed_steps else False,
            "thoughts": [],  # Would collect from reasoning here in full implementation
            "tool_results": outputs,
        }

        reflection = self.self_improvement.reflect_on_goal_cycle(
            goal_title=self._current_goal.title,
            thoughts=[],  # Full thought chain would be captured
            outcome_success=completed_steps == plan.steps if plan else False,
            tool_results=outputs,
            unexpected_observation=None,
        )

        # Step 3: Encode lessons
        if reflection.distilled_lesson:
            self.self_improvement.encode_lesson(
                lesson_text=reflection.distilled_lesson,
                confidence=reflection.confidence_in_lesson,
            )

        return {"completed": len(completed_steps) == len(plan.steps) if plan else False}

    def _start_new_plan(self) -> None:
        """Set up a new goal with its initial plan."""
        
        # Set the goal as active
        self._current_goal = Goal(
            id="active_goal",  # In production, use unique ID
            title=self._current_goal.title if self._current_goal else "Exploring workspace",
            description=self._current_goal.description if self._current_goal else 
                       "Discover and execute meaningful goals autonomously.",
            status=GoalStatus.IN_PROGRESS,
        )

        # Generate the plan for this goal
        self._active_plan = self.planner.plan(goal_title=self._current_goal.title)
        
        print(f"\n  📋 Starting new goal: {self._current_goal.title}")
        print(f"  └─ Plan has {len(self._active_plan.steps)} steps")

    def _on_observation(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Handle incoming perception events from the Perception Bus."""
        
        # Update world model with new observations
        if "content" in payload:
            self.world_model.observe(observation=payload["content"])

    def respond_to_user(self, user_input: str) -> str:
        """Respond to a direct user prompt.

        This is how the agent responds when explicitly prompted,
        as opposed to autonomous goal-driven behavior.
        """
        
        print(f"\n  👤 User: {user_input}")
        
        # Step 1: Recall relevant memories
        memories = self.memory_manager.retrieve(user_input)
        
        # Step 2: Reason about the response
        thoughts = self.reasoning_engine.reason_about(stimulus=user_input, context="User prompt")

        # Step 3: If external model available and task is complex, use it
        response_content = ""
        if self._external_model_client and self.reasoning_engine._current_style:
            style = self.reasoning_engine._current_style
            reasoning_steps = "\n".join([t.content for t in thoughts if hasattr(t, 'content')])
            
            system_prompt = f"""You are the Foundation Model Agent from Project Alpha.
        
        Context provided by the agent's memory:
        {memories[0].summary[:500] if memories else "No relevant memories available."}

        Reasoning chain (the agent's internal monologue):
        {reasoning_steps[:1000]}

        Respond directly to the user's question or request.
        
        User input: {user_input}"""

            # Use external model for response generation
            from alpha.model_intelligence.connector.client import OpenAICompatibleClient
            
            response = self._external_model_client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are Alpha-Foundation-Model, a highly capable autonomous reasoning agent. Be helpful, precise, and thoughtful in your responses."},
                    {"role": "user", "content": system_prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            
            response_content = response.choices[0].message.content

        else:
            # Fallback: use the agent's internal reasoning to generate a response
            from alpha.foundation_model.tool_use_engine import ToolUseEngine
            tool_engine = ToolUseEngine()
            
            thought_chain = " ".join([t.content for t in thoughts])
            response_content = f"Based on my analysis:\n\n{thought_chain}\n\n---\nProposed action: Execute the following reasoning steps to address your query."

        # Step 4: Log this as a memory (episodic experience)
        self.memory_manager.store(content=f"Responded to user input about '{user_input[:50]}...' with response covering {len(thoughts)} thoughts of reasoning.", 
                                  layer="experience")

        return response_content


# =============================================================================
# Main Entry Point & Demo
# =============================================================================

def main():
    """Demonstrate the Foundation Model Agent in action."""
    
    print("\n" + "=" * 70)
    print("  🧠 PROJECT ALPHA: FOUNDATION MODEL AGIT")
    print("=" * 70)
    print()

    # Initialize the agent
    agent = FoundationModelAgent(
        workspace_root=Path.cwd(),
        model_url="http://localhost:1234/v1",
        default_model="gemma-4-e4b-it-ultra-uncensored-heretic",
        thought_interval_seconds=5.0,
        enable_external_model=False,  # Set True if localhost:1234 is running
    )

    # Show the agent's self-model (what it knows about itself)
    print("\n📋 Agent Self-Model:")
    print("-" * 60)
    for k, v in agent.self_model.items():
        if isinstance(v, list):
            print(f"  {k}:")
            for item in v[-3:]:  # Last 3 items of each list
                print(f"    • {item}")
        else:
            print(f"  {k}: {v}")

    print("\n🧭 Memory State:")
    print("-" * 60)
    mem_summary = agent.memory_manager.summarize_state()
    for line in mem_summary.split('\n'):
        print(f"  {line}")

    # Run a quick demonstration
    print("\n🎯 Autonomous Goal Discovery Demo:")
    print("-" * 60)
    
    goals = agent.goal_discovery.discover_all()[:3]
    for g in goals:
        print(f"\n  📌 {g.status.value}: {g.title}")
        print(f"     └─ {g.description[:80]}...")

    # Demo a user interaction
    print("\n\n💬 User Prompt Demo:")
    print("-" * 60)
    
    response = agent.respond_to_user("What do you know about yourself and your capabilities?")
    print(f"\n  🤖 Agent:\n{response}")

    # Show what tools are available
    print("\n\n🛠️  Available Tools:")
    print("-" * 60)
    for tool in agent.tool_engine.registry.list_tools():
        print(f"  • {tool.display_name}: {tool.description[:70]}...")

    # Show the self-improvement loop's lessons
    print("\n\n📚 Lessons Learned (from reflection):")
    print("-" * 60)
    all_lessons = agent.self_improvement.load_prior_lessons()
    for lesson in all_lessons[:3]:
        if "lesson" in lesson:
            print(f"\n  🧠 {lesson['confidence']:.1%} confidence:")
            print(f"     └─ {lesson.get('lesson', 'N/A')}")

    # Save state
    agent.save_state()
    print("\n\n💾 State saved to workspace.")


if __name__ == "__main__":
    main()