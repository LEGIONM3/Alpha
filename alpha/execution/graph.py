"""Execution Graph: Directed Acyclic Graph (DAG) for orchestrating tool calls with dependencies and parallelism."""

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from alpha.tools.protocol import ToolResult

class NodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"

class ExecutionNode(BaseModel):
    """A discrete tool invocation node in the execution graph."""
    node_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    timeout_seconds: Optional[float] = None
    max_retries: int = 2
    retry_count: int = 0
    fallback_tool: Optional[str] = None
    fallback_arguments: Optional[Dict[str, Any]] = None
    is_critical: bool = True
    result: Optional[ToolResult] = None
    error_message: Optional[str] = None

class ExecutionGraph:
    """Directed Acyclic Graph governing workflow orchestration and dependency management."""

    def __init__(self, name: str = "ExecutionGraph"):
        self.name = name
        self.nodes: Dict[str, ExecutionNode] = {}
        self._adjacency: Dict[str, Set[str]] = {}  # node -> set of dependent nodes
        self._reverse_adjacency: Dict[str, Set[str]] = {}  # node -> set of prerequisite nodes

    def add_node(self, node: ExecutionNode) -> None:
        """Add a node to the execution graph."""
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node ID '{node.node_id}' in execution graph.")
        self.nodes[node.node_id] = node
        self._adjacency[node.node_id] = set()
        self._reverse_adjacency[node.node_id] = set()

        for dep in node.depends_on:
            self._reverse_adjacency[node.node_id].add(dep)

    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Add a directional dependency from from_node_id to to_node_id."""
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            raise KeyError(f"Both nodes must exist: '{from_node_id}' -> '{to_node_id}'")
        self._adjacency[from_node_id].add(to_node_id)
        self._reverse_adjacency[to_node_id].add(from_node_id)
        if from_node_id not in self.nodes[to_node_id].depends_on:
            self.nodes[to_node_id].depends_on.append(from_node_id)

    def validate_dag(self) -> None:
        """Verify that all dependencies exist and graph has no cycles."""
        for nid, node in self.nodes.items():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    raise ValueError(f"Node '{nid}' references non-existent dependency '{dep}'.")
                self._adjacency[dep].add(nid)
                self._reverse_adjacency[nid].add(dep)

        # Cycle detection using Kahn's algorithm
        in_degree = {nid: len(self._reverse_adjacency[nid]) for nid in self.nodes}
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in self._adjacency[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(self.nodes):
            raise ValueError("Execution graph contains cyclic dependencies. Must be a strict DAG.")

    def get_ready_nodes(self, completed_ids: Set[str], failed_ids: Set[str]) -> List[ExecutionNode]:
        """Return nodes whose dependencies are fully satisfied and ready to run."""
        ready: List[ExecutionNode] = []
        for nid, node in self.nodes.items():
            if node.status != NodeStatus.PENDING:
                continue

            # Check if any dependency failed
            failed_deps = [dep for dep in node.depends_on if dep in failed_ids]
            if failed_deps:
                node.status = NodeStatus.SKIPPED
                node.error_message = f"Prerequisite dependency failed: {failed_deps}"
                continue

            # Check if all dependencies are completed
            if all(dep in completed_ids for dep in node.depends_on):
                node.status = NodeStatus.READY
                ready.append(node)
        return ready

    def get_parallel_execution_layers(self) -> List[List[ExecutionNode]]:
        """Calculate parallel execution waves/layers via topological level ranking."""
        self.validate_dag()
        in_degree = {nid: len(self._reverse_adjacency[nid]) for nid in self.nodes}
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        layers: List[List[ExecutionNode]] = []

        while queue:
            current_layer = [self.nodes[nid] for nid in queue]
            layers.append(current_layer)
            next_queue = []
            for nid in queue:
                for neighbor in self._adjacency[nid]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            queue = next_queue
        return layers
