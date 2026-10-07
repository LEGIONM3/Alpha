"""Performance Analytics: Tracks success rate, tool usage, latency percentiles, retries, and historical trends."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from alpha.tools.protocol import utc_now

class ToolExecutionMetric(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_name: str
    success: bool
    latency_ms: float
    retries: int = 0
    reward: float = 1.0
    error_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)

class PerformanceAnalytics:
    """Computes operational performance KPIs and tracks historical reliability metrics."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_analytics_events (
                    id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    retries INTEGER NOT NULL,
                    reward REAL NOT NULL,
                    error_type TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_analytic_tool ON tool_analytics_events(tool_name)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_analytic_ts ON tool_analytics_events(timestamp)")

    def record_event(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float,
        retries: int = 0,
        reward: float = 1.0,
        error_type: Optional[str] = None
    ) -> ToolExecutionMetric:
        metric = ToolExecutionMetric(
            tool_name=tool_name,
            success=success,
            latency_ms=latency_ms,
            retries=retries,
            reward=reward,
            error_type=error_type
        )
        with self._conn:
            self._conn.execute("""
                INSERT INTO tool_analytics_events (
                    id, tool_name, success, latency_ms, retries, reward, error_type, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.id,
                metric.tool_name,
                1 if metric.success else 0,
                metric.latency_ms,
                metric.retries,
                metric.reward,
                metric.error_type,
                metric.timestamp.isoformat()
            ))
        return metric

    def get_tool_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Compute aggregate metrics for a single tool or across all tools."""
        with self._conn:
            if tool_name:
                cur = self._conn.execute(
                    "SELECT * FROM tool_analytics_events WHERE tool_name = ?", (tool_name,)
                )
            else:
                cur = self._conn.execute("SELECT * FROM tool_analytics_events")
            rows = cur.fetchall()

        if not rows:
            return {
                "total_invocations": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_retries": 0.0,
                "avg_reward": 0.0
            }

        total = len(rows)
        successes = sum(1 for r in rows if r["success"] == 1)
        latencies = sorted([float(r["latency_ms"]) for r in rows])
        retries = sum(int(r["retries"]) for r in rows)
        rewards = sum(float(r["reward"]) for r in rows)

        p50 = latencies[int(total * 0.5)] if latencies else 0.0
        p95 = latencies[min(total - 1, int(total * 0.95))] if latencies else 0.0

        return {
            "total_invocations": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": round(successes / total, 4),
            "failure_rate": round((total - successes) / total, 4),
            "avg_latency_ms": round(sum(latencies) / total, 2),
            "p50_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2),
            "avg_retries": round(retries / total, 2),
            "avg_reward": round(rewards / total, 2)
        }

    def get_tool_usage_distribution(self) -> Dict[str, int]:
        with self._conn:
            cur = self._conn.execute(
                "SELECT tool_name, count(*) as cnt FROM tool_analytics_events GROUP BY tool_name ORDER BY cnt DESC"
            )
            return {r["tool_name"]: r["cnt"] for r in cur.fetchall()}

    def generate_report(self) -> str:
        overall = self.get_tool_metrics()
        dist = self.get_tool_usage_distribution()

        lines = [
            "# Alpha Operating System — Tool Analytics Report",
            f"- **Total Tool Invocations**: {overall['total_invocations']}",
            f"- **Overall Success Rate**: {overall['success_rate']*100:.1f}%",
            f"- **Overall Failure Rate**: {overall['failure_rate']*100:.1f}%",
            f"- **Average Latency**: {overall['avg_latency_ms']} ms (P95: {overall['p95_latency_ms']} ms)",
            f"- **Average Retries**: {overall['avg_retries']}",
            f"- **Average Reward**: {overall['avg_reward']}",
            "",
            "## Tool Usage Distribution"
        ]
        for tname, count in dist.items():
            t_met = self.get_tool_metrics(tname)
            lines.append(f"- **{tname}**: {count} calls | {t_met['success_rate']*100:.1f}% success | {t_met['avg_latency_ms']}ms avg")

        return "\n".join(lines)
