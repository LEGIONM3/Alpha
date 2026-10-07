"""Tool Memory Integration: Records every tool interaction, inputs, outputs, latency, cost, and lessons learned."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from alpha.tools.protocol import ToolResult, utc_now
from alpha.memory.manager import MemoryManager

class ToolInteractionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_name: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output_summary: str
    full_output: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float
    cost_units: float
    success: bool
    success_score: float = 1.0
    lesson_learned: Optional[str] = None
    executed_at: datetime = Field(default_factory=utc_now)

class ToolMemoryStore:
    """Persistent SQLite store recording every tool interaction and bridging to Alpha's Memory Manager."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None, db_path: str = ":memory:"):
        self.memory_manager = memory_manager
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_interactions (
                    id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    inputs_json TEXT NOT NULL,
                    output_summary TEXT NOT NULL,
                    full_output TEXT,
                    error TEXT,
                    latency_ms REAL NOT NULL,
                    cost_units REAL NOT NULL,
                    success INTEGER NOT NULL,
                    success_score REAL NOT NULL,
                    lesson_learned TEXT,
                    executed_at TEXT NOT NULL
                )
            """)
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_interactions(tool_name)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_success ON tool_interactions(success)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_executed ON tool_interactions(executed_at)")

    def record_interaction(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        result: ToolResult,
        success_score: float = 1.0,
        lesson_learned: Optional[str] = None
    ) -> ToolInteractionRecord:
        """Store detailed tool interaction record and create corresponding cognitive memory."""
        summary = result.summary(max_length=200)
        full_out_str = str(result.output)[:10_000] if result.output is not None else None

        record = ToolInteractionRecord(
            tool_name=tool_name,
            inputs=inputs,
            output_summary=summary,
            full_output=full_out_str,
            error=result.error,
            latency_ms=result.latency_ms,
            cost_units=result.cost_units,
            success=result.success,
            success_score=success_score if result.success else 0.0,
            lesson_learned=lesson_learned
        )

        with self._conn:
            self._conn.execute("""
                INSERT OR REPLACE INTO tool_interactions (
                    id, tool_name, inputs_json, output_summary, full_output,
                    error, latency_ms, cost_units, success, success_score,
                    lesson_learned, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.tool_name,
                json.dumps(record.inputs, default=str),
                record.output_summary,
                record.full_output,
                record.error,
                record.latency_ms,
                record.cost_units,
                1 if record.success else 0,
                record.success_score,
                record.lesson_learned,
                record.executed_at.isoformat()
            ))

        # Bridge into MemoryManager if wired
        if self.memory_manager:
            if record.success:
                obs = f"Tool '{tool_name}' completed successfully in {record.latency_ms:.1f}ms: {summary}"
                self.memory_manager.store_observation(obs, context={"tool_name": tool_name})
            else:
                self.memory_manager.store_failure(
                    task_id=record.id,
                    description=f"Invocation of tool '{tool_name}'",
                    error_message=record.error or "Unknown error",
                    root_cause=summary
                )

            if lesson_learned:
                self.memory_manager.store_lesson_learned(
                    rule=lesson_learned,
                    context_trigger=f"tool_usage_{tool_name}",
                    rationale=f"Distilled from tool '{tool_name}' execution"
                )

        return record

    def get_tool_history(self, tool_name: Optional[str] = None, limit: int = 10) -> List[ToolInteractionRecord]:
        with self._conn:
            if tool_name:
                cur = self._conn.execute(
                    "SELECT * FROM tool_interactions WHERE tool_name = ? ORDER BY executed_at DESC LIMIT ?",
                    (tool_name, limit)
                )
            else:
                cur = self._conn.execute(
                    "SELECT * FROM tool_interactions ORDER BY executed_at DESC LIMIT ?",
                    (limit,)
                )
            rows = cur.fetchall()

        records = []
        for r in rows:
            records.append(ToolInteractionRecord(
                id=r["id"],
                tool_name=r["tool_name"],
                inputs=json.loads(r["inputs_json"]),
                output_summary=r["output_summary"],
                full_output=r["full_output"],
                error=r["error"],
                latency_ms=r["latency_ms"],
                cost_units=r["cost_units"],
                success=bool(r["success"]),
                success_score=r["success_score"],
                lesson_learned=r["lesson_learned"],
                executed_at=datetime.fromisoformat(r["executed_at"])
            ))
        return records
