"""SQLite persistence layer for Memory Manager with FTS5 search support."""

import json
import sqlite3
from typing import List, Optional
from datetime import datetime, timezone
from alpha.memory.schemas import MemoryItem, MemoryQuery
from alpha.core.types import MemoryType

class MemoryStorage:
    """Manages SQLite storage and keyword/FTS search for memories."""

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
            # Main memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    importance REAL NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_accessed_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(memory_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_importance ON memories(importance)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_created ON memories(created_at)")

            # FTS5 virtual table for full-text retrieval
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    content,
                    tags
                )
            """)
            conn.commit()

    def save(self, item: MemoryItem) -> MemoryItem:
        """Insert or update a memory item and keep FTS5 synchronized."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            tags_str = " ".join(item.tags)
            cursor.execute("""
                INSERT OR REPLACE INTO memories (
                    id, memory_type, content, metadata_json, tags_json,
                    importance, access_count, created_at, last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id,
                item.memory_type.value,
                item.content,
                json.dumps(item.metadata),
                json.dumps(item.tags),
                item.importance,
                item.access_count,
                item.created_at.isoformat(),
                item.last_accessed_at.isoformat()
            ))

            # Update FTS index
            cursor.execute("DELETE FROM memories_fts WHERE id = ?", (item.id,))
            cursor.execute("INSERT INTO memories_fts (id, content, tags) VALUES (?, ?, ?)",
                           (item.id, item.content, tags_str))
            conn.commit()
        return item

    def get(self, memory_id: str) -> Optional[MemoryItem]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_item(row)

    def search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Search memories with text matching, type filtering, importance thresholds, and token budget limit."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            params: list = []
            
            # If query text is provided, use FTS5
            if query.query_text and query.query_text.strip():
                # Clean query for FTS5 (escape special chars)
                cleaned = "".join(c for c in query.query_text if c.isalnum() or c.isspace()).strip()
                if cleaned:
                    fts_query = " OR ".join(cleaned.split())
                    sql = """
                        SELECT m.* FROM memories m
                        JOIN memories_fts f ON m.id = f.id
                        WHERE memories_fts MATCH ?
                    """
                    params.append(fts_query)
                else:
                    sql = "SELECT m.* FROM memories m WHERE 1=1"
            else:
                sql = "SELECT m.* FROM memories m WHERE 1=1"

            if query.memory_types:
                placeholders = ",".join("?" for _ in query.memory_types)
                sql += f" AND m.memory_type IN ({placeholders})"
                params.extend([t.value for t in query.memory_types])

            if query.min_importance > 0.0:
                sql += " AND m.importance >= ?"
                params.append(query.min_importance)

            sql += " ORDER BY m.importance DESC, m.created_at DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results: List[MemoryItem] = []
            total_tokens = 0
            
            for row in rows:
                item = self._row_to_item(row)
                
                # Check tag filtering if requested
                if query.tags:
                    if not any(t.lower() in [item_t.lower() for item_t in item.tags] for t in query.tags):
                        continue
                        
                item_tokens = item.estimate_tokens()
                if query.max_tokens and (total_tokens + item_tokens > query.max_tokens) and results:
                    break
                    
                results.append(item)
                total_tokens += item_tokens
                if len(results) >= query.limit:
                    break

            # Update access counts and timestamps for retrieved memories
            if results:
                now_str = datetime.now(timezone.utc).isoformat()
                for item in results:
                    cursor.execute("""
                        UPDATE memories 
                        SET access_count = access_count + 1, last_accessed_at = ?
                        WHERE id = ?
                    """, (now_str, item.id))
                conn.commit()

            return results

    def delete(self, memory_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            cursor.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories")
            cursor.execute("DELETE FROM memories_fts")
            conn.commit()

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            memory_type=MemoryType(row["memory_type"]),
            content=row["content"],
            metadata=json.loads(row["metadata_json"]),
            tags=json.loads(row["tags_json"]),
            importance=row["importance"],
            access_count=row["access_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_accessed_at=datetime.fromisoformat(row["last_accessed_at"])
        )
