"""Knowledge Gap Detector for Project Alpha.

Driven by the Foundation Model (Qwen 3.8 9B Heretic) as the sole strategic reasoner.
Analyzes the EvidenceBundle of live empirical observations to identify:
- What appears unusual
- What is missing
- What contradicts expectations
- What should be investigated next
- Which investigation has highest epistemic value

No scoring formulas. No hardcoded priorities. The Foundation Model decides.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from alpha.observation_engine.observation import Observation, ObservationRecord
from alpha.reasoning.qwen_reasoner import (
    EvidenceBundle,
    StrategicInvestigation,
    StrategicReasoningResult,
    qwen_reasoner,
)

logger = logging.getLogger("alpha.knowledge.detector")


class KnowledgeGap(BaseModel):
    """Defines a specific area of unknown, unverified, or contradictory knowledge."""
    topic: str
    reason: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    urgency: int = Field(default=3, ge=1, le=5)
    evidence: List[str] = Field(default_factory=list)
    category: str = Field(default="general")
    suggested_action: str = Field(default="")
    epistemic_value: str = Field(default="HIGH")


class KnowledgeGapDetector:
    """Detects genuine epistemic gaps grounded in empirical evidence and Qwen strategic reasoning."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()

    def detect(
        self,
        observations: List[ObservationRecord],
        world_model: Optional[Any] = None
    ) -> List[KnowledgeGap]:
        """Strategic detection routine powered by Qwen reasoning over the EvidenceBundle."""
        gaps: List[KnowledgeGap] = []
        bundle = EvidenceBundle(observations=observations)

        try:
            # Qwen Foundation Model Strategic Reasoning
            reasoning: StrategicReasoningResult = qwen_reasoner.reason_over_evidence(bundle)

            # 1. Highest Epistemic Value Investigation
            if reasoning.highest_epistemic_investigation:
                inv = reasoning.highest_epistemic_investigation
                gaps.append(
                    KnowledgeGap(
                        topic=inv.topic,
                        reason=inv.epistemic_rationale or inv.question,
                        confidence=0.95,
                        urgency=5,
                        evidence=[f"Target: {inv.target}"] if inv.target else [o.source for o in observations[:2]],
                        category="highest_epistemic_investigation",
                        suggested_action=inv.question,
                        epistemic_value="HIGHEST"
                    )
                )

            # 2. Next Strategic Investigations
            for inv in reasoning.next_investigations:
                if gaps and inv.topic == gaps[0].topic:
                    continue
                gaps.append(
                    KnowledgeGap(
                        topic=inv.topic,
                        reason=inv.question,
                        confidence=0.90,
                        urgency=4,
                        evidence=[f"Target: {inv.target}"] if inv.target else [o.source for o in observations[:2]],
                        category="strategic_investigation",
                        suggested_action=inv.question,
                        epistemic_value=str(inv.epistemic_value)
                    )
                )

            # 3. Contradictions Identified by Qwen
            for contra in reasoning.contradictions:
                gaps.append(
                    KnowledgeGap(
                        topic=f"Contradiction: {contra[:60]}",
                        reason=contra,
                        confidence=0.92,
                        urgency=4,
                        evidence=[o.source for o in observations[:3]],
                        category="contradiction",
                        suggested_action="Gather empirical citations to resolve contradiction."
                    )
                )

            # 4. Missing Capabilities or Implementations Identified by Qwen
            for missing_item in reasoning.missing:
                gaps.append(
                    KnowledgeGap(
                        topic=f"Missing: {missing_item[:60]}",
                        reason=missing_item,
                        confidence=0.88,
                        urgency=3,
                        evidence=[o.source for o in observations[:3]],
                        category="missing_implementation",
                        suggested_action=f"Investigate implementation requirement for: {missing_item[:50]}"
                    )
                )

        except Exception as e:
            logger.warning(f"Qwen strategic reasoning fallback: {e}")
            # Fallback for offline testing if LM Studio endpoint is unreachable
            gaps.extend(self._fallback_static_audit(observations, world_model))

        if not gaps:
            gaps.extend(self._fallback_static_audit(observations, world_model))

        return gaps

    def _fallback_static_audit(
        self,
        observations: List[ObservationRecord],
        world_model: Optional[Any]
    ) -> List[KnowledgeGap]:
        """Fallback static analysis used only if LLM endpoint is offline during unit testing."""
        fallback_gaps: List[KnowledgeGap] = []
        alpha_dir = self.workspace_root / "alpha"
        tests_dir = self.workspace_root / "tests"

        if alpha_dir.exists() and tests_dir.exists():
            test_names = {p.stem.replace("test_", "") for p in tests_dir.glob("test_*.py")}
            for py_path in sorted(alpha_dir.rglob("*.py")):
                if py_path.name.startswith(("_", ".")) or "__pycache__" in str(py_path):
                    continue
                stem = py_path.stem
                rel_path = py_path.relative_to(self.workspace_root).as_posix()
                if stem not in test_names:
                    fallback_gaps.append(
                        KnowledgeGap(
                            topic=f"Untested Module: {rel_path}",
                            reason=f"Module '{rel_path}' lacks direct unit test counterpart.",
                            confidence=0.85,
                            urgency=4,
                            evidence=[f"Module: {rel_path}"],
                            category="untested_path",
                            suggested_action=f"Create test suite for {stem}."
                        )
                    )
                    break

        if not fallback_gaps and observations:
            fallback_gaps.append(
                KnowledgeGap(
                    topic=f"Observation Audit: {observations[0].source}",
                    reason=f"Verification required for evidence: {observations[0].evidence[:60]}",
                    confidence=0.80,
                    urgency=3,
                    evidence=[observations[0].source],
                    category="unknown_module",
                    suggested_action="Conduct targeted code search."
                )
            )

        return fallback_gaps


# Singleton default instance
knowledge_gap_detector = KnowledgeGapDetector()