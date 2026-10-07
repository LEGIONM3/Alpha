"""Real Question Generator for Project Alpha.

Transforms detected KnowledgeGaps into actionable, empirical ResearchQuestions
prioritized by urgency and domain difficulty.
"""

from typing import List
from pydantic import BaseModel, Field
from alpha.knowledge.detector import KnowledgeGap


class ResearchQuestion(BaseModel):
    """A specific, actionable query derived from a knowledge gap."""
    question: str
    source_gap: str
    difficulty: int = Field(default=3, ge=1, le=5)


class QuestionGenerator:
    """Transforms abstract knowledge gaps into precise, actionable research questions

    suitable for empirical investigation by the ResearchEngine.
    """

    def __init__(self):
        pass

    def generate_questions(self, gaps: List[KnowledgeGap]) -> List[ResearchQuestion]:
        """Converts a list of detected knowledge gaps into actionable queries."""
        questions: List[ResearchQuestion] = []

        for gap in gaps:
            cat = getattr(gap, "category", "")

            if cat == "untested_path":
                mod_name = gap.topic.replace("Untested Module: ", "")
                q_text = f"What are the interface invariants and public functions defined in {mod_name}?"
            elif cat == "unknown_module":
                subsys = gap.topic.replace("Unknown Subsystem: ", "")
                q_text = f"What is the architectural purpose and subsystem role of {subsys} in Project Alpha?"
            elif cat == "missing_causal_link":
                pair = gap.topic.replace("Missing Causal Link: ", "")
                q_text = f"What causal dependency mechanism connects {pair} in runtime execution?"
            elif cat == "low_confidence_belief":
                q_text = f"What verifiable empirical evidence corroborates or refutes the belief: {gap.topic}?"
            elif cat == "missing_documentation":
                mod_name = gap.topic.replace("Missing Module Documentation: ", "")
                q_text = f"What classes, functions, and responsibilities are implemented in {mod_name}?"
            elif cat == "dead_code":
                q_text = f"Is the symbol in {gap.topic} referenced by any external tests or modules?"
            elif cat == "unused_system":
                q_text = f"How should {gap.topic} be integrated into the Alpha tools registry or boot sequence?"
            elif "Causal Graph Completeness" in gap.topic:
                q_text = f"What are the established methods for causal discovery concerning {gap.reason}?"
            elif "Low Confidence Data Point" in gap.topic:
                q_text = f"Can existing documentation refute the finding that '{gap.topic}' holds true?"
            else:
                q_text = f"Investigate the mechanism underlying: {gap.reason} related to topic '{gap.topic}'."

            questions.append(
                ResearchQuestion(
                    question=q_text,
                    source_gap=f"{gap.topic} ({gap.urgency})",
                    difficulty=min(5, max(1, gap.urgency))
                )
            )

        return questions


# Singleton default instance
question_generator = QuestionGenerator()