"""Workflow Engine: Dispatches DAG workflows, integrates reflection and experience recording."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from alpha.execution.graph import ExecutionGraph
from alpha.execution.context import ExecutionContext
from alpha.execution.engine import ToolInvocationEngine, ExecutionGraphResult
from alpha.reflection.tool_reflection import ToolReflectionEngine, ToolReflectionReport
from alpha.tools.registry import ToolRegistry

class WorkflowExecutionResult(BaseModel):
    workflow_name: str
    success: bool
    graph_result: ExecutionGraphResult
    reflections: List[ToolReflectionReport] = Field(default_factory=list)
    knowledge_observations: List[str] = Field(default_factory=list) # New field for verified external observations
    transient_commentary: List[str] = Field(default_factory=list) # Renamed/repurposed lessons

class WorkflowEngine:
    """Orchestrates high-level agentic workflows with automatic execution and reflection loops."""

    def __init__(
        self,
        invocation_engine: ToolInvocationEngine,
        reflection_engine: Optional[ToolReflectionEngine] = None
    ):
        self.invocation_engine = invocation_engine
        self.reflection_engine = reflection_engine

    def execute_workflow(
        self,
        graph: ExecutionGraph,
        context: Optional[ExecutionContext] = None
    ) -> WorkflowExecutionResult:
        ctx = context or ExecutionContext()
        graph_result = self.invocation_engine.execute_graph(graph, ctx)

        reflections: List[ToolReflectionReport] = []
        lessons: List[str] = []

        if self.reflection_engine:
            for nid, node in graph.nodes.items():
                if node.result:
                    report = self.reflection_engine.reflect_on_tool_execution(
                        tool_name=node.tool_name,
                        inputs=node.arguments,
                        result=node.result,
                        task_intent=graph.name
                    )
                    reflections.append(report)
                    if report.distilled_lesson:
                        # Initially route all distilled lessons to transient commentary (Phase 2 requirement)
                        transient_commentary.append(report.distilled_lesson)

        return WorkflowExecutionResult(
            workflow_name=graph.name,
            success=graph_result.success,
            graph_result=graph_result,
            reflections=reflections,
            knowledge_observations=[], # Start empty; observations must be explicitly derived later
            transient_commentary=transient_commentary
        )
