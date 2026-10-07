"""Self-Observation: System Observer, Telemetry Snapshots, Bottleneck Detection, and Improvement Reports."""

import statistics
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.agents.core.runtime import AgentRuntime
from alpha.agents.core.base import AgentStatus

class TelemetrySnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_agents: int
    active_agents: int
    idle_agents: int
    suspended_agents: int
    retired_agents: int
    total_messages_exchanged: int
    total_tasks_completed: int
    total_tasks_failed: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    estimated_cost_units: float
    resource_utilization_pct: float
    timestamp: float = Field(default_factory=time.time)

class ImprovementReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    health_status: str  # "OPTIMAL", "CONGESTED", "DEGRADED"
    bottlenecks_detected: List[Dict[str, Any]]
    recommendations: List[str]
    snapshot: TelemetrySnapshot
    generated_at: float = Field(default_factory=time.time)

class SystemObserver:
    """Observes all agents, workflows, bottlenecks, latency percentiles, and costs."""

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.snapshots: List[TelemetrySnapshot] = []

    def capture_snapshot(self) -> TelemetrySnapshot:
        """Collect instantaneous state across all agents and communication channels."""
        agents = self.runtime.registry.get_all()
        total_agents = len(agents)
        active_agents = sum(1 for a in agents if a.status == AgentStatus.RUNNING)
        idle_agents = sum(1 for a in agents if a.status == AgentStatus.IDLE)
        suspended_agents = sum(1 for a in agents if a.status == AgentStatus.SUSPENDED)
        retired_agents = sum(1 for a in agents if a.status == AgentStatus.RETIRED)

        total_completed = sum(a.metrics.tasks_completed for a in agents)
        total_failed = sum(a.metrics.tasks_failed for a in agents)

        # Collect latency samples
        latencies = []
        for a in agents:
            if a.metrics.tasks_completed > 0:
                latencies.append(a.metrics.avg_latency_ms)

        if latencies:
            latencies.sort()
            avg_lat = round(statistics.mean(latencies), 2)
            n = len(latencies)
            p50 = round(latencies[int(n * 0.50)], 2)
            p95 = round(latencies[min(n - 1, int(n * 0.95))], 2)
            p99 = round(latencies[min(n - 1, int(n * 0.99))], 2)
        else:
            avg_lat = p50 = p95 = p99 = 0.0

        audit_log = self.runtime.bus.get_audit_trail()
        total_messages = len(audit_log)

        # Virtual compute unit estimation: based on message volume and task completions
        cost_units = round(total_completed * 1.5 + total_messages * 0.1, 2)
        utilization = round((active_agents / max(1, total_agents)) * 100.0, 1)

        snap = TelemetrySnapshot(
            total_agents=total_agents,
            active_agents=active_agents,
            idle_agents=idle_agents,
            suspended_agents=suspended_agents,
            retired_agents=retired_agents,
            total_messages_exchanged=total_messages,
            total_tasks_completed=total_completed,
            total_tasks_failed=total_failed,
            avg_latency_ms=avg_lat,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            estimated_cost_units=cost_units,
            resource_utilization_pct=utilization
        )
        self.snapshots.append(snap)
        return snap

    def generate_improvement_report(self) -> ImprovementReport:
        """Analyze current telemetry and generate actionable architectural recommendations."""
        snap = self.capture_snapshot()
        bottlenecks = []
        recommendations = []

        # Detect bottlenecks in agents
        agents = self.runtime.registry.get_all()
        for a in agents:
            unread = a.mailbox.peek_unread_count() if a.mailbox else 0
            if unread > 5:
                bottlenecks.append({
                    "agent_id": a.agent_id,
                    "agent_name": a.identity.name,
                    "issue": f"Mailbox backlog of {unread} unread messages",
                    "severity": "HIGH"
                })
                recommendations.append(f"Scale out additional worker agents for role '{a.role.value}' to alleviate queue backlog.")

            if a.metrics.avg_latency_ms > 500.0:
                bottlenecks.append({
                    "agent_id": a.agent_id,
                    "agent_name": a.identity.name,
                    "issue": f"High latency averaging {a.metrics.avg_latency_ms:.1f}ms",
                    "severity": "MEDIUM"
                })
                recommendations.append(f"Profile and apply OptimizationAgent caching to '{a.identity.name}'.")

        if snap.total_tasks_failed > 0:
            recommendations.append("Trigger MetaLearningFramework pattern analysis on observed task failures.")

        if not recommendations:
            recommendations.append("System is operating at optimal parameters. Maintain current scheduling quotas.")

        health = "OPTIMAL" if len(bottlenecks) == 0 else ("CONGESTED" if len(bottlenecks) < 3 else "DEGRADED")

        return ImprovementReport(
            health_status=health,
            bottlenecks_detected=bottlenecks,
            recommendations=recommendations,
            snapshot=snap
        )
