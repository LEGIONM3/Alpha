"""Schemas for Task Decomposer and Hierarchical Task Tree."""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from alpha.core.types import TaskLevel, TaskStatus, ComplexityScore, utc_now

class TaskNode(BaseModel):
    """A node in the hierarchical task decomposition tree / DAG."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str
    level: TaskLevel
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must complete before this starts")
    status: TaskStatus = TaskStatus.PENDING
    complexity: ComplexityScore = ComplexityScore.LOW
    retry_count: int = 0
    max_retries: int = 3
    expected_output_type: str = "text"
    validation_rules: List[str] = Field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None

    def is_atomic(self) -> bool:
        return self.level == TaskLevel.ATOMIC_ACTION

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

class TaskTree(BaseModel):
    """Container representing the complete hierarchical decomposition and DAG."""
    root_goal_id: str
    nodes: Dict[str, TaskNode] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    def get_root(self) -> Optional[TaskNode]:
        return self.nodes.get(self.root_goal_id)

    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.id] = node
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if node.id not in parent.children_ids:
                parent.children_ids.append(node.id)

    def get_children(self, node_id: str) -> List[TaskNode]:
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[child_id] for child_id in node.children_ids if child_id in self.nodes]

    def get_atomic_actions(self) -> List[TaskNode]:
        """Return all leaf/atomic actions in the tree."""
        return [n for n in self.nodes.values() if n.is_atomic()]

    def get_ready_tasks(self) -> List[TaskNode]:
        """Return atomic tasks whose dependencies have all completed successfully."""
        ready: List[TaskNode] = []
        for node in self.nodes.values():
            if not node.is_atomic():
                continue
            if node.status != TaskStatus.PENDING and node.status != TaskStatus.READY:
                continue
            # Check dependencies
            deps_satisfied = True
            for dep_id in node.dependencies:
                dep_node = self.nodes.get(dep_id)
                if not dep_node or dep_node.status != TaskStatus.COMPLETED:
                    deps_satisfied = False
                    break
            if deps_satisfied:
                node.status = TaskStatus.READY
                ready.append(node)
        return ready

    def topological_order(self) -> List[TaskNode]:
        """Return atomic action nodes in dependency-respecting execution order (Kahn's algorithm)."""
        atomic_nodes = {nid: n for nid, n in self.nodes.items() if n.is_atomic()}
        in_degree: Dict[str, int] = {nid: 0 for nid in atomic_nodes}
        adj: Dict[str, List[str]] = {nid: [] for nid in atomic_nodes}

        for nid, node in atomic_nodes.items():
            for dep in node.dependencies:
                if dep in atomic_nodes:
                    adj[dep].append(nid)
                    in_degree[nid] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: List[TaskNode] = []

        while queue:
            curr_id = queue.pop(0)
            order.append(atomic_nodes[curr_id])
            for neighbor in adj[curr_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) < len(atomic_nodes):
            # Circular dependency detected, fallback to arbitrary list
            remaining = [n for nid, n in atomic_nodes.items() if n not in order]
            order.extend(remaining)

        return order
