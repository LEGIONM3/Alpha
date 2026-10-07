"""Tool Reflection Engine: Analyzes tool correctness, necessity, efficiency, and alternative candidates."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from alpha.tools.protocol import ToolResult, ToolCapability
from alpha.tools.discovery import ToolCapabilityGraph
from alpha.memory.manager import MemoryManager
from alpha.memory.tool_memory import ToolMemoryStore

class ToolReflectionReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_name: str
    was_correct: bool
    was_necessary: bool
    was_efficient: bool
    better_alternative: Optional[str] = None
    overall_score: float
    distilled_lesson: str
    improvement_recommendation: Optional[str] = None

class ToolReflectionEngine:
    """Post-execution reflective engine that distills operational heuristics from tool interactions."""

    def __init__(
        self,
        capability_graph: Optional[ToolCapabilityGraph] = None,
        memory_manager: Optional[MemoryManager] = None,
        tool_memory: Optional[ToolMemoryStore] = None,
        latency_budget_ms: float = 10_000.0
    ):
        self.capability_graph = capability_graph
        self.memory_manager = memory_manager
        self.tool_memory = tool_memory
        self.latency_budget_ms = latency_budget_ms

    def reflect_on_tool_execution(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        result: ToolResult,
        task_intent: str = ""
    ) -> ToolReflectionReport:
        """Critique tool execution across correctness, necessity, efficiency, and alternatives."""
        # 1. Correctness
        was_correct = result.success and (result.error is None)
        if result.output is None:
            was_correct = False

        # 2. Necessity
        was_necessary = True
        # If input query was already directly present in memory, could have been avoided
        if self.memory_manager and "query" in inputs:
            q = str(inputs["query"])
            cached = self.memory_manager.retrieve(query_text=q, limit=1)
            if cached and cached[0].importance >= 0.8:
                was_necessary = False

        # 3. Efficiency
        was_efficient = result.latency_ms <= self.latency_budget_ms
        if len(str(result.output)) > 500_000:
            was_efficient = False

        # 4. Better Alternative Evaluation
        better_alternative = None
        if self.capability_graph and self.capability_graph.registry.has_tool(tool_name):
            current_tool = self.capability_graph.registry.get_tool(tool_name)
            curr_meta = current_tool.get_metadata()

            # Rule heuristic: If searching for code symbols using read_file
            if tool_name == "fs_read_file" and ("def " in str(inputs.get("file_path", "")) or "class" in task_intent):
                if self.capability_graph.registry.has_tool("fs_locate_symbols"):
                    better_alternative = "fs_locate_symbols"
            elif tool_name == "browser_navigate" and "search" in task_intent.lower():
                if self.capability_graph.registry.has_tool("browser_search"):
                    better_alternative = "browser_search"

        # 5. Distill Lesson Learned
        lesson = ""
        recommendation = None

        if not was_correct:
            lesson = f"When using '{tool_name}', verify input parameters and constraints to prevent: {result.error or 'unknown failure'}"
            recommendation = "Review input schema constraints and consider retry or fallback."
        elif not was_necessary:
            lesson = f"Check working memory before invoking '{tool_name}' to avoid redundant external calls."
            recommendation = "Query working memory or context prior to dispatching external tool."
        elif not was_efficient:
            lesson = f"Tool '{tool_name}' exceeded latency/size limits ({result.latency_ms:.0f}ms). Apply pagination or stricter filters."
            recommendation = "Enforce max_lines or tighter search constraints."
        elif better_alternative:
            lesson = f"Prefer '{better_alternative}' over '{tool_name}' for intent '{task_intent}' for higher precision."
            recommendation = f"Switch primary tool to '{better_alternative}' in future execution graphs."
        else:
            lesson = f"Tool '{tool_name}' executed cleanly and efficiently for intent '{task_intent}'."

        # Compute overall score
        score = 0.0
        if was_correct:
            score += 0.5
        if was_necessary:
            score += 0.25
        if was_efficient:
            score += 0.25
        if better_alternative:
            score = max(0.1, score - 0.2)

        report = ToolReflectionReport(
            tool_name=tool_name,
            was_correct=was_correct,
            was_necessary=was_necessary,
            was_efficient=was_efficient,
            better_alternative=better_alternative,
            overall_score=round(score, 3),
            distilled_lesson=lesson,
            improvement_recommendation=recommendation
        )

        # 6. Commit to Memory and Tool Store
        if self.tool_memory:
            self.tool_memory.record_interaction(
                tool_name=tool_name,
                inputs=inputs,
                result=result,
                success_score=report.overall_score,
                lesson_learned=report.distilled_lesson
            )

        return report
