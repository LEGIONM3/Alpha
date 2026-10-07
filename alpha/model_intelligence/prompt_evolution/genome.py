"""Prompt Genome: Structural genetic representation of prompt configurations.

Part 4: Prompt Evolution System
Represents prompt architecture as an evolvable genome:
- Role directives
- Reasoning scaffolds
- Format constraints
- Negative instructions
- Few-shot styles
- Fitness tracking across generations
"""

from __future__ import annotations

import copy
import uuid
import time
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class ScaffoldStyle(str, Enum):
    DIRECT = "direct"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    PLAN_THEN_EXECUTE = "plan_then_execute"
    REFLECTION_LOOP = "reflection_loop"


class PromptGenome(BaseModel):
    """Genetic specification of a prompt scaffold."""
    genome_id: str = Field(default_factory=lambda: f"genome_{str(uuid.uuid4())[:8]}")
    domain: str = "general"
    generation: int = 1
    parent_ids: List[str] = Field(default_factory=list)
    role_directive: str = "You are an autonomous cognitive component in Project Alpha."
    scaffold_mode: str = "plan_then_execute"  # direct, chain_of_thought, plan_then_execute, reflection_loop
    format_constraint: str = "strict_json"     # strict_json, concise_text, delimited_blocks
    negative_instructions: List[str] = Field(default_factory=lambda: [
        "Do not include conversational filler or greetings.",
        "Do not output markdown code blocks if raw format is requested."
    ])
    include_deliberation_contract: bool = True
    temperature: float = 0.1
    fitness_score: float = 0.5
    evaluations_count: int = 0
    mutations_applied: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

    def assemble_prompt(self, instruction: str, context_block: Optional[str] = None) -> str:
        """Render the complete structured prompt from genetic attributes."""
        sections = [
            f"### SYSTEM ROLE\n{self.role_directive}",
        ]

        if self.scaffold_mode == "chain_of_thought":
            sections.append("### REASONING SCAFFOLD\nAnalyze constraints step-by-step before concluding.")
        elif self.scaffold_mode == "plan_then_execute":
            sections.append("### REASONING SCAFFOLD\nFormulate a strict 3-step execution plan, then output the final artifact.")
        elif self.scaffold_mode == "reflection_loop":
            sections.append("### REASONING SCAFFOLD\nDraft tentative answer, self-critique for edge cases, then produce hardened response.")

        if context_block and context_block.strip():
            sections.append(f"### GROUNDING CONTEXT\n{context_block.strip()}")

        sections.append(f"### IMMEDIATE TASK\n{instruction.strip()}")

        # Format and output constraints
        format_rules = [f"Output format contract: {self.format_constraint}"]
        format_rules.extend(self.negative_instructions)
        if self.include_deliberation_contract:
            format_rules.append("Ensure every factual claim is grounded in provided context.")
        sections.append("### CONSTRAINTS & OUTPUT CONTRACT\n" + "\n".join(f"- {r}" for r in format_rules))

        return "\n\n".join(sections)

    def mutate(self) -> PromptGenome:
        """Create a mutated descendant genome."""
        child = copy.deepcopy(self)
        child.genome_id = f"genome_{str(uuid.uuid4())[:8]}"
        child.generation = self.generation + 1
        child.parent_ids = [self.genome_id]
        child.evaluations_count = 0
        child.fitness_score = self.fitness_score * 0.95  # Initial slight decay until verified

        import random
        mutation_types = ["scaffold", "negative_constraint", "temperature", "role"]
        chosen = random.choice(mutation_types)

        if chosen == "scaffold":
            scaffolds = ["direct", "chain_of_thought", "plan_then_execute", "reflection_loop"]
            child.scaffold_mode = random.choice([s for s in scaffolds if s != self.scaffold_mode])
            child.mutations_applied.append(f"Mutated scaffold to {child.scaffold_mode}")

        elif chosen == "negative_constraint":
            new_negatives = [
                "Refuse to guess unknown facts; state UNKNOWN explicitly.",
                "Ensure mathematical computations are checked against sanity bounds.",
                "Strip all conversational apologies."
            ]
            cand = random.choice(new_negatives)
            if cand not in child.negative_instructions:
                child.negative_instructions.append(cand)
                child.mutations_applied.append(f"Added negative constraint: {cand[:30]}...")

        elif chosen == "temperature":
            child.temperature = round(max(0.05, min(0.7, self.temperature + random.choice([-0.05, 0.05]))), 2)
            child.mutations_applied.append(f"Adjusted temperature to {child.temperature}")

        else:
            child.role_directive += " Prioritize empirical verification and deterministic contracts."
            child.mutations_applied.append("Hardened role directive")

        return child
