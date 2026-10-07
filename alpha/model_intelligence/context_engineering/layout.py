"""Context Layout Engine: Structured sectioning, ordering, and template framing."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ContextLayout(BaseModel):
    world_model_injections: List[str] = Field(default_factory=list)
    epistemic_beliefs: List[str] = Field(default_factory=list)
    memory_injections: List[str] = Field(default_factory=list)
    reflection_lessons: List[str] = Field(default_factory=list)
    few_shot_examples: List[str] = Field(default_factory=list)

    def render(self) -> str:
        blocks = []
        if self.world_model_injections:
            blocks.append("### WORLD MODEL STATE & AXIOMS\n" + "\n".join(f"- {w}" for w in self.world_model_injections))
        if self.epistemic_beliefs:
            blocks.append("### GROUNDED BELIEFS (HIGH CONFIDENCE)\n" + "\n".join(f"- {b}" for b in self.epistemic_beliefs))
        if self.reflection_lessons:
            blocks.append("### PREVIOUS LESSONS LEARNED & RETRIES\n" + "\n".join(f"- {l}" for l in self.reflection_lessons))
        if self.memory_injections:
            blocks.append("### RELEVANT EPISODIC MEMORY\n" + "\n".join(f"- {m}" for m in self.memory_injections))
        if self.few_shot_examples:
            blocks.append("### REFERENCE EXEMPLARS\n" + "\n\n".join(self.few_shot_examples))
        return "\n\n".join(blocks)


class ContextLayoutEngine:
    """Arranges disparate cognitive signals into optimal sequential prompt layouts."""

    def assemble_layout(
        self,
        world_model_items: Optional[List[str]] = None,
        beliefs: Optional[List[str]] = None,
        memories: Optional[List[str]] = None,
        reflections: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> ContextLayout:
        return ContextLayout(
            world_model_injections=world_model_items or [],
            epistemic_beliefs=beliefs or [],
            memory_injections=memories or [],
            reflection_lessons=reflections or [],
            few_shot_examples=examples or []
        )
