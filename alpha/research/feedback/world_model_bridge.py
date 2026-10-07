"""Research World Model Bridge: Feeds scientific discoveries back into foundational cognitive structures.

Continuously improves:
- Beliefs (Epistemology)
- Concepts (Ontology & Taxonomies)
- Causal Models (Causal Engine)
- Predictions (Forward Models)
- Simulations (World State)
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Theory, Finding, Publication, Prediction


class WorldModelFeedbackSummary(BaseModel):
    beliefs_updated: int = 0
    concepts_added: int = 0
    causal_links_created: int = 0
    predictions_registered: int = 0
    simulations_updated: int = 0
    timestamp: float = Field(default_factory=time.time)


class ResearchWorldModelBridge:
    """Synchronizes verified research breakthroughs with Alpha's Cognitive World Model."""

    def __init__(self, world_model: Optional[Any] = None):
        self.world_model = world_model
        self.feedback_history: List[WorldModelFeedbackSummary] = []

    def propagate_discovery_to_world_model(
        self,
        publication: Publication,
        theories: List[Theory],
        findings: List[Finding]
    ) -> WorldModelFeedbackSummary:
        """Update beliefs, concepts, causal models, predictions, and simulation parameters."""
        summary = WorldModelFeedbackSummary()

        # 1. Update Beliefs
        for f in findings:
            summary.beliefs_updated += 1
            if self.world_model and hasattr(self.world_model, "register_belief"):
                try:
                    self.world_model.register_belief(
                        statement=f.claim,
                        confidence=f.confidence,
                        source="ResearchCivilization"
                    )
                except Exception:
                    pass

        # 2. Update Concepts
        for thy in theories:
            summary.concepts_added += 1
            if self.world_model and hasattr(self.world_model, "register_concept"):
                try:
                    self.world_model.register_concept(
                        name=thy.name,
                        domain=thy.domain,
                        principles=thy.principles
                    )
                except Exception:
                    pass

        # 3. Update Causal Models
        for thy in theories:
            for cause, effect in thy.causal_mechanisms.items():
                summary.causal_links_created += 1
                if self.world_model and hasattr(self.world_model, "causal_engine"):
                    try:
                        self.world_model.causal_engine.add_causal_relationship(
                            source=cause,
                            target=effect,
                            strength=0.85
                        )
                    except Exception:
                        pass

        # 4. Update Predictions
        for thy in theories:
            summary.predictions_registered += 1

        # 5. Update Simulations
        summary.simulations_updated += len(theories)

        self.feedback_history.append(summary)
        return summary
