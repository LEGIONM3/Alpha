"""Alpha Cognitive Scaffolding Engine: Orchestrates Memory, Decomposition, Planning, Reflection, Experience, and Knowledge."""

from typing import Optional, Dict, Any, List
from alpha.config import AlphaConfig, default_config
from alpha.core.types import TaskStatus, ComplexityScore
from alpha.core.model_adapter import BaseLanguageModel, MockWeakModel, ModelAdapter
from alpha.memory.manager import MemoryManager
from alpha.decomposer.decomposer import TaskDecomposer
from alpha.decomposer.schemas import TaskTree, TaskNode
from alpha.planner.planner import Planner
from alpha.planner.schemas import ExecutionPlan, ExecutionStep
from alpha.reflection.engine import ReflectionEngine
from alpha.reflection.schemas import ReflectionReport
from alpha.experience.logger import ExperienceLogger
from alpha.experience.schemas import ExperienceRecord
from alpha.knowledge.store import KnowledgeStore

class AlphaEngine:
    """Master Phase 1 Cognitive Scaffolding Layer for Alpha."""

    def __init__(
        self,
        config: Optional[AlphaConfig] = None,
        model: Optional[BaseLanguageModel] = None,
        db_path: Optional[str] = None
    ):
        self.config = config or default_config
        target_db = db_path or self.config.db_path

        # 1. Initialize Memory Manager
        self.memory = MemoryManager(db_path=target_db)

        # 2. Initialize Task Decomposer
        self.decomposer = TaskDecomposer(
            max_depth=self.config.max_decomposition_depth,
            max_retries=self.config.max_task_retries
        )

        # 3. Initialize Planner
        self.planner = Planner()

        # 4. Initialize Reflection Engine (wired with memory)
        self.reflection = ReflectionEngine(
            memory_manager=self.memory,
            quality_threshold=self.config.reflection_threshold
        )

        # 5. Initialize Experience Logger
        self.experience = ExperienceLogger(db_path=target_db)

        # 6. Initialize Knowledge Store
        self.knowledge = KnowledgeStore(db_path=target_db)

        # Initialize Model Adapter
        self.model = model or MockWeakModel()
        self.adapter = ModelAdapter(model=self.model)

    def execute_goal(
        self,
        goal: str,
        goal_name: Optional[str] = None,
        structured_steps: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Execute a complex goal end-to-end through the complete cognitive scaffolding pipeline."""
        
        # 1. Working Memory Setup
        self.memory.working_memory.clear()
        self.memory.working_memory.set_variable("current_goal", goal)

        # 2. Task Decomposition (Goal -> Sub-Goals -> Tasks -> Atomic Actions)
        task_tree: TaskTree = self.decomposer.decompose(
            goal_description=goal,
            goal_name=goal_name,
            structured_steps=structured_steps
        )

        # 3. Planning (Ordered Steps + Resource Budgets + Blockers + Validation Contracts)
        plan: ExecutionPlan = self.planner.create_plan_from_tree(task_tree)

        # Execution tracking state
        step_results: Dict[str, Any] = {}
        reports: List[ReflectionReport] = []
        overall_success = True

        # 4. Step-by-Step Execution Loop
        for step in plan.steps:
            node = task_tree.nodes.get(step.task_id)
            if not node:
                continue

            node.status = TaskStatus.IN_PROGRESS
            step_success = False
            corrective_feedback: Optional[str] = None

            # Retry loop for atomic step
            while not step_success and node.can_retry():
                # Context Assembly (Strict token budget)
                memory_ctx = self.memory.format_context_for_prompt(
                    task_description=step.name,
                    max_tokens=self.config.max_memory_retrieval_tokens
                )
                knowledge_ctx = self.knowledge.format_knowledge_for_prompt(
                    query_text=step.name,
                    max_tokens=self.config.max_knowledge_retrieval_tokens
                )

                # Execute through small model via ModelAdapter
                exec_result = self.adapter.execute_atomic_step(
                    task_id=step.task_id,
                    instruction=step.instruction,
                    memory_context=memory_ctx,
                    knowledge_context=knowledge_ctx,
                    corrective_feedback=corrective_feedback,
                    expected_format=node.expected_output_type
                )

                # 5. Reflection Engine Evaluation (What worked? What failed? What can improve?)
                report = self.reflection.reflect_on_step(
                    step=step,
                    result=exec_result,
                    raw_output=exec_result.raw_output
                )
                reports.append(report)

                # 6. Experience Log Record (Append-only audit trail with reward)
                reward = 1.0 if report.passed else -0.5
                record = ExperienceRecord(
                    task_id=step.task_id,
                    step_number=step.step_number,
                    goal_id=plan.goal_id,
                    decision_context={"instruction": step.instruction, "node_level": node.level.value},
                    action_taken=step.name,
                    model_output=exec_result.raw_output,
                    success=report.passed,
                    reward=reward,
                    latency_ms=exec_result.latency_ms,
                    tokens_used_est=exec_result.tokens_used_est,
                    reflection_report_id=report.report_id,
                    error_message="; ".join(report.what_failed) if not report.passed else None
                )
                if self.config.auto_record_experience:
                    self.experience.record(record)

                if report.passed:
                    step_success = True
                    node.status = TaskStatus.COMPLETED
                    node.result = exec_result.parsed_output or exec_result.raw_output
                    step_results[step.name] = node.result

                    # Update Working Memory and Long Term Completed Tasks
                    self.memory.working_memory.set_variable(step.name, str(node.result))
                    self.memory.store_completed_task(
                        task_id=step.task_id,
                        description=step.name,
                        result_summary=str(node.result)[:200],
                        latency_ms=exec_result.latency_ms
                    )
                else:
                    # Retry handling
                    node.retry_count += 1
                    corrective_feedback = report.corrective_prompt_injection

            if not step_success:
                node.status = TaskStatus.FAILED
                overall_success = False
                break

        # Final Goal Status
        root = task_tree.get_root()
        if root:
            root.status = TaskStatus.COMPLETED if overall_success else TaskStatus.FAILED

        return {
            "goal_id": plan.goal_id,
            "goal": goal,
            "success": overall_success,
            "total_steps": len(plan.steps),
            "completed_steps": sum(1 for n in task_tree.get_atomic_actions() if n.status == TaskStatus.COMPLETED),
            "results": step_results,
            "reflection_reports": [r.model_dump() for r in reports],
            "task_tree": task_tree.model_dump()
        }
