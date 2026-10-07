"""Unit tests for Component 6: Knowledge Store."""

import pytest
from alpha.core.types import KnowledgeType
from alpha.knowledge.store import KnowledgeStore
from alpha.knowledge.schemas import KnowledgeQuery

@pytest.fixture
def store():
    return KnowledgeStore(db_path=":memory:")

def test_store_and_retrieve_document(store):
    doc = store.store_document(
        title="PostgreSQL Concurrency Guidelines",
        content="Use connection pooling with max 20 connections per pool. Keep transaction scopes small.",
        tags=["postgres", "database", "concurrency"]
    )
    assert doc.doc_id is not None
    assert doc.summary is not None

    results = store.retrieve(KnowledgeQuery(query_text="connection pooling", tags=["postgres"]))
    assert len(results) == 1
    assert "PostgreSQL Concurrency" in results[0].title

def test_store_adr(store):
    adr = store.store_adr(
        title="Use SQLite FTS5 for Local Text Retrieval",
        decision="Adopt SQLite FTS5 for zero-dependency local text and memory retrieval in Phase 1.",
        rationale="Vector databases require external daemons and embeddings that burden low-resource environments."
    )
    assert adr.doc_type == KnowledgeType.ARCHITECTURE_DECISION
    assert "ADR: Use SQLite FTS5" in adr.title

def test_format_knowledge_for_prompt(store):
    store.store_document(
        title="API Design Spec",
        content="All endpoints must return JSON with an explicit 'status' code and 'data' envelope."
    )
    formatted = store.format_knowledge_for_prompt("API endpoints JSON", max_tokens=200)
    assert "### Relevant Knowledge & Specifications:" in formatted
    assert "API Design Spec" in formatted
