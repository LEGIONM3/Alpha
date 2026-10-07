"""Meta-Knowledge Engine: Knowledge Gap Detector, Curiosity Engine, and Learning Priority Engine.

Part 15: Meta-Knowledge Engine
Alpha must know:
- What it knows
- What it believes
- What it doubts
- What it misunderstands
- What it should learn
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from alpha.world_model.ontology.registry import OntologyRegistry
from alpha.world_model.ontology.entities import EntityType
from alpha.world_model.epistemology.belief import BeliefSystem
from alpha.world_model.epistemology.uncertainty import UncertaintyLevel, UncertaintyEngine


class KnowledgeGap(BaseModel):
    """An identified void or unresolved ambiguity in Alpha's world model."""
    gap_id: str
    domain: str
    description: str
    severity: float = Field(ge=0.0, le=1.0)
    related_goal_ids: List[str] = Field(default_factory=list)
    suggested_action: str = ""


class LearningPriority(BaseModel):
    """A prioritized objective for civilizational or agentic study."""
    priority_id: str
    topic: str
    urgency_score: float = Field(ge=0.0, le=1.0)
    expected_gain: str = ""
    target_role: str = "researcher"


class KnowledgeGapDetector:
    """Scans the ontology and belief systems for missing dependencies and epistemic voids."""

    def __init__(self, ontology: OntologyRegistry, beliefs: BeliefSystem):
        self.ontology = ontology
        self.beliefs = beliefs

    def detect_gaps(self) -> List[KnowledgeGap]:
        gaps = []
        import uuid

        # 1. Detect goals without supporting active tasks
        goals = self.ontology.get_by_type(EntityType.GOAL)
        tasks = self.ontology.get_by_type(EntityType.TASK)
        task_goal_ids = {getattr(t, "goal_id", "") for t in tasks}

        for g in goals:
            if g.id not in task_goal_ids:
                gaps.append(KnowledgeGap(
                    gap_id=f"GAP_GOAL_{str(uuid.uuid4())[:6]}",
                    domain="planning",
                    description=f"Goal '{g.name}' has no active executing tasks mapped to it.",
                    severity=0.75,
                    related_goal_ids=[g.id],
                    suggested_action="Decompose goal into operational tasks."
                ))

        # 2. Detect beliefs with high contradiction or low confidence
        active_beliefs = self.beliefs.get_active_beliefs(min_confidence=0.0)
        for b in active_beliefs:
            if len(b.contradictions) > 0 and b.confidence > 0.3:
                gaps.append(KnowledgeGap(
                    gap_id=f"GAP_BELIEF_{str(uuid.uuid4())[:6]}",
                    domain=b.domain,
                    description=f"Belief '{b.statement[:50]}...' exhibits unresolved contradictions.",
                    severity=0.85,
                    suggested_action="Perform adversarial deliberation or run verification benchmark."
                ))

        # 3. Detect risks without mitigation plans
        risks = self.ontology.get_by_type(EntityType.RISK)
        for r in risks:
            if not getattr(r, "mitigation_plan", ""):
                gaps.append(KnowledgeGap(
                    gap_id=f"GAP_RISK_{str(uuid.uuid4())[:6]}",
                    domain="security",
                    description=f"Identified Risk '{r.name}' lacks a formulated mitigation plan.",
                    severity=getattr(r, "severity", 0.6),
                    suggested_action="Assign RiskAgent to draft mitigation strategy."
                ))

        return gaps


class CuriosityEngine:
    """Generates proactive research queries to expand understanding beyond reactive triggers."""

    def generate_curiosity_probes(self, gaps: List[KnowledgeGap]) -> List[Dict[str, Any]]:
        probes = []
        for g in gaps:
            probes.append({
                "probe_id": f"PROBE_{g.gap_id}",
                "inquiry": f"What mechanisms or empirical data resolve gap in {g.domain}: '{g.description}'?",
                "domain": g.domain,
                "urgency": g.severity,
                "recommended_tool": "browser_search" if g.domain == "research" else "sandbox_execute_code"
            })
        return probes


class LearningPriorityEngine:
    """Ranks what Alpha needs to acquire or verify next."""

    def rank_priorities(self, gaps: List[KnowledgeGap]) -> List[LearningPriority]:
        priorities = []
        import uuid
        for g in sorted(gaps, key=lambda x: x.severity, reverse=True):
            role = "researcher" if g.domain in ("research", "planning") else "validator"
            priorities.append(LearningPriority(
                priority_id=f"LP_{str(uuid.uuid4())[:6]}",
                topic=f"Resolve: {g.description}",
                urgency_score=g.severity,
                expected_gain=f"Closes critical gap in {g.domain}",
                target_role=role
            ))
        return priorities


class MetaKnowledgeEngine:
    """Master engine orchestrating epistemic self-awareness."""

    def __init__(self, ontology: OntologyRegistry, beliefs: BeliefSystem):
        self.ontology = ontology
        self.beliefs = beliefs
        self.gap_detector = KnowledgeGapDetector(ontology, beliefs)
        self.curiosity = CuriosityEngine()
        self.learning_priorities = LearningPriorityEngine()
        self.uncertainty = UncertaintyEngine()

    def evaluate_epistemic_overview(self) -> Dict[str, Any]:
        """Answer: What do I know, believe, doubt, misunderstand, and need to learn?"""
        active_beliefs = self.beliefs.get_active_beliefs(min_confidence=0.0)
        known = [b for b in active_beliefs if b.confidence >= 0.85]
        believed = [b for b in active_beliefs if 0.50 <= b.confidence < 0.85]
        doubted = [b for b in active_beliefs if 0.20 <= b.confidence < 0.50]
        misunderstood = [b for b in active_beliefs if len(b.contradictions) > 0]

        gaps = self.gap_detector.detect_gaps()
        priorities = self.learning_priorities.rank_priorities(gaps)

        return {
            "what_i_know": [{"statement": b.statement, "confidence": b.confidence} for b in known[:5]],
            "what_i_believe": [{"statement": b.statement, "confidence": b.confidence} for b in believed[:5]],
            "what_i_doubt": [{"statement": b.statement, "confidence": b.confidence} for b in doubted[:5]],
            "what_i_misunderstand_or_contradict": [{"statement": b.statement, "contradictions": len(b.contradictions)} for b in misunderstood[:5]],
            "knowledge_gaps_count": len(gaps),
            "top_learning_priorities": [p.model_dump() for p in priorities[:5]]
        }
