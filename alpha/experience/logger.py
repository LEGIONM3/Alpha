"""Experience Logger: Append-only persistent execution ledger with reward tracking."""

import json
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from alpha.experience.schemas import ExperienceRecord, ExperienceQuery

class ExperienceLogger:
    """Manages recording and querying the experience log."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return self._conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experience_logs (
                    trace_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    step_number INTEGER,
                    goal_id TEXT,
                    decision_context_json TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    model_output TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    reward REAL NOT NULL,
                    latency_ms REAL NOT NULL,
                    tokens_used_est INTEGER NOT NULL,
                    reflection_report_id TEXT,
                    error_message TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_task ON experience_logs(task_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_success ON experience_logs(success)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_reward ON experience_logs(reward)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_time ON experience_logs(timestamp)")
            conn.commit()

    def record(self, record: ExperienceRecord) -> ExperienceRecord:
        """Deterministically append an execution experience to the log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO experience_logs (
                    trace_id, task_id, step_number, goal_id,
                    decision_context_json, action_taken, model_output,
                    success, reward, latency_ms, tokens_used_est,
                    reflection_report_id, error_message, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.trace_id,
                record.task_id,
                record.step_number,
                record.goal_id,
                json.dumps(record.decision_context),
                record.action_taken,
                record.model_output,
                1 if record.success else 0,
                record.reward,
                record.latency_ms,
                record.tokens_used_est,
                record.reflection_report_id,
                record.error_message,
                record.timestamp.isoformat()
            ))
            conn.commit()
        return record

    def query(self, query: ExperienceQuery) -> List[ExperienceRecord]:
        """Query experience records matching parameters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM experience_logs WHERE 1=1"
            params: list = []

            if query.task_id:
                sql += " AND task_id = ?"
                params.append(query.task_id)

            if query.goal_id:
                sql += " AND goal_id = ?"
                params.append(query.goal_id)

            if query.only_failures:
                sql += " AND success = 0"
            elif query.only_successes:
                sql += " AND success = 1"

            if query.min_reward is not None:
                sql += " AND reward >= ?"
                params.append(query.min_reward)

            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(query.limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_record(r) for r in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """Compute performance statistics across recorded history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as total_successes,
                    AVG(reward) as avg_reward,
                    AVG(latency_ms) as avg_latency_ms,
                    SUM(tokens_used_est) as total_tokens
                FROM experience_logs
            """)
            row = cursor.fetchone()
            total = row["total_runs"] or 0
            successes = row["total_successes"] or 0
            success_rate = (successes / total) if total > 0 else 0.0

            return {
                "total_runs": total,
                "successful_runs": successes,
                "failed_runs": total - successes,
                "success_rate": round(success_rate, 4),
                "avg_reward": round(row["avg_reward"] or 0.0, 4),
                "avg_latency_ms": round(row["avg_latency_ms"] or 0.0, 2),
                "total_tokens_used": row["total_tokens"] or 0
            }

    def _row_to_record(self, row: sqlite3.Row) -> ExperienceRecord:
        return ExperienceRecord(
            trace_id=row["trace_id"],
            task_id=row["task_id"],
            step_number=row["step_number"],
            goal_id=row["goal_id"],
            decision_context=json.loads(row["decision_context_json"]),
            action_taken=row["action_taken"],
            model_output=row["model_output"],
            success=bool(row["success"]),
            reward=row["reward"],
            latency_ms=row["latency_ms"],
            tokens_used_est=row["tokens_used_est"],
            reflection_report_id=row["reflection_report_id"],
            error_message=row["error_message"],
            timestamp=datetime.fromisoformat(row["timestamp"])
        )
