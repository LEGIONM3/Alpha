"""Ontology Version Manager: Version tracking, snapshots, diffs, and state rollbacks."""

import copy
from typing import Dict, Any, List, Optional
from alpha.world_model.ontology.entities import Entity, EntityVersion


class OntologyVersionManager:
    """Tracks historical versions of entities, computes diffs, and performs rollback operations."""

    def record_version(self, entity: Entity, summary: str = "update", changed_by: str = "system") -> EntityVersion:
        """Create and append a new version snapshot to an entity."""
        return entity.snapshot(summary=summary, changed_by=changed_by)

    def get_history(self, entity: Entity) -> List[EntityVersion]:
        """Return the full version history for an entity."""
        return entity.version_history

    def compute_diff(self, entity: Entity, v1: int, v2: int) -> Dict[str, Any]:
        """Compute the attribute and metric diff between two version numbers."""
        snap1 = None
        snap2 = None

        for snap in entity.version_history:
            if snap.version_number == v1:
                snap1 = snap.snapshot
            if snap.version_number == v2:
                snap2 = snap.snapshot

        if v1 == entity.version:
            snap1 = entity.model_dump(exclude={"version_history"})
        if v2 == entity.version:
            snap2 = entity.model_dump(exclude={"version_history"})

        if not snap1 or not snap2:
            return {"error": f"One or both versions not found: {v1}, {v2}"}

        added = {k: v for k, v in snap2.items() if k not in snap1}
        removed = {k: v for k, v in snap1.items() if k not in snap2}
        modified = {k: {"from": snap1[k], "to": snap2[k]} for k in snap1 if k in snap2 and snap1[k] != snap2[k]}

        return {
            "entity_id": entity.id,
            "version_from": v1,
            "version_to": v2,
            "added": added,
            "removed": removed,
            "modified": modified
        }

    def rollback(self, entity: Entity, target_version: int) -> bool:
        """Roll back an entity's mutable fields to a previous version snapshot."""
        target_snap = None
        for snap in entity.version_history:
            if snap.version_number == target_version:
                target_snap = snap
                break

        if not target_snap:
            return False

        # Record current before rolling back
        entity.snapshot(summary=f"Rollback to v{target_version}", changed_by="version_manager")
        for k, v in target_snap.snapshot.items():
            if hasattr(entity, k) and k not in ("id", "entity_type", "version_history", "version"):
                setattr(entity, k, copy.deepcopy(v))
        return True
