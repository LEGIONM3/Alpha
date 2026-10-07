"""Evidence Chains: Immutable epistemic provenance linking observations to theories."""

from __future__ import annotations

import hashlib
import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ChainLink(BaseModel):
    step_type: str  # OBSERVATION, EVIDENCE, FINDING, THEORY
    entity_id: str
    prev_hash: str
    data_digest: str
    link_hash: str
    timestamp: float = Field(default_factory=time.time)


class EvidenceProvenanceChain(BaseModel):
    chain_id: str
    hypothesis_id: str
    links: List[ChainLink] = Field(default_factory=list)
    is_valid: bool = True

    def add_link(self, step_type: str, entity_id: str, payload: Any) -> ChainLink:
        prev_hash = self.links[-1].link_hash if self.links else "GENESIS"
        data_str = str(payload)
        data_digest = hashlib.sha256(data_str.encode()).hexdigest()[:16]

        block = f"{prev_hash}:{step_type}:{entity_id}:{data_digest}"
        link_hash = hashlib.sha256(block.encode()).hexdigest()[:16]

        link = ChainLink(
            step_type=step_type,
            entity_id=entity_id,
            prev_hash=prev_hash,
            data_digest=data_digest,
            link_hash=link_hash
        )
        self.links.append(link)
        return link

    def verify_integrity(self) -> bool:
        """Verify unbroken cryptographic cryptographic chain of custody."""
        if not self.links:
            return True
        for i, link in enumerate(self.links):
            expected_prev = "GENESIS" if i == 0 else self.links[i-1].link_hash
            if link.prev_hash != expected_prev:
                self.is_valid = False
                return False
            recomputed = hashlib.sha256(
                f"{link.prev_hash}:{link.step_type}:{link.entity_id}:{link.data_digest}".encode()
            ).hexdigest()[:16]
            if link.link_hash != recomputed:
                self.is_valid = False
                return False
        self.is_valid = True
        return True
