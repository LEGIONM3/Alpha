"""Hypothesis Agent: Autonomous scientific theorist formulating creative hypotheses."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from alpha.research.agents.base import ScientificAgentBase
from alpha.research.entities import Hypothesis, ResearchQuestion
from alpha.research.hypotheses.generator import HypothesisGenerator


class HypothesisAgent(ScientificAgentBase):
    """Specialized discovery agent formulating novel, competing, and alternative hypotheses."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id=agent_id, role_name="HypothesisAgent")
        self.generator = HypothesisGenerator()

    def propose_hypothesis(self, question: ResearchQuestion) -> Hypothesis:
        """Formulate a novel hypothesis addressing a scientific question."""
        hyp = self.generator.generate_novel_hypothesis(question, proposer=self.agent_id)
        self.log_action("propose_hypothesis", target_id=hyp.hypothesis_id, question_id=question.question_id)
        return hyp

    def propose_rivals(self, base_hypothesis: Hypothesis, count: int = 2) -> List[Hypothesis]:
        """Formulate competing rival hypotheses to stress-test the initial idea."""
        rivals = self.generator.generate_competing_hypotheses(base_hypothesis, count=count)
        self.log_action("propose_rivals", target_id=base_hypothesis.hypothesis_id, rival_count=len(rivals))
        return rivals
