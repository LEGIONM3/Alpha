"""Concept Formation Engine: Concept Discovery and Exemplar Generalization.

Part 10: Concept Formation
Transforms exemplar entities into generalized concepts:
- Dog, Wolf, Fox -> Canine
- Redis, Postgres, Qdrant -> Data Storage Systems
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from alpha.world_model.ontology.entities import Entity, ConceptEntity


class ConceptDiscoveryEngine:
    """Discovers recurring patterns among concrete entities and forms generalized concepts."""

    def form_concept_from_exemplars(
        self,
        concept_name: str,
        definition: str,
        exemplar_entities: List[Entity],
        abstraction_depth: int = 1
    ) -> ConceptEntity:
        """Create a ConceptEntity synthesizing a set of concrete exemplars."""
        exemplar_ids = [e.id for e in exemplar_entities]
        avg_importance = sum(e.importance for e in exemplar_entities) / max(1, len(exemplar_entities))
        avg_confidence = sum(e.confidence for e in exemplar_entities) / max(1, len(exemplar_entities))

        # Collect common attributes
        shared_attributes = {}
        if exemplar_entities:
            first = exemplar_entities[0].attributes
            for k, v in first.items():
                if all(e.attributes.get(k) == v for e in exemplar_entities[1:]):
                    shared_attributes[k] = v

        concept = ConceptEntity(
            name=concept_name,
            definition=definition,
            abstraction_depth=abstraction_depth,
            exemplar_ids=exemplar_ids,
            importance=round(avg_importance, 3),
            confidence=round(avg_confidence, 3),
            attributes={
                "shared_invariants": shared_attributes,
                "exemplar_names": [e.name for e in exemplar_entities]
            }
        )
        return concept

    def discover_concepts_from_clusters(
        self,
        entities: List[Entity],
        group_key: str = "category"
    ) -> List[ConceptEntity]:
        """Automatically group entities by a key attribute and form concepts."""
        groups = defaultdict(list)
        for e in entities:
            val = e.attributes.get(group_key, e.entity_type.value)
            groups[val].append(e)

        concepts = []
        for cat_name, members in groups.items():
            if len(members) >= 2:
                names_str = ", ".join(m.name for m in members[:4])
                c = self.form_concept_from_exemplars(
                    concept_name=f"{cat_name.title()} Systems" if not cat_name.endswith("s") else cat_name.title(),
                    definition=f"Higher-order concept discovered from instances: {names_str}.",
                    exemplar_entities=members,
                    abstraction_depth=2
                )
                concepts.append(c)
        return concepts
