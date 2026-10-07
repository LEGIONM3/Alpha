"""Knowledge Store component: Manages documents, notes, ADRs, and research."""

import json
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from alpha.core.types import KnowledgeType
from alpha.knowledge.schemas import KnowledgeDocument, KnowledgeQuery

class KnowledgeStore:
    """Persistent store for project knowledge, notes, architectural decisions, and research."""

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
                CREATE TABLE IF NOT EXISTS knowledge_docs (
                    doc_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    tags_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kdoc_type ON knowledge_docs(doc_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kdoc_title ON knowledge_docs(title)")

            # FTS5 virtual table for searching documents
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    doc_id UNINDEXED,
                    title,
                    content,
                    summary,
                    tags
                )
            """)
            conn.commit()

    def store_document(
        self,
        title: str,
        content: str,
        doc_type: KnowledgeType = KnowledgeType.DOCUMENT,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeDocument:
        """Store a document, auto-generate summary if missing, and index in FTS5."""
        clean_content = content.strip()
        doc_summary = summary or self.summarize(clean_content)
        all_tags = list(set((tags or []) + [doc_type.value]))

        doc = KnowledgeDocument(
            title=title.strip(),
            doc_type=doc_type,
            content=clean_content,
            summary=doc_summary,
            tags=all_tags,
            metadata=metadata or {}
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_docs (
                    doc_id, title, doc_type, content, summary,
                    tags_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.doc_id,
                doc.title,
                doc.doc_type.value,
                doc.content,
                doc.summary,
                json.dumps(doc.tags),
                json.dumps(doc.metadata),
                doc.created_at.isoformat(),
                doc.updated_at.isoformat()
            ))

            tags_str = " ".join(doc.tags)
            cursor.execute("DELETE FROM knowledge_fts WHERE doc_id = ?", (doc.doc_id,))
            cursor.execute("""
                INSERT INTO knowledge_fts (doc_id, title, content, summary, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (doc.doc_id, doc.title, doc.content, doc.summary or "", tags_str))
            conn.commit()

        return doc

    def store_adr(self, title: str, decision: str, rationale: str, status: str = "ACCEPTED") -> KnowledgeDocument:
        """Store an Architecture Decision Record (ADR)."""
        content = f"DECISION:\n{decision}\n\nRATIONALE:\n{rationale}\n\nSTATUS: {status}"
        return self.store_document(
            title=f"ADR: {title}",
            content=content,
            doc_type=KnowledgeType.ARCHITECTURE_DECISION,
            tags=["adr", "architecture", status.lower()],
            metadata={"status": status}
        )

    def store_note(self, title: str, note_body: str, tags: Optional[List[str]] = None) -> KnowledgeDocument:
        """Store a lightweight project note."""
        return self.store_document(
            title=title,
            content=note_body,
            doc_type=KnowledgeType.PROJECT_NOTE,
            tags=tags or []
        )

    def summarize(self, text: str, max_sentences: int = 2) -> str:
        """Deterministic extractive summarizer for documents."""
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        if not sentences:
            return text[:150]
        summary_sentences = sentences[:max_sentences]
        return ". ".join(summary_sentences) + "."

    def retrieve(self, query: KnowledgeQuery) -> List[KnowledgeDocument]:
        """Search and retrieve knowledge documents matching criteria within token budgets."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            params: list = []

            if query.query_text and query.query_text.strip():
                cleaned = "".join(c for c in query.query_text if c.isalnum() or c.isspace()).strip()
                if cleaned:
                    fts_query = " OR ".join(cleaned.split())
                    sql = """
                        SELECT k.* FROM knowledge_docs k
                        JOIN knowledge_fts f ON k.doc_id = f.doc_id
                        WHERE knowledge_fts MATCH ?
                    """
                    params.append(fts_query)
                else:
                    sql = "SELECT k.* FROM knowledge_docs k WHERE 1=1"
            else:
                sql = "SELECT k.* FROM knowledge_docs k WHERE 1=1"

            if query.doc_types:
                placeholders = ",".join("?" for _ in query.doc_types)
                sql += f" AND k.doc_type IN ({placeholders})"
                params.extend([t.value for t in query.doc_types])

            sql += " ORDER BY k.updated_at DESC"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results: List[KnowledgeDocument] = []
            total_tokens = 0

            for r in rows:
                doc = self._row_to_doc(r)
                if query.tags:
                    if not any(t.lower() in [dt.lower() for dt in doc.tags] for t in query.tags):
                        continue

                doc_tokens = doc.estimate_tokens()
                if query.max_tokens and (total_tokens + doc_tokens > query.max_tokens) and results:
                    break

                results.append(doc)
                total_tokens += doc_tokens
                if len(results) >= query.limit:
                    break

            return results

    def format_knowledge_for_prompt(self, query_text: str, max_tokens: int = 500) -> str:
        """Format retrieved knowledge summaries into a concise prompt context block."""
        docs = self.retrieve(KnowledgeQuery(query_text=query_text, max_tokens=max_tokens, limit=3))
        if not docs:
            return "(No specific project documentation found)"

        lines: List[str] = ["### Relevant Knowledge & Specifications:"]
        for d in docs:
            snippet = d.summary if d.summary else d.content[:180]
            lines.append(f"- **{d.title}** [{d.doc_type.value}]: {snippet}")
        return "\n".join(lines)

    def _row_to_doc(self, row: sqlite3.Row) -> KnowledgeDocument:
        return KnowledgeDocument(
            doc_id=row["doc_id"],
            title=row["title"],
            doc_type=KnowledgeType(row["doc_type"]),
            content=row["content"],
            summary=row["summary"],
            tags=json.loads(row["tags_json"]),
            metadata=json.loads(row["metadata_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
