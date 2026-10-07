"""Research Prioritization: Manages research backlogs, priorities, and knowledge gap rankings."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import ResearchProblem, ResearchQuestion


class KnowledgeGapEntry(BaseModel):
    gap_id: str
    domain: str
    target: str
    epistemic_value: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)
    feasibility: float = Field(ge=0.0, le=1.0)
    composite_rank_score: float = 0.0

    def compute_composite_score(self) -> float:
        # Multi-factor priority weighting
        self.composite_rank_score = round(
            0.35 * self.epistemic_value +
            0.25 * self.uncertainty +
            0.25 * self.impact +
            0.15 * self.feasibility,
            4
        )
        return self.composite_rank_score


class ResearchBacklog(BaseModel):
    problems: List[ResearchProblem] = Field(default_factory=list)
    questions: List[ResearchQuestion] = Field(default_factory=list)
    gap_rankings: List[KnowledgeGapEntry] = Field(default_factory=list)
    updated_at: float = Field(default_factory=time.time)


class ResearchPrioritizer:
    """Calculates optimal resource allocation across competing research questions."""

    def __init__(self):
        self._backlog = ResearchBacklog()
        self._lock = threading.RLock()

    def add_problem(self, problem: ResearchProblem) -> None:
        with self._lock:
            self._backlog.problems.append(problem)
            entry = KnowledgeGapEntry(
                gap_id=problem.problem_id,
                domain=problem.domain,
                target=problem.title,
                epistemic_value=problem.severity,
                uncertainty=problem.epistemic_uncertainty,
                impact=problem.expected_impact,
                feasibility=0.85
            )
            entry.compute_composite_score()
            self._backlog.gap_rankings.append(entry)
            self._sort_backlog()

    def add_question(self, question: ResearchQuestion) -> None:
        with self._lock:
            self._backlog.questions.append(question)
            entry = KnowledgeGapEntry(
                gap_id=question.question_id,
                domain=question.domain,
                target=question.question_text[:40],
                epistemic_value=question.epistemic_priority,
                uncertainty=0.75,
                impact=question.epistemic_priority,
                feasibility=question.investigability_score
            )
            entry.compute_composite_score()
            self._backlog.gap_rankings.append(entry)
            self._sort_backlog()

    def _sort_backlog(self) -> None:
        self._backlog.gap_rankings.sort(key=lambda g: g.composite_rank_score, reverse=True)
        self._backlog.questions.sort(key=lambda q: q.epistemic_priority, reverse=True)
        self._backlog.updated_at = time.time()

    def get_highest_priority_questions(self, limit: int = 5) -> List[ResearchQuestion]:
        with self._lock:
            return self._backlog.questions[:limit]

    def get_ranked_knowledge_gaps(self, limit: int = 10) -> List[KnowledgeGapEntry]:
        with self._lock:
            return self._backlog.gap_rankings[:limit]

    def get_backlog_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_problems": len(self._backlog.problems),
                "total_questions": len(self._backlog.questions),
                "total_gaps_ranked": len(self._backlog.gap_rankings),
                "top_gap": self._backlog.gap_rankings[0].target if self._backlog.gap_rankings else None,
                "top_priority_score": self._backlog.gap_rankings[0].composite_rank_score if self._backlog.gap_rankings else 0.0
            }
