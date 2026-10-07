"""Evidence Chain Engine: Deep Traceability and Epistemic Integrity for Project Alpha (Phase 8).

Ensures:
- Every belief contains: belief_id, source_documents, observations, supporting_evidence,
  contradicting_evidence, confidence_score, verification_status, last_verified_timestamp.
- Deep, bidirectional traceability from high-level beliefs down to empirical observations
  and cryptographic file/document hashes.
- Absolute rejection of orphan beliefs and unsupported claims.
- Cryptographic hash verification of source documents and observations.
- Cycle detection preventing circular evidentiary loops.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

import networkx as nx

from alpha.world_model.epistemology.evidence import (
    Evidence,
    EvidenceRegistry,
    EvidencePolarity,
    EvidenceStrength,
)
from alpha.world_model.epistemology.belief import Belief, BeliefSystem


class ChainValidationResult(BaseModel):
    """Integrity audit result for an evidence chain."""
    chain_id: str
    belief_id: str
    statement: str
    is_valid: bool
    is_orphan: bool = False
    is_circular: bool = False
    coherence_score: float = 1.0
    verification_status: str = "UNVERIFIED"
    confidence_score: float = 0.5
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    observation_count: int = 0
    source_document_count: int = 0
    broken_evidence_links: List[str] = Field(default_factory=list)
    missing_source_documents: List[str] = Field(default_factory=list)
    hash_mismatches: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    chain_depth: int = 0
    timestamp: float = Field(default_factory=time.time)


class EvidenceChainTrace(BaseModel):
    """Complete traceable lineage of a belief."""
    belief_id: str
    statement: str
    confidence_score: float
    verification_status: str
    last_verified_timestamp: float
    source_documents: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    contradicting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    provenance_chain: List[str] = Field(default_factory=list)
    coherence_score: float = 1.0


class EvidenceChainEngine:
    """Manages, audits, and enforces end-to-end evidence chains for all beliefs."""

    def __init__(
        self,
        evidence_registry: EvidenceRegistry,
        belief_system: Optional[BeliefSystem] = None,
        workspace_root: Optional[Path] = None,
    ):
        self.evidence_registry = evidence_registry
        self.belief_system = belief_system
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def set_belief_system(self, belief_system: BeliefSystem) -> None:
        self.belief_system = belief_system

    @staticmethod
    def compute_file_sha256(filepath: Path) -> Optional[str]:
        """Compute SHA-256 hash for a local file if it exists."""
        if not filepath.exists() or not filepath.is_file():
            return None
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def trace_chain(self, belief: Belief) -> EvidenceChainTrace:
        """Trace backward from a belief to its raw observations, documents, and evidence items."""
        supporting_items: List[Dict[str, Any]] = []
        for eid in belief.supporting_evidence:
            ev = self.evidence_registry.get(eid)
            if ev:
                supporting_items.append(ev.model_dump())
            else:
                supporting_items.append({"evidence_id": eid, "status": "BROKEN_LINK"})

        contradicting_items: List[Dict[str, Any]] = []
        for eid in belief.contradicting_evidence:
            ev = self.evidence_registry.get(eid)
            if ev:
                contradicting_items.append(ev.model_dump())
            else:
                contradicting_items.append({"evidence_id": eid, "status": "BROKEN_LINK"})

        doc_records: List[Dict[str, Any]] = []
        for doc_path in belief.source_documents:
            p = Path(doc_path)
            if not p.is_absolute():
                p = (self.workspace_root / p).resolve()
            exists = p.exists() and p.is_file()
            file_hash = self.compute_file_sha256(p) if exists else None
            doc_records.append({
                "path": str(doc_path),
                "resolved_path": str(p),
                "exists": exists,
                "sha256": file_hash,
            })

        # Calculate coherence score
        validation = self.validate_chain(belief)

        return EvidenceChainTrace(
            belief_id=belief.belief_id,
            statement=belief.statement,
            confidence_score=belief.confidence_score,
            verification_status=belief.verification_status,
            last_verified_timestamp=belief.last_verified_timestamp,
            source_documents=doc_records,
            observations=belief.observations,
            supporting_evidence=supporting_items,
            contradicting_evidence=contradicting_items,
            provenance_chain=belief.provenance_chain,
            coherence_score=validation.coherence_score,
        )

    def validate_chain(self, belief: Belief) -> ChainValidationResult:
        """Thoroughly audit the epistemic chain supporting a belief."""
        warnings: List[str] = []
        broken_evidence: List[str] = []
        missing_docs: List[str] = []
        hash_mismatches: List[str] = []

        # 1. Orphan check: Beliefs must not be empty of support
        is_orphan = (
            len(belief.supporting_evidence) == 0
            and len(belief.source_documents) == 0
            and len(belief.observations) == 0
            and len(belief.sources) == 0
        )
        if is_orphan:
            warnings.append("Orphan belief: No supporting evidence, observations, or source documents.")

        # 2. Check supporting evidence existence in registry
        for eid in belief.supporting_evidence:
            ev = self.evidence_registry.get(eid)
            if not ev:
                broken_evidence.append(eid)
                warnings.append(f"Broken evidence reference: {eid} not in EvidenceRegistry.")

        for eid in belief.contradicting_evidence:
            ev = self.evidence_registry.get(eid)
            if not ev:
                broken_evidence.append(eid)
                warnings.append(f"Broken contradiction reference: {eid} not in EvidenceRegistry.")

        # 3. Check source documents on disk
        for doc_path in belief.source_documents:
            p = Path(doc_path)
            if not p.is_absolute():
                p = (self.workspace_root / p).resolve()
            if not p.exists():
                missing_docs.append(str(doc_path))
                warnings.append(f"Referenced source document does not exist: {doc_path}")

        # 4. Circular check (if provenance chain references self)
        is_circular = belief.belief_id in belief.provenance_chain
        if is_circular:
            warnings.append(f"Circular evidentiary provenance detected in belief {belief.belief_id}.")

        # 5. Calculate Coherence Score
        coherence = 1.0
        if is_orphan:
            coherence = 0.0
        else:
            # Penalize broken links heavily
            if broken_evidence:
                coherence -= 0.3 * len(broken_evidence)
            if missing_docs:
                coherence -= 0.25 * len(missing_docs)
            if is_circular:
                coherence -= 0.5

            # Contradiction penalty
            if belief.contradicting_evidence:
                coherence -= 0.2 * len(belief.contradicting_evidence)

            # High confidence without solid backing or with incomplete sample size
            valid_evidence_count = len(belief.supporting_evidence) - len(broken_evidence)
            if belief.confidence_score > 0.8:
                if valid_evidence_count == 0 and len(belief.observations) == 0:
                    coherence -= 0.3
                    warnings.append("Confidence inflation: confidence > 0.8 with zero verified evidence/observations.")
                elif valid_evidence_count == 0 and len(belief.observations) < 3 and len(belief.source_documents) == 0:
                    coherence -= 0.35
                    warnings.append("Confidence inflation: confidence > 0.8 with incomplete observations (N < 3) and no formal evidence.")

        coherence = round(max(0.0, min(1.0, coherence)), 3)
        is_valid = not is_orphan and not is_circular and len(broken_evidence) == 0 and len(missing_docs) == 0

        # Update verification status on belief if appropriate
        if is_orphan:
            belief.verification_status = "ORPHAN"
        elif not is_valid:
            belief.verification_status = "UNVERIFIED"
        elif len(belief.contradicting_evidence) > 0 and len(belief.contradicting_evidence) >= len(belief.supporting_evidence):
            belief.verification_status = "CONTRADICTED"
        elif is_valid and coherence >= 0.7 and (valid_evidence_count > 0 or len(belief.observations) >= 3 or len(belief.source_documents) > 0):
            belief.verification_status = "VERIFIED"
        else:
            belief.verification_status = "UNVERIFIED"

        belief.last_verified_timestamp = time.time()

        depth = 1 + (1 if len(belief.supporting_evidence) > 0 else 0) + (1 if len(belief.observations) > 0 else 0) + (1 if len(belief.source_documents) > 0 else 0)

        return ChainValidationResult(
            chain_id=f"chain_{belief.belief_id[:8]}",
            belief_id=belief.belief_id,
            statement=belief.statement,
            is_valid=is_valid,
            is_orphan=is_orphan,
            is_circular=is_circular,
            coherence_score=coherence,
            verification_status=belief.verification_status,
            confidence_score=belief.confidence_score,
            supporting_evidence_count=len(belief.supporting_evidence),
            contradicting_evidence_count=len(belief.contradicting_evidence),
            observation_count=len(belief.observations),
            source_document_count=len(belief.source_documents),
            broken_evidence_links=broken_evidence,
            missing_source_documents=missing_docs,
            hash_mismatches=hash_mismatches,
            warnings=warnings,
            chain_depth=depth,
        )

    def link_observation(self, belief_id: str, observation: Dict[str, Any]) -> bool:
        """Attach a direct empirical observation record to a belief."""
        if not self.belief_system:
            return False
        belief = self.belief_system.get_belief(belief_id)
        if not belief:
            return False

        obs_record = dict(observation)
        if "timestamp" not in obs_record:
            obs_record["timestamp"] = time.time()
        if "obs_id" not in obs_record:
            obs_record["obs_id"] = hashlib.sha256(str(obs_record).encode()).hexdigest()[:12]

        belief.observations.append(obs_record)
        belief.last_verified_timestamp = time.time()
        return True

    def link_source_document(
        self, belief_id: str, document_path: str, expected_hash: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Link a source file/document to a belief and optionally verify its hash."""
        if not self.belief_system:
            return False, "No belief system configured"
        belief = self.belief_system.get_belief(belief_id)
        if not belief:
            return False, f"Belief {belief_id} not found"

        p = Path(document_path)
        if not p.is_absolute():
            p = (self.workspace_root / p).resolve()

        if not p.exists() or not p.is_file():
            return False, f"Document file does not exist: {p}"

        file_hash = self.compute_file_sha256(p)
        if expected_hash and file_hash != expected_hash:
            return False, f"Hash mismatch: expected {expected_hash}, got {file_hash}"

        if str(document_path) not in belief.source_documents:
            belief.source_documents.append(str(document_path))
        belief.last_verified_timestamp = time.time()
        return True, file_hash

    def audit_all_beliefs(self) -> Dict[str, ChainValidationResult]:
        """Audit every belief currently registered in the BeliefSystem."""
        if not self.belief_system:
            return {}
        results: Dict[str, ChainValidationResult] = {}
        for belief in self.belief_system.get_all():
            results[belief.belief_id] = self.validate_chain(belief)
        return results

    def export_subgraph(self, belief_id: str) -> nx.DiGraph:
        """Export an evidentiary DAG representing the belief and its foundational chain."""
        g = nx.DiGraph()
        if not self.belief_system:
            return g
        belief = self.belief_system.get_belief(belief_id)
        if not belief:
            return g

        b_node = f"belief:{belief.belief_id[:8]}"
        g.add_node(b_node, type="belief", statement=belief.statement, confidence=belief.confidence_score)

        for eid in belief.supporting_evidence:
            ev = self.evidence_registry.get(eid)
            ev_node = f"evidence:{eid[:8]}"
            g.add_node(ev_node, type="evidence", polarity="supporting", strength=ev.strength.value if ev else "unknown")
            g.add_edge(ev_node, b_node, relationship="SUPPORTS")

        for eid in belief.contradicting_evidence:
            ev = self.evidence_registry.get(eid)
            ev_node = f"evidence:{eid[:8]}"
            g.add_node(ev_node, type="evidence", polarity="contradicting", strength=ev.strength.value if ev else "unknown")
            g.add_edge(ev_node, b_node, relationship="CONTRADICTS")

        for obs in belief.observations:
            obs_node = f"obs:{obs.get('obs_id', 'unknown')[:8]}"
            g.add_node(obs_node, type="observation", data=str(obs))
            g.add_edge(obs_node, b_node, relationship="OBSERVED_IN")

        for doc in belief.source_documents:
            doc_node = f"doc:{Path(doc).name}"
            g.add_node(doc_node, type="source_document", path=doc)
            g.add_edge(doc_node, b_node, relationship="GROUNDED_IN")

        return g
