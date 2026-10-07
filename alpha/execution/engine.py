"""Tool Invocation Engine: Orchestrates ExecutionGraph traversal, parallel execution, timeout handling, and rollback dispatch."""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from alpha.tools.protocol import ToolResult
from alpha.tools.registry import ToolRegistry
from alpha.execution.context import ExecutionContext
from alpha.execution.graph import ExecutionGraph, ExecutionNode, NodeStatus
from alpha.execution.recovery import (
    RecoverySystem,
    FailureDetector,
    RecoveryStrategy,
    FailureMode
)

logger = logging.getLogger(__name__)

class ExecutionGraphResult(BaseModel):
    graph_name: str
    success: bool
    total_nodes: int
    completed_nodes: int
    failed_nodes: int
    skipped_nodes: int
    node_results: Dict[str, Any] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    rollbacks_triggered: List[Dict[str, Any]] = Field(default_factory=list)

class ToolInvocationEngine:
    """Executes execution graphs with parallel worker threads, dependency propagation, and recovery."""

    def __init__(
        self,
        registry: ToolRegistry,
        recovery_system: Optional[RecoverySystem] = None,
        max_workers: int = 4
    ):
        self.registry = registry
        self.recovery = recovery_system or RecoverySystem(registry)
        self.max_workers = max_workers

    def execute_node(
        self,
        node: ExecutionNode,
        context: ExecutionContext
    ) -> ToolResult:
        """Execute a single graph node, with automatic parameter interpolation and recovery."""
        node.status = NodeStatus.RUNNING

        tool_to_run = node.tool_name
        current_args = context.interpolate(node.arguments)

        while node.retry_count <= node.max_retries:
            res = self.registry.execute_tool(
                tool_name=tool_to_run,
                arguments=current_args,
                timeout_seconds=node.timeout_seconds,
                call_id=f"{node.node_id}_try{node.retry_count+1}"
            )

            # Validate through registry contract
            val_report = self.registry.validate_tool_result(tool_to_run, res)
            if not val_report.valid:
                res.success = False
                res.error = f"Validation Rejected: {'; '.join(val_report.errors)}"

            if res.success:
                node.status = NodeStatus.COMPLETED
                node.result = res
                context.register_step_result(node.node_id, res)
                return res

            # Failure occurred: Diagnose and attempt recovery
            node.retry_count += 1
            diagnosis = FailureDetector.diagnose(res)
            logger.warning(
                f"Node '{node.node_id}' failed using tool '{tool_to_run}' (Attempt {node.retry_count}/{node.max_retries+1}). "
                f"Diagnosis: {diagnosis.failure_mode.value}. Cause: {diagnosis.root_cause}"
            )

            if node.retry_count > node.max_retries:
                # Exhausted standard retries: Check for fallback tool
                fallback = node.fallback_tool or self.recovery.get_fallback_tool(tool_to_run)
                if fallback and fallback != tool_to_run:
                    logger.info(f"Node '{node.node_id}' substituting fallback tool '{fallback}' for '{tool_to_run}'.")
                    tool_to_run = fallback
                    node.retry_count = 0  # Reset retry budget for fallback tool
                    node.fallback_tool = None  # Prevent infinite loop
                    current_args = context.interpolate(node.fallback_arguments or node.arguments)
                    continue

                # Final failure
                node.status = NodeStatus.FAILED
                node.result = res
                node.error_message = res.error
                return res

            # Exponential backoff delay
            backoff_delay = self.recovery.calculate_backoff(node.retry_count)
            time.sleep(backoff_delay)

            # Adjust parameters if suggested by diagnosis
            if diagnosis.failure_mode == FailureMode.TIMEOUT:
                node.timeout_seconds = (node.timeout_seconds or 30.0) * 1.5

        node.status = NodeStatus.FAILED
        node.result = res
        return res

    def execute_graph(
        self,
        graph: ExecutionGraph,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraphResult:
        """Execute an entire ExecutionGraph respecting dependencies and exploiting parallelism."""
        start_time = time.perf_counter()
        ctx = context or ExecutionContext()
        graph.validate_dag()

        completed_ids: Set[str] = set()
        failed_ids: Set[str] = set()
        node_results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}
        rollbacks: List[Dict[str, Any]] = []

        overall_success = True

        with ThreadPoolExecutor(max_workers=self.max_workers) as thread_pool:
            while len(completed_ids) + len(failed_ids) < len(graph.nodes):
                ready_nodes = graph.get_ready_nodes(completed_ids, failed_ids)

                if not ready_nodes:
                    # Check if pending nodes are blocked by skipped/failed nodes
                    pending_unresolved = [
                        nid for nid, n in graph.nodes.items()
                        if n.status in (NodeStatus.PENDING, NodeStatus.READY)
                    ]
                    if pending_unresolved:
                        for nid in pending_unresolved:
                            node = graph.nodes[nid]
                            if node.status == NodeStatus.PENDING:
                                node.status = NodeStatus.SKIPPED
                                failed_ids.add(nid)
                    break

                # Submit ready nodes in parallel
                future_to_node = {
                    thread_pool.submit(self.execute_node, node, ctx): node
                    for node in ready_nodes
                }

                for future in as_completed(future_to_node):
                    node = future_to_node[future]
                    try:
                        res: ToolResult = future.result()
                        if res.success:
                            completed_ids.add(node.node_id)
                            node_results[node.node_id] = res.output
                        else:
                            failed_ids.add(node.node_id)
                            errors[node.node_id] = res.error or "Unknown failure"
                            if node.is_critical:
                                overall_success = False
                    except Exception as exc:
                        failed_ids.add(node.node_id)
                        errors[node.node_id] = str(exc)
                        if node.is_critical:
                            overall_success = False

                if not overall_success:
                    # Critical failure encountered, trigger rollbacks
                    logger.warning("Critical node failure encountered. Initiating rollback stack.")
                    rollbacks = ctx.execute_rollbacks()
                    break

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ExecutionGraphResult(
            graph_name=graph.name,
            success=overall_success and len(failed_ids) == 0,
            total_nodes=len(graph.nodes),
            completed_nodes=len(completed_ids),
            failed_nodes=len(failed_ids),
            skipped_nodes=sum(1 for n in graph.nodes.values() if n.status == NodeStatus.SKIPPED),
            node_results=node_results,
            errors=errors,
            execution_time_ms=elapsed_ms,
            rollbacks_triggered=rollbacks
        )
