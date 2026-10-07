"""Agentic Workflow Engine package for Alpha OS."""

from alpha.workflows.engine import WorkflowEngine, WorkflowExecutionResult
from alpha.workflows.templates import (
    build_research_workflow,
    build_coding_workflow,
    build_debug_workflow,
    build_analysis_workflow,
    build_validation_workflow
)

__all__ = [
    "WorkflowEngine",
    "WorkflowExecutionResult",
    "build_research_workflow",
    "build_coding_workflow",
    "build_debug_workflow",
    "build_analysis_workflow",
    "build_validation_workflow"
]
