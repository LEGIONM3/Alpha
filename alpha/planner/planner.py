"""Planner component: Generates validated execution plans from Goal and Task Trees."""

from typing import List, Optional
from alpha.core.types import ComplexityScore, ValidationType
from alpha.decomposer.schemas import TaskTree, TaskNode
from alpha.planner.schemas import ExecutionPlan, ExecutionStep, ResourceEstimate, ValidationContract

class Planner:
    """Transforms decomposed TaskTrees into sequential ExecutionPlans with resource budgeting."""

    def create_plan_from_tree(self, tree: TaskTree) -> ExecutionPlan:
        """Create a sequentially ordered ExecutionPlan respecting DAG dependencies."""
        root = tree.get_root()
        goal_id = root.id if root else tree.root_goal_id
        goal_desc = root.description if root else "Goal"

        plan = ExecutionPlan(
            goal_id=goal_id,
            goal_description=goal_desc
        )

        # Get atomic tasks sorted by topological order
        ordered_nodes = tree.topological_order()

        for idx, node in enumerate(ordered_nodes, start=1):
            step = self._build_step_from_node(idx, node, tree)
            plan.steps.append(step)

        plan.calculate_totals()
        return plan

    def _build_step_from_node(self, step_number: int, node: TaskNode, tree: TaskTree) -> ExecutionStep:
        """Synthesize an ExecutionStep with resource estimates, blockers, and validation contracts."""
        complexity = node.complexity
        resources = self._estimate_resources(complexity)
        blockers = self._identify_blockers(node, tree)
        contracts = self._derive_validation_contracts(node)
        fallback = f"If step {step_number} fails, re-query memory for fallback heuristics or ask for clarification."

        return ExecutionStep(
            step_number=step_number,
            task_id=node.id,
            name=node.name,
            instruction=f"Action: {node.name}\nContext: {node.description}\nTarget Output Type: {node.expected_output_type}",
            complexity=complexity,
            resources=resources,
            blockers=blockers,
            validation_contracts=contracts,
            fallback_strategy=fallback
        )

    def _estimate_resources(self, complexity: ComplexityScore) -> ResourceEstimate:
        """Estimate token limits and timeout based on complexity."""
        if complexity == ComplexityScore.TRIVIAL:
            return ResourceEstimate(
                estimated_input_tokens=150,
                estimated_output_tokens=80,
                timeout_seconds=15.0
            )
        elif complexity == ComplexityScore.LOW:
            return ResourceEstimate(
                estimated_input_tokens=300,
                estimated_output_tokens=180,
                timeout_seconds=30.0
            )
        elif complexity == ComplexityScore.MEDIUM:
            return ResourceEstimate(
                estimated_input_tokens=500,
                estimated_output_tokens=300,
                timeout_seconds=45.0
            )
        else:
            return ResourceEstimate(
                estimated_input_tokens=800,
                estimated_output_tokens=450,
                timeout_seconds=60.0
            )

    def _identify_blockers(self, node: TaskNode, tree: TaskTree) -> List[str]:
        """Identify what preceding tasks must finish or data artifacts must be ready."""
        blockers: List[str] = []
        for dep_id in node.dependencies:
            dep_node = tree.nodes.get(dep_id)
            if dep_node:
                blockers.append(f"Requires completion of Task '{dep_node.name}' (ID: {dep_id})")
            else:
                blockers.append(f"Requires external dependency ID: {dep_id}")
        return blockers

    def _derive_validation_contracts(self, node: TaskNode) -> List[ValidationContract]:
        """Attach deterministic validation contracts to prevent low-reasoning errors."""
        contracts: List[ValidationContract] = []

        # 1. Output non-empty assertion
        contracts.append(ValidationContract(
            validation_type=ValidationType.DETERMINISTIC_ASSERTION,
            rule="len(output.strip()) > 0",
            description="Output must not be empty or blank whitespace"
        ))

        # 2. Type-specific contracts
        if "json" in node.expected_output_type.lower():
            contracts.append(ValidationContract(
                validation_type=ValidationType.SCHEMA_MATCH,
                rule="valid_json_object",
                description="Output must parse as a valid JSON document"
            ))
        elif "report" in node.expected_output_type.lower() or "validation" in node.expected_output_type.lower():
            contracts.append(ValidationContract(
                validation_type=ValidationType.KEYWORD_PRESENCE,
                rule="status,result",
                description="Output must contain status/result indicators"
            ))
        else:
            contracts.append(ValidationContract(
                validation_type=ValidationType.REGEX_PATTERN,
                rule=r"\S+",
                description="Output must contain readable characters"
            ))

        return contracts
