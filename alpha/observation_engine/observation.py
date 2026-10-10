"""Core Observation Data Model for Project Alpha Phase 9.

Represents an empirical, verifiable piece of external reality:
- observation_id: unique identifier with provenance
- source_type: type of observer (filesystem, git, test, runtime, log, doc, world_model, agent, tool, dependency, performance)
- source_uri: exact provenance URI or file path
- timestamp: ISO 8601 acquisition time
- raw_evidence: exact verifiable contents, AST deltas, git diffs, test tracebacks, metrics
- normalized_summary: concise, normalized textual summary for cognitive evaluation
- content_hash: SHA-256 hash of invariant evidence content
- confidence: calibrated certainty score (0.0 to 1.0)
- novelty_signature: structural signature for deduplication and novelty indexing
- metadata: contextual telemetry and provenance metadata
- verification_status: UNVERIFIED, VERIFIED, FALSIFIED, CONTRADICTED, STALE
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import uuid
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, model_validator


class Observation(BaseModel):
    """Represents a verified piece of external reality acquired during an autonomous cycle."""
    observation_id: str = Field(default="")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = Field(default="")
    source_type: str = Field(default="general")
    evidence: Any = Field(default_factory=dict)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Extended provenance and verification fields
    source_uri: str = Field(default="")
    raw_evidence: Any = Field(default="")
    normalized_summary: str = Field(default="")
    content_hash: str = Field(default="")
    novelty_signature: str = Field(default="")
    verification_status: str = Field(default="VERIFIED")

    # -------------------------------------------------------------------------
    # Backward Compatibility Properties & Accessors
    # -------------------------------------------------------------------------

    @property
    def content(self) -> str:
        return self.evidence

    @property
    def category(self) -> str:
        return self.source_type

    @property
    def hash(self) -> str:
        return self.content_hash

    @model_validator(mode="before")
    @classmethod
    def sync_pre_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Backward compatibility: map 'source' to source_type & source_uri
            if "source" in data and ("source_type" not in data or "source_uri" not in data):
                src = str(data["source"])
                parts = src.split(":", 1)
                if len(parts) == 2:
                    if "source_type" not in data:
                        data["source_type"] = parts[0].lower()
                    if "source_uri" not in data:
                        data["source_uri"] = parts[1]
                else:
                    if "source_type" not in data:
                        data["source_type"] = data.get("category", "general")
                    if "source_uri" not in data:
                        data["source_uri"] = src

            if "source_uri" in data and not data.get("source"):
                data["source"] = data["source_uri"]

            if "category" in data and "source_type" not in data:
                data["source_type"] = data["category"]

            # Backward compatibility: map 'evidence' or 'content'
            ev = data.get("evidence") if "evidence" in data else (
                data.get("content") if "content" in data else data.get("raw_evidence", "")
            )
            if "raw_evidence" not in data:
                data["raw_evidence"] = ev
            if "evidence" not in data:
                data["evidence"] = ev
            if "normalized_summary" not in data:
                data["normalized_summary"] = ev if isinstance(ev, str) else json.dumps(ev)

            # Map legacy 'hash' to content_hash
            if "hash" in data and not data.get("content_hash"):
                data["content_hash"] = data["hash"]

            if "timestamp" not in data or not data["timestamp"]:
                data["timestamp"] = datetime.now(timezone.utc).isoformat()
        return data

    @model_validator(mode="after")
    def compute_identifiers_if_missing(self) -> "Observation":
        # Keep source and source_uri in sync
        if not self.source and self.source_uri:
            object.__setattr__(self, "source", self.source_uri)
        if not self.source_uri and self.source:
            object.__setattr__(self, "source_uri", self.source)

        # Keep evidence and raw_evidence in sync
        if not self.evidence and self.raw_evidence:
            object.__setattr__(self, "evidence", self.raw_evidence)
        if not self.raw_evidence and self.evidence:
            object.__setattr__(self, "raw_evidence", self.evidence)

        # 1. Compute content_hash
        if not self.content_hash:
            raw_str = (
                json.dumps(self.evidence, sort_keys=True, default=str)
                if isinstance(self.evidence, dict)
                else str(self.evidence)
            )
            # Invariant content hash independent of volatile timestamp
            invariant_key = f"{self.source_type}:{self.source}:{raw_str}"
            h = hashlib.sha256(invariant_key.encode("utf-8")).hexdigest()
            object.__setattr__(self, "content_hash", h)

        # 2. Compute observation_id
        if not self.observation_id:
            oid = f"obs_{self.source_type}_{self.content_hash[:12]}"
            object.__setattr__(self, "observation_id", oid)

        # 3. Compute novelty_signature
        if not self.novelty_signature:
            norm_text = (
                self.normalized_summary.strip().lower()[:120]
                if self.normalized_summary
                else str(self.evidence).strip().lower()[:120]
            )
            sig_raw = f"{self.source_type}:{self.source}:{norm_text}"
            sig = hashlib.sha256(sig_raw.encode("utf-8")).hexdigest()[:16]
            object.__setattr__(self, "novelty_signature", sig)

        return self


# Backwards compatibility alias
ObservationRecord = Observation
