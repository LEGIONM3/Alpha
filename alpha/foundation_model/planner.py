"""Planner Module — Decomposes goals into actionable execution plans.

The planner bridges the gap between abstract goals and concrete actions:
  "Write a test" → [create_test_file, write_code_block, run_tests]

It implements multiple planning strategies suited to different task types.

Author: Gemini (Alpha Principal Systems Engineer)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PlanStep(BaseModel):
    """A single step in an execution plan."""
    id: str = Field(default_factory=lambda: f"step_{len([t for t in globals().values() if hasattr(t, '_id')])}")
    
    description: str  # What this step accomplishes
    tool: Optional[str] = None  # Tool to use (if any)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    status: PlanStepStatus = "pending"  # pending | in_progress | completed | failed
    
    estimated_effort: str = ""  # e.g., "1 min", "5 minutes of thinking", etc.
    
    depends_on: List[str] = Field(default_factory=list)  # Step IDs this step requires first


class Plan(BaseModel):
    """A complete plan for achieving a goal."""
    goal_title: str
    created_at: datetime = Field(default_factory=utc_now)
    
    steps: List[PlanStep]
    
    # Execution state
    current_step_index: int = 0
    last_executed_step: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "goal_title": "Write a Python function to calculate Fibonacci",
                "steps": [
                    {"description": "Understand requirements: write fib(n) that returns nth fibonacci number"},
                    {"description": "Choose approach: recursive vs iterative vs memoized", "tool": None},
                    {"description": "Decompose into sub-tasks: define function signature, handle base cases...", "tool": None},
                    {"description": "Write the implementation", "tool": "execute_python"},
                    {"description": "Test with edge cases (0, 1, n=10)", "tool": "execute_python"}
                ]
            }
        }


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Planning Strategies
# Each strategy is a heuristic for decomposing goals into steps.
# The planner selects the most appropriate one based on task characteristics.
# =============================================================================

class SequentialDecompositionStrategy(BaseModel):
    """Break a goal into a linear sequence of steps.
    
    Best for: Tool-driven tasks, file operations, code execution sequences.
    Pattern: A → B → C → D → E
    """

    def plan(self, goal_title: str, context: Optional[str] = None) -> Plan:
        return Plan(
            goal_title=goal_title,
            steps=[
                PlanStep(description="Understand the task and identify constraints", tool=None),
                PlanStep(description="Break down into sub-components if applicable", tool=None),
                PlanStep(description=f"Analyze requirements for '{goal_title}'", tool="read_file_lines"),
                PlanStep(description="Determine what tools are needed", tool=None),
                PlanStep(description="Execute tool: scan filesystem for relevant context", tool="filesystem_scan"),
            ],
        )


class BranchingDecompositionStrategy(BaseModel):
    """Break a goal into branches based on conditions.
    
    Best for: Tasks where the path depends on discovered information,
             or tasks with multiple valid approaches to choose from.
    Pattern: A → {B if X else C} → D
    """

    def plan(self, goal_title: str, context: Optional[str] = None) -> Plan:
        return Plan(
            goal_title=goal_title,
            steps=[
                PlanStep(description="Gather information needed to choose a path", tool="filesystem_scan"),
                # Branch point — the next step depends on what we find
                PlanStep(
                    description="Evaluate available approaches and choose one based on constraints discovered",
                    depends_on=["step_1"],
                ),
            ],
        )


class IterativeDecompositionStrategy(BaseModel):
    """Break a goal into iterative steps (for loop pattern).
    
    Best for: Tasks that require processing multiple items,
             generating multiple outputs, or exhaustive searches.
    Pattern: For each item in collection: do X; combine results
    """

    def plan(self, goal_title: str, context: Optional[str] = None) -> Plan:
        return Plan(
            goal_title=goal_title,
            steps=[
                PlanStep(description="Identify the iteration target (files, lines, values)", tool=None),
                PlanStep(description="Define what operation to perform on each item", tool=None),
                PlanStep(description=f"Process first item in '{goal_title}'", tool=None),
                # ... iterative step would be templated here ...
            ],
        )


class CausalDecompositionStrategy(BaseModel):
    """Break a goal into cause-effect chains.
    
    Best for: Debugging, root-cause analysis, and tasks where understanding
             intermediate states is important to the outcome.
    Pattern: A causes B which enables C which produces D (goal)
    """

    def plan(self, goal_title: str, context: Optional[str] = None) -> Plan:
        return Plan(
            goal_title=goal_title,
            steps=[
                PlanStep(description="Identify the end state that represents success", tool=None),
                PlanStep(description="Work backwards: what immediately precedes this end state?", tool=None),
                PlanStep(description="Continue tracing back to identify root causes/actions", tool=None),
                PlanStep(description="Order steps so each provides evidence for the next", tool=None),
            ],
        )


# =============================================================================
# The Planner — Orchestrator of planning strategies
# =============================================================================

class Planner:
    """Decomposes high-level goals into executable plans.

    Selects the most appropriate strategy based on task characteristics,
    then generates a step-by-step plan with tool assignments and dependencies.
    
    Planning Pipeline:
        1. Receive goal + context
        2. Classify task type (tool-based? exploratory? generative?)
        3. Select strategy
        4. Generate draft plan
        5. Validate plan feasibility (does this actually achieve the goal?)
        6. Refine if needed
    
    """

    STRATEGY_REGISTRY = {
        "sequential": SequentialDecompositionStrategy,
        "branching": BranchingDecompositionStrategy,
        "iterative": IterativeDecompositionStrategy,
        "causal": CausalDecompositionStrategy,
    }

    def __init__(self):
        self._executed_steps: List[Dict] = []  # Track what we've done for learning

    def plan(self, goal_title: str, context: Optional[str] = None) -> Plan:
        """Generate a complete plan for achieving the given goal.
        
        Args:
            goal_title: The high-level goal to achieve
            context: Optional additional context (previous attempts, constraints, etc.)
            
        Returns:
            A Plan object with decomposed steps and tool assignments.
        """
        
        # Step 1: Classify the task type
        strategy = self._select_strategy(goal_title, context)
        
        # Step 2: Generate the plan using the selected strategy
        draft_plan = strategy.plan(goal_title=goal_title, context=context)
        
        # Step 3: Enrich with tool-specific details
        enriched_plan = self._enrich_with_tool_details(draft_plan)
        
        return enriched_plan

    def _select_strategy(self, goal_title: str, context: Optional[str] = None) -> 'Strategy':
        """Select the most appropriate planning strategy based on task characteristics."""
        
        keywords = (goal_title + " " + (context or "")).lower()
        
        # Rule-based strategy selection with fallback to sequential (default)
        if any(kw in keywords for kw in ["debug", "fix error", "investigate why", 
                                          "root cause", "why did"]):
            return CausalDecompositionStrategy()
        
        elif any(kw in keywords for kw in ["for each", "all files", "every file",
                                           "loop through", "process all"]):
            return IterativeDecompositionStrategy()
        
        elif any(kw in keywords for kw in ["choose", "select which", "determine best",
                                            "compare approaches"]):
            return BranchingDecompositionStrategy()

        # Default: sequential decomposition works for most tool-based tasks
        return SequentialDecompositionStrategy()

    def _enrich_with_tool_details(self, draft_plan: Plan) -> Plan:
        """Fill in tool assignments and parameter details for each step."""
        
        plan = draft_plan.model_copy()  # Deep copy to avoid mutating the strategy's plan
        
        tools_map = {
            "scan directory": "filesystem_scan",
            "list files/folders": "filesystem_scan", 
            "read a file": "read_file_lines",
            "write/create file": "file_create",
            "run code": "execute_python",
            "search web for info": "web_search",
        }

        for step in plan.steps:
            # Map the description to likely tools
            desc = step.description.lower()
            
            if any(kw in desc for kw in ["scan directory", "list files"]):
                step.tool = "filesystem_scan"
                step.parameters["path"] = "."
                step.estimated_effort = "< 1 sec"
            
            elif "read file" in desc:
                step.tool = "read_file_lines"
                # Extract path from context if available
                extracted_path = self._extract_parameter_from_text(step.description)
                step.parameters["path"] = extracted_path or "."
                step.estimated_effort = "< 1 sec"

            elif any(kw in desc for kw in ["write", "create file"]):
                step.tool = "file_create"
                step.parameters["content"] = "... (generated by agent)"
                step.estimated_effort = "1-2 minutes of thinking + < 1 sec write"

            elif "execute" in desc or "run code" in desc:
                step.tool = "execute_python"
                step.estimated_effort = "Varies with code complexity"

        return plan

    def _extract_parameter_from_text(self, text: str) -> Optional[str]:
        """Extract a file path from a natural language description."""
        keywords = ["alpha/foundation_model/", "./", ".\\", "/workspace/"]
        
        for kw in keywords:
            if kw in text:
                # Extract path after keyword
                rest = text[len(kw):].strip().rstrip(")")
                return rest.strip()

        return None

    def execute_plan(self, plan: Plan) -> Tuple[List[str], List[Any]]:
        """Execute a plan step by step, tracking outcomes.
        
        Returns:
            Tuple of (completed steps list, collected outputs list)
        """
        completed = []
        outputs = []

        for i, step in enumerate(plan.steps):
            print(f"  [{i+1}/{len(plan.steps)}] {step.description}")
            
            # Check dependencies
            if step.depends_on:
                deps_done = all(self._is_completed(s.id) for s in plan.steps 
                               if s.id in step.depends_on)
                if not deps_done:
                    print(f"    ⏭️  Skipping (waiting on {step.depends_on})")
                    continue
            
            # Simulate execution (in production, call ToolUseEngine here)
            result = self._simulate_step_execution(step)
            
            step.status = "completed" if result["success"] else "failed"
            completed.append(step.id)
            outputs.append(result.get("output"))

        return completed, outputs

    def _simulate_step_execution(self, step: PlanStep) -> Dict[str, Any]:
        """Simulate executing a plan step (returns mock data)."""
        
        # In production, this would call the ToolUseEngine
        tool = step.tool
        
        if tool == "filesystem_scan":
            return {
                "success": True,
                "output": f"Scanned directory. Found 15 items.",
                "tool_name": tool,
            }

        elif tool == "read_file_lines":
            path = step.parameters.get("path", ".")
            return {
                "success": True,
                "output": json.dumps({
                    "lines_read": 42,
                    "content_preview": f"# Read: {path}",
                }),
                "tool_name": tool,
            }

        elif tool == "file_create":
            return {
                "success": True,
                "output": f"File created successfully at path.",
                "tool_name": tool,
            }

        else:
            # For steps without tools (thinking/planning steps)
            return {"success": True, "output": step.description}

    def _is_completed(self, step_id: str) -> bool:
        """Check if a given step has been completed."""
        for s in self._executed_steps:
            if hasattr(s, 'id') and s.id == step_id and hasattr(s, 'status'):
                return s.status == "completed"
        return False


# =============================================================================
# Main Demo
# =============================================================================

if __name__ == "__main__":
    print("=== Planner Demo ===\n")

    planner = Planner()

    # Generate a plan for a complex goal
    goal = "Create a comprehensive documentation file for the Alpha project"
    
    print(f"\nGoal: {goal}")
    print("\n--- Generated Plan ---\n")

    plan = planner.plan(goal_title=goal)
    
    for i, step in enumerate(plan.steps, 1):
        status_mark = "→" if i < len(plan.steps)-1 else "↓"
        tool_info = f"[tool: {step.tool}]" if step.tool else ""
        
        print(f"{status_mark} Step {i}: {step.description}")
        if tool_info:
            print(f"         {tool_info} (effort: {step.estimated_effort})")

    # Execute the plan
    print("\n--- Executing Plan ---\n")
    completed, outputs = planner.execute_plan(plan)
    print(f"\nCompleted: {len(completed)} of {len(plan.steps)} steps")