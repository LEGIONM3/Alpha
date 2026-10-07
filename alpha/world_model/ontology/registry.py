"""Ontology Registry: Storage, indexing, retrieval, and validation of all Universal Entities."""

import threading
from typing import Dict, List, Optional, Any
from alpha.world_model.ontology.entities import Entity, EntityType, LifecycleState
from alpha.world_model.ontology.validator import OntologyValidator, ValidationResult
from alpha.world_model.ontology.versioning import OntologyVersionManager
from alpha.world_model.ontology.evolution import OntologyEvolutionEngine


class OntologyRegistry:
    """Central repository and indexing system for all Universal Entities."""

    def __init__(self, validator: Optional[OntologyValidator] = None):
        self._entities: Dict[str, Entity] = {}
        self._by_type: Dict[EntityType, List[str]] = {t: [] for t in EntityType}
        self._by_name: Dict[str, str] = {}
        self._lock = threading.RLock()
        self.validator = validator or OntologyValidator()
        self.versioning = OntologyVersionManager()
        self.evolution = OntologyEvolutionEngine()

    def register(self, entity: Entity, validate: bool = True) -> Entity:
        """Register an entity into the ontology registry with validation."""
        with self._lock:
            if validate:
                res = self.validator.validate_entity(entity)
                if not res.is_valid:
                    raise ValueError(f"Ontology validation failed for entity '{entity.name}': {res.errors}")

            # Store entity
            self._entities[entity.id] = entity
            if entity.id not in self._by_type[entity.entity_type]:
                self._by_type[entity.entity_type].append(entity.id)
            self._by_name[entity.name.lower()] = entity.id
            return entity

    def get(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by unique ID."""
        with self._lock:
            return self._entities.get(entity_id)

    def get_by_name(self, name: str) -> Optional[Entity]:
        """Retrieve an entity by unique or primary name."""
        with self._lock:
            eid = self._by_name.get(name.lower())
            return self._entities.get(eid) if eid else None

    def get_by_type(self, entity_type: EntityType, state: Optional[LifecycleState] = None) -> List[Entity]:
        """Retrieve entities filtered by EntityType and optional LifecycleState."""
        with self._lock:
            eids = self._by_type.get(entity_type, [])
            results = [self._entities[eid] for eid in eids if eid in self._entities]
            if state:
                results = [e for e in results if e.lifecycle_state == state]
            return results

    def get_all(self, state: Optional[LifecycleState] = None) -> List[Entity]:
        """Retrieve all registered entities."""
        with self._lock:
            all_e = list(self._entities.values())
            if state:
                return [e for e in all_e if e.lifecycle_state == state]
            return all_e

    def update(self, entity: Entity, summary: str = "update", changed_by: str = "system") -> Entity:
        """Update an entity with version recording."""
        with self._lock:
            if entity.id not in self._entities:
                raise KeyError(f"Entity with ID {entity.id} does not exist.")
            self.versioning.record_version(entity, summary=summary, changed_by=changed_by)
            self._entities[entity.id] = entity
            self._by_name[entity.name.lower()] = entity.id
            return entity

    def remove(self, entity_id: str) -> bool:
        """Remove an entity from the registry."""
        with self._lock:
            entity = self._entities.pop(entity_id, None)
            if not entity:
                return False
            if entity_id in self._by_type[entity.entity_type]:
                self._by_type[entity.entity_type].remove(entity_id)
            self._by_name.pop(entity.name.lower(), None)
            return True

    def search(
        self,
        query: str,
        entity_type: Optional[EntityType] = None,
        min_importance: float = 0.0,
        min_confidence: float = 0.0
    ) -> List[Entity]:
        """Textual and metric search across entities."""
        q = query.lower()
        with self._lock:
            candidates = self.get_by_type(entity_type) if entity_type else list(self._entities.values())
            matched = []
            for e in candidates:
                if e.importance < min_importance or e.confidence < min_confidence:
                    continue
                if q in e.name.lower() or any(q in str(v).lower() for v in e.attributes.values()):
                    matched.append(e)
            matched.sort(key=lambda x: (x.importance * 0.5 + x.confidence * 0.5), reverse=True)
            return matched

    def count(self) -> int:
        with self._lock:
            return len(self._entities)

    def count_by_type(self) -> Dict[str, int]:
        with self._lock:
            return {t.value: len(self._by_type[t]) for t in EntityType}
