"""Ontology Validator: Schema, constraint, and semantic validation for Universal Entities."""

from typing import List, Dict, Any, Tuple
from alpha.world_model.ontology.entities import Entity, EntityType, LifecycleState


class ValidationResult:
    """Outcome of ontology validation."""
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __repr__(self) -> str:
        return f"<ValidationResult valid={self.is_valid} errors={len(self.errors)} warnings={len(self.warnings)}>"


class OntologyValidator:
    """Enforces integrity, bounded fields, and semantic consistency across entities."""

    def validate_entity(self, entity: Entity) -> ValidationResult:
        errors = []
        warnings = []

        # 1. Identity & Type check
        if not entity.id or not isinstance(entity.id, str):
            errors.append("Entity ID must be a non-empty string.")
        if not isinstance(entity.entity_type, EntityType):
            errors.append(f"Invalid entity type: {entity.entity_type}")

        # 2. Bounded metrics
        if not (0.0 <= entity.importance <= 1.0):
            errors.append(f"Importance {entity.importance} must be in [0.0, 1.0].")
        if not (0.0 <= entity.confidence <= 1.0):
            errors.append(f"Confidence {entity.confidence} must be in [0.0, 1.0].")

        # 3. Provenance check
        if not entity.provenance or not entity.provenance.creator_id:
            errors.append("Entity must contain valid provenance with creator_id.")

        # 4. Lifecycle consistency
        if entity.lifecycle_state == LifecycleState.DEAD and entity.confidence > 0.1:
            warnings.append(f"Entity is in DEAD lifecycle state but still retains confidence {entity.confidence}.")

        # 5. Type-specific constraints
        type_errors, type_warnings = self._validate_type_specific(entity)
        errors.extend(type_errors)
        warnings.extend(type_warnings)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_type_specific(self, entity: Entity) -> Tuple[List[str], List[str]]:
        errs, warns = [], []
        t = entity.entity_type

        if t == EntityType.BELIEF:
            stmt = getattr(entity, "statement", "")
            if not stmt:
                errs.append("BeliefEntity requires a non-empty 'statement'.")
            ev_ids = getattr(entity, "evidence_ids", [])
            # In Alpha, every belief must have evidence or provenance source
            if not ev_ids and not entity.provenance.source_ids:
                errs.append("No orphan beliefs: Belief must trace to evidence_ids or provenance source_ids.")

        elif t == EntityType.TASK:
            status = getattr(entity, "status", "")
            if not status:
                warns.append("TaskEntity has undefined status.")

        elif t == EntityType.RELATIONSHIP:
            src = getattr(entity, "source_id", "")
            tgt = getattr(entity, "target_id", "")
            if not src or not tgt:
                errs.append("RelationshipEntity must define source_id and target_id.")

        elif t == EntityType.PREDICTION:
            target = getattr(entity, "target_variable", "")
            if not target:
                warns.append("PredictionEntity missing target_variable.")

        return errs, warns
