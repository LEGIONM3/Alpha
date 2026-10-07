"""Tiered Knowledge Loader for Project Alpha: 4-Tier Knowledge Architecture.

Tier 0: Identity, Constitution, Governance (Always loaded in memory)
Tier 1: Core cognitive knowledge (Embedded & cached, fast lookup)
Tier 2: Frequently used domains (Dynamic semantic retrieval)
Tier 3: Rare domains (On-demand lazy loading)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from alpha.core.identity import IdentityState, IdentityLoader, ConstitutionEngine
from alpha.memory.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeTier(int):
    TIER_0 = 0  # Invariant Identity & Governance
    TIER_1 = 1  # Core Cognitive & Axioms
    TIER_2 = 2  # Frequently Used Domains
    TIER_3 = 3  # Rare / Deep Archive


class TieredDocument(BaseModel):
    id: str
    tier: int
    title: str
    content: str
    domain: str
    is_active: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TieredKnowledgeSystem:
    """Manages multi-tier knowledge loading and selective activation."""

    def __init__(
        self,
        identity_path: str = "alpha_identity.md",
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.embedding_service = embedding_service or EmbeddingService()

        # Tier 0: Identity & Governance (Always loaded)
        self.identity: IdentityState = IdentityLoader.load_from_markdown(identity_path)
        self.tier0_header: str = ConstitutionEngine.generate_system_prompt_header(self.identity)

        # Tier 1, 2, 3 Storage
        self._tier1_items: Dict[str, TieredDocument] = {}
        self._tier2_items: Dict[str, TieredDocument] = {}
        self._tier3_items: Dict[str, TieredDocument] = {}

        self._initialize_core_tiers()

    def _initialize_core_tiers(self) -> None:
        """Seed baseline Tier 1 and Tier 2 knowledge."""
        # Tier 1: Core Cognitive Knowledge
        t1_docs = [
            ("t1_ontology_axioms", "Universal Ontology Contract", "Alpha organizes reality into 25 canonical entity types and 14 bidirectional relationship types.", "ontology"),
            ("t1_truth_rules", "Truth Verification Protocol", "No belief may exist without empirical evidence. Contradictions trigger resolution.", "epistemology"),
            ("t1_sandbox_rules", "Sandbox Security Protocol", "All external actions and code executions must run in isolated sandboxes with deterministic contracts.", "security")
        ]
        for doc_id, title, content, domain in t1_docs:
            doc = TieredDocument(id=doc_id, tier=1, title=title, content=content, domain=domain, is_active=True)
            self._tier1_items[doc_id] = doc
            self.embedding_service.add_document(doc_id, f"{title}: {content}", {"tier": 1, "domain": domain})

        # Tier 2: Frequently Used Domains
        t2_docs = [
            ("t2_git_workflow", "Git Workflow Conventions", "Inspect commits, diffs, branches, and PR reviews deterministically.", "git"),
            ("t2_api_rate_limiting", "API Gateway Resilience", "Token bucket rate limiting and 3-state circuit breakers protect external endpoints.", "network"),
            ("t2_sqlite_persistence", "SQLite Persistent Memory", "Scaffolding DB stores observations, tasks, and telemetry in WAL mode.", "database")
        ]
        for doc_id, title, content, domain in t2_docs:
            doc = TieredDocument(id=doc_id, tier=2, title=title, content=content, domain=domain, is_active=False)
            self._tier2_items[doc_id] = doc
            self.embedding_service.add_document(doc_id, f"{title}: {content}", {"tier": 2, "domain": domain})

        # Tier 3: Rare Deep Archive
        t3_docs = [
            ("t3_quantum_sim", "Quantum Entanglement Simulation", "Theoretical simulation parameters for non-local state correlations.", "quantum_physics"),
            ("t3_historical_v1_notes", "Legacy Alpha Phase 0 Scratchpad", "Initial exploratory design notes from early prototyping.", "historical_archive")
        ]
        for doc_id, title, content, domain in t3_docs:
            doc = TieredDocument(id=doc_id, tier=3, title=title, content=content, domain=domain, is_active=False)
            self._tier3_items[doc_id] = doc

    def get_tier0_context(self) -> str:
        """Always active Tier 0 identity and constitutional invariants."""
        return self.tier0_header

    def get_tier1_context(self) -> str:
        """Active core cognitive knowledge."""
        lines = ["### TIER 1 - CORE COGNITIVE AXIOMS"]
        for d in self._tier1_items.values():
            lines.append(f"- **{d.title}**: {d.content}")
        return "\n".join(lines)

    def retrieve_tier2_context(self, query: str, top_k: int = 2) -> List[TieredDocument]:
        """Dynamic semantic retrieval over Tier 2 domain knowledge."""
        matches = self.embedding_service.search(query, top_k=5)
        activated: List[TieredDocument] = []
        for item, sim in matches:
            if item.id in self._tier2_items:
                doc = self._tier2_items[item.id]
                doc.is_active = True
                activated.append(doc)
                if len(activated) >= top_k:
                    break
        return activated

    def load_tier3_on_demand(self, doc_id: str) -> Optional[TieredDocument]:
        """On-demand lazy load for rare / archived documents."""
        doc = self._tier3_items.get(doc_id)
        if doc:
            doc.is_active = True
            logger.info(f"Loaded Tier 3 document on demand: {doc.title}")
            return doc
        return None

    def assemble_prompt_context(self, task_query: str) -> str:
        """Assemble complete multi-tier prompt context."""
        sections = [
            self.get_tier0_context(),
            self.get_tier1_context()
        ]

        # Retrieve relevant Tier 2 knowledge
        t2_docs = self.retrieve_tier2_context(task_query, top_k=2)
        if t2_docs:
            t2_lines = ["### TIER 2 - DYNAMICALLY RETRIEVED DOMAIN KNOWLEDGE"]
            for d in t2_docs:
                t2_lines.append(f"- **{d.title}**: {d.content}")
            sections.append("\n".join(t2_lines))

        return "\n\n".join(sections)
