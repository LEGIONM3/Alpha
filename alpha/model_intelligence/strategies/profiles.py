"""Reasoning Strategy Profiles: Definitions of cognitive modes for model amplification."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ReasoningMode(str, Enum):
    ARCHITECT = "architect"
    RESEARCH = "research"
    ANALYST = "analyst"
    CODING = "coding"
    PLANNING = "planning"
    SIMULATION = "simulation"
    CRITIC = "critic"
    VERIFICATION = "verification"
    TEACHER = "teacher"
    BUILDER = "builder"


class ReasoningProfile(BaseModel):
    mode: ReasoningMode
    title: str
    description: str
    system_scaffold: str
    temperature: float = 0.2
    thought_phases: List[str] = Field(default_factory=list)
    recommended_tools: List[str] = Field(default_factory=list)
    context_priorities: List[str] = Field(default_factory=list)
    verification_required: bool = False
    simulation_required: bool = False

    def build_system_prompt(self, base_role_prompt: Optional[str] = None) -> str:
        scaffold_lines = [
            f"=== COGNITIVE MODE: {self.title.upper()} ===",
            self.description,
            "\n### OPERATIONAL MANDATE:",
            self.system_scaffold,
            "\n### MANDATORY REASONING PHASES:",
        ]
        for i, phase in enumerate(self.thought_phases, 1):
            scaffold_lines.append(f"{i}. {phase}")

        if base_role_prompt:
            scaffold_lines.insert(0, base_role_prompt.strip() + "\n")

        return "\n".join(scaffold_lines)
