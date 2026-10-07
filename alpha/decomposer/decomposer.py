"""Task Decomposer: Breaks high-level goals into a hierarchical Task Tree with DAG dependencies."""

from typing import List, Optional, Dict, Any
from alpha.core.types import TaskLevel, TaskStatus, ComplexityScore
from alpha.decomposer.schemas import TaskNode, TaskTree

class TaskDecomposer:
    """Decomposes goals into Sub-Goals -> Tasks -> Atomic Actions with strict dependency tracking."""

    def __init__(self, max_depth: int = 3, max_retries: int = 3):
        self.max_depth = max_depth
        self.max_retries = max_retries

    def create_goal_tree(self, goal_description: str, goal_name: Optional[str] = None) -> TaskTree:
        """Initialize a new TaskTree with the root goal."""
        root_node = TaskNode(
            name=goal_name or "Root Goal",
            description=goal_description,
            level=TaskLevel.GOAL,
            complexity=ComplexityScore.EXTREME,
            status=TaskStatus.IN_PROGRESS
        )
        tree = TaskTree(root_goal_id=root_node.id)
        tree.add_node(root_node)
        return tree

    def decompose(
        self,
        goal_description: str,
        goal_name: Optional[str] = None,
        structured_steps: Optional[List[Dict[str, Any]]] = None
    ) -> TaskTree:
        """Decompose a high-level goal into a validated 4-level hierarchical DAG.
        
        If structured_steps is provided (e.g. from planner or LLM output), builds the exact tree.
        Otherwise, applies cognitive scaffolding decomposition patterns.
        """
        tree = self.create_goal_tree(goal_description, goal_name)
        root = tree.get_root()
        assert root is not None

        if structured_steps:
            self._build_from_structured_steps(tree, root.id, structured_steps)
        else:
            self._apply_heuristic_scaffolding_decomposition(tree, root)

        self._validate_and_finalize_tree(tree)
        return tree

    def _apply_heuristic_scaffolding_decomposition(self, tree: TaskTree, root: TaskNode) -> None:
        """Standard cognitive decomposition scaffold:
        Phase 1: Ingestion & Requirement Analysis (SubGoal 1)
        Phase 2: Execution & Synthesis (SubGoal 2)
        Phase 3: Verification & Polish (SubGoal 3)
        """
        # SubGoal 1: Analysis & Information Gathering
        sg1 = TaskNode(
            name=f"Analyze: {root.name}",
            description=f"Analyze requirements and gather relevant context for: {root.description}",
            level=TaskLevel.SUB_GOAL,
            parent_id=root.id,
            complexity=ComplexityScore.MEDIUM
        )
        tree.add_node(sg1)

        t1_1 = TaskNode(
            name="Inspect Constraints & Requirements",
            description="Extract specific constraints, invariants, and input parameters",
            level=TaskLevel.TASK,
            parent_id=sg1.id,
            complexity=ComplexityScore.LOW
        )
        tree.add_node(t1_1)

        a1_1_1 = TaskNode(
            name="Extract Parameters",
            description="Parse explicit inputs, format expectations, and target bounds",
            level=TaskLevel.ATOMIC_ACTION,
            parent_id=t1_1.id,
            complexity=ComplexityScore.LOW,
            expected_output_type="json_summary"
        )
        tree.add_node(a1_1_1)

        # SubGoal 2: Core Execution & Implementation
        sg2 = TaskNode(
            name=f"Execute: {root.name}",
            description=f"Execute core transformation and generation for: {root.description}",
            level=TaskLevel.SUB_GOAL,
            parent_id=root.id,
            complexity=ComplexityScore.HIGH
        )
        tree.add_node(sg2)

        t2_1 = TaskNode(
            name="Perform Core Work",
            description="Process inputs according to extracted requirements",
            level=TaskLevel.TASK,
            parent_id=sg2.id,
            complexity=ComplexityScore.MEDIUM
        )
        tree.add_node(t2_1)

        a2_1_1 = TaskNode(
            name="Generate Core Artifact",
            description="Produce draft solution or target payload",
            level=TaskLevel.ATOMIC_ACTION,
            parent_id=t2_1.id,
            dependencies=[a1_1_1.id],  # Depends on parameter extraction
            complexity=ComplexityScore.MEDIUM,
            expected_output_type="text_or_artifact"
        )
        tree.add_node(a2_1_1)

        # SubGoal 3: Verification & Reflection
        sg3 = TaskNode(
            name=f"Verify: {root.name}",
            description=f"Validate output against initial criteria and reflect",
            level=TaskLevel.SUB_GOAL,
            parent_id=root.id,
            complexity=ComplexityScore.LOW
        )
        tree.add_node(sg3)

        t3_1 = TaskNode(
            name="Review & Format",
            description="Verify consistency and apply final format check",
            level=TaskLevel.TASK,
            parent_id=sg3.id,
            complexity=ComplexityScore.LOW
        )
        tree.add_node(t3_1)

        a3_1_1 = TaskNode(
            name="Validate Constraints",
            description="Confirm output satisfies all extracted parameters and rubrics",
            level=TaskLevel.ATOMIC_ACTION,
            parent_id=t3_1.id,
            dependencies=[a2_1_1.id],  # Depends on core generation
            complexity=ComplexityScore.LOW,
            expected_output_type="validation_report"
        )
        tree.add_node(a3_1_1)

    def _build_from_structured_steps(self, tree: TaskTree, root_id: str, steps: List[Dict[str, Any]]) -> None:
        """Construct a TaskTree from an explicit list of sub-goals and actions."""
        last_action_id: Optional[str] = None
        for i, step_data in enumerate(steps):
            # Create sub-goal or task
            sub_goal = TaskNode(
                name=step_data.get("name", f"Step {i+1}"),
                description=step_data.get("description", ""),
                level=TaskLevel.SUB_GOAL,
                parent_id=root_id,
                complexity=step_data.get("complexity", ComplexityScore.LOW)
            )
            tree.add_node(sub_goal)

            actions = step_data.get("atomic_actions", [
                {"name": f"Execute {sub_goal.name}", "description": sub_goal.description}
            ])

            for act in actions:
                action_node = TaskNode(
                    name=act.get("name", "Action"),
                    description=act.get("description", ""),
                    level=TaskLevel.ATOMIC_ACTION,
                    parent_id=sub_goal.id,
                    complexity=act.get("complexity", ComplexityScore.LOW),
                    dependencies=act.get("dependencies", [last_action_id] if last_action_id else []),
                    expected_output_type=act.get("expected_output_type", "text"),
                    validation_rules=act.get("validation_rules", [])
                )
                tree.add_node(action_node)
                last_action_id = action_node.id

    def _validate_and_finalize_tree(self, tree: TaskTree) -> None:
        """Enforce architectural constraints:
        1. All atomic actions must have complexity <= 3 (low enough for weak models).
        2. Set initial statuses: actions with no dependencies become READY, others PENDING.
        """
        for node in tree.nodes.values():
            if node.is_atomic():
                if node.complexity > ComplexityScore.MEDIUM:
                    node.complexity = ComplexityScore.MEDIUM  # Clamp complexity for SLMs
                if not node.dependencies:
                    node.status = TaskStatus.READY
                else:
                    node.status = TaskStatus.PENDING

    def record_retry(self, node: TaskNode, error: str) -> bool:
        """Increment retry count and check if retrying is permitted."""
        node.retry_count += 1
        node.error = error
        if node.can_retry():
            node.status = TaskStatus.READY
            return True
        else:
            node.status = TaskStatus.FAILED
            return False
