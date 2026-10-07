"""Ontology Evolution Engine: Schema migrations, entity transformations, merging, and upgrades."""

from typing import Dict, Any, List, Optional
from alpha.world_model.ontology.entities import Entity, EntityType, LifecycleState, ConceptEntity


class OntologyEvolutionEngine:
    """Manages structural mutations, conceptual generalization, schema migration, and lifecycle evolution."""

    def __init__(self):
        self.migration_rules: List[Dict[str, Any]] = []

    def register_migration(self, rule_name: str, transform_fn: Any) -> None:
        """Register a migration transformation function."""
        self.migration_rules.append({"name": rule_name, "fn": transform_fn})

    def migrate_entity(self, entity: Entity) -> Entity:
        """Apply registered migrations to an entity, preserving version history."""
        for rule in self.migration_rules:
            entity.snapshot(summary=f"Migration applied: {rule['name']}", changed_by="evolution_engine")
            rule["fn"](entity)
        return entity

    def merge_entities(
        self,
        primary: Entity,
        secondary: Entity,
        merged_name: Optional[str] = None
    ) -> Entity:
        """Merge a secondary entity into a primary entity, retiring the secondary."""
        primary.snapshot(summary=f"Merged with entity {secondary.id}", changed_by="evolution_engine")
        if merged_name:
            primary.name = merged_name

        # Merge attributes and metadata
        for k, v in secondary.attributes.items():
            if k not in primary.attributes:
                primary.attributes[k] = v

        for k, v in secondary.metadata.items():
            if k not in primary.metadata:
                primary.metadata[k] = v

        # Combine importance and confidence via weighted blend
        primary.importance = max(primary.importance, secondary.importance)
        primary.confidence = (primary.confidence + secondary.confidence) / 2.0

        # Append secondary ID into provenance sources
        if secondary.id not in primary.provenance.source_ids:
            primary.provenance.source_ids.append(secondary.id)

        # Deprecate/retire secondary entity
        secondary.transition_lifecycle(
            LifecycleState.DEPRECATED,
            reason=f"Merged into primary entity {primary.id}"
        )
        return primary

    def abstract_to_concept(self, entities: List[Entity], concept_name: str, definition: str) -> ConceptEntity:
        """Evolve a set of concrete entities into a higher-order ConceptEntity."""
        exemplar_ids = [e.id for e in entities]
        avg_importance = sum(e.importance for e in entities) / max(1, len(entities))
        avg_confidence = sum(e.confidence for e in entities) / max(1, len(entities))

        concept = ConceptEntity(
            name=concept_name,
            definition=definition,
            abstraction_depth=2,
            exemplar_ids=exemplar_ids,
            importance=round(avg_importance, 3),
            confidence=round(avg_confidence, 3),
            metadata={"evolved_from_count": len(entities)}
        )
        return concept
