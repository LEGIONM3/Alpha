"""Model Capability Graph: Dynamic mapping of model competencies, failure modes, and evidence.

Part 3: Capability Graph
Tracks all 12 canonical capabilities:
- Coding, Debugging, Architecture, Research, Reasoning, Planning,
- Summarization, Extraction, Classification, Mathematics, Simulation, Prediction.
Each capability tracks:
confidence, score, sample size, failure modes, evidence, and historical trajectories.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field


class CapabilityScoreSnapshot(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    score: float
    confidence: float
    sample_size: int
    trigger_event: str = ""


class CapabilityNode(BaseModel):
    name: str
    score: float = Field(default=0.75, ge=0.0, le=1.0)
    confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    sample_size: int = 10
    failure_modes: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    history: List[CapabilityScoreSnapshot] = Field(default_factory=list)

    def record_evaluation(
        self,
        new_score: float,
        evidence_text: str,
        failure_mode: Optional[str] = None
    ) -> None:
        """Update capability score with Bayesian/exponential moving average."""
        # Moving average update
        alpha = 0.2
        self.score = round(self.score * (1.0 - alpha) + new_score * alpha, 3)
        self.sample_size += 1
        # Confidence increases asymptotically with sample size
        self.confidence = round(min(0.99, 0.5 + (self.sample_size / (self.sample_size + 20)) * 0.5), 3)

        if evidence_text and evidence_text not in self.evidence:
            self.evidence.append(evidence_text)
        if failure_mode and failure_mode not in self.failure_modes:
            self.failure_modes.append(failure_mode)

        self.history.append(
            CapabilityScoreSnapshot(
                score=self.score,
                confidence=self.confidence,
                sample_size=self.sample_size,
                trigger_event=evidence_text[:60]
            )
        )


class ModelCapabilityGraph:
    """Graph tracking the model's empirical proficiency profile and weaknesses over time."""

    CANONICAL_CAPABILITIES = [
        "Coding",
        "Debugging",
        "Architecture",
        "Research",
        "Reasoning",
        "Planning",
        "Summarization",
        "Extraction",
        "Classification",
        "Mathematics",
        "Simulation",
        "Prediction",
    ]

    def __init__(self, model_id: str = "default_model"):
        self.model_id = model_id
        self._capabilities: Dict[str, CapabilityNode] = {}
        self._initialize_canonical_graph()

    def _initialize_canonical_graph(self) -> None:
        """Seed baseline nodes for all 12 capabilities."""
        initial_priors = {
            "Coding": (0.86, 0.85, ["syntax errors on unclosed parens"], ["Passed 95% of basic code benchmarks"]),
            "Debugging": (0.80, 0.80, ["overlooks subtle race conditions"], ["Diagnosed off-by-one errors in unit tests"]),
            "Architecture": (0.84, 0.85, ["over-engineers simple tasks"], ["Structured clean 4-tier microservice architecture"]),
            "Research": (0.88, 0.90, ["cites outdated API parameters"], ["Extracted 5 papers with 90% keyword recall"]),
            "Reasoning": (0.78, 0.80, ["syllogism confusion with negation"], ["Resolved 8/10 transitive deduction puzzles"]),
            "Planning": (0.81, 0.82, ["omits rollback steps without prompts"], ["Formulated 5-step DAG with correct dependencies"]),
            "Summarization": (0.92, 0.95, ["rarely drops secondary constraints"], ["Summarized 5,000 token spec in 150 words"]),
            "Extraction": (0.91, 0.92, ["string truncation on nested JSON"], ["Extracted 100% of required schema fields"]),
            "Classification": (0.89, 0.90, ["edge-case confusion on boundary classes"], ["Achieved 91% F1 score on intent classification"]),
            "Mathematics": (0.70, 0.75, ["arithmetic errors on 4+ digit multiplication"], ["Solves basic algebra but struggles on mental math"]),
            "Simulation": (0.75, 0.78, ["counterfactual path omission"], ["Simulated downstream task failure correctly"]),
            "Prediction": (0.74, 0.75, ["overconfidence on high-variance outcomes"], ["Forecasted resource latency trends"]),
        }

        for cap_name in self.CANONICAL_CAPABILITIES:
            score, conf, fails, evs = initial_priors.get(cap_name, (0.75, 0.75, [], []))
            node = CapabilityNode(
                name=cap_name,
                score=score,
                confidence=conf,
                sample_size=15,
                failure_modes=list(fails),
                evidence=list(evs)
            )
            node.history.append(CapabilityScoreSnapshot(score=score, confidence=conf, sample_size=15, trigger_event="Initial baseline prior"))
            self._capabilities[cap_name.lower()] = node

    def get_capability(self, name: str) -> Optional[CapabilityNode]:
        return self._capabilities.get(name.lower())

    def update_capability(
        self,
        name: str,
        new_score: float,
        evidence: str,
        failure_mode: Optional[str] = None
    ) -> CapabilityNode:
        node = self._capabilities.get(name.lower())
        if not node:
            node = CapabilityNode(name=name, score=new_score, confidence=0.7, sample_size=1)
            self._capabilities[name.lower()] = node
        node.record_evaluation(new_score, evidence_text=evidence, failure_mode=failure_mode)
        return node

    def get_strongest_capabilities(self, top_k: int = 3) -> List[CapabilityNode]:
        nodes = list(self._capabilities.values())
        return sorted(nodes, key=lambda n: n.score, reverse=True)[:top_k]

    def get_weakest_capabilities(self, top_k: int = 3) -> List[CapabilityNode]:
        nodes = list(self._capabilities.values())
        return sorted(nodes, key=lambda n: n.score)[:top_k]

    def list_all(self) -> List[CapabilityNode]:
        return list(self._capabilities.values())

    def get_all_capabilities(self) -> Dict[str, CapabilityNode]:
        return self._capabilities

    def record_evaluation(
        self,
        capability_name: str,
        score: float,
        evidence: str = "",
        failure_mode: Optional[str] = None
    ) -> CapabilityNode:
        return self.update_capability(capability_name, score, evidence, failure_mode)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "capabilities": {k: v.model_dump() for k, v in self._capabilities.items()}
        }
