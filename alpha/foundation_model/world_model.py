"""World Model — The Foundation Model's representation of reality.

This module implements the agent's cognitive world model: a dynamic, evolving
representation of its environment built from observations, memory retrieval,
and evidence accumulation over time.

The world model answers four fundamental questions:
1. What exists? (Ontology)
2. How is it related? (Causal structure)  
3. When did things happen? (Temporal grounding)
4. Why do I believe what I believe? (Epistemic provenance)

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                     WORLD MODEL                                  │
│                                                                  │
│  ┌──────────────────┐                                           │
│  │   Ontology       │  — Entity types, relationships            │
│  │   (what exists)  │                                          │
│  └────────┬─────────┘                                           │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │   Entities       │  — Concrete instances (files, tools...)   │
│  │   & Facts        │                                          │
│  └────────┬─────────┘                                           │
│           ▼                                                      │
│  ┌──────────────────┐           ┌──────────────────┐            │
│  │  Causal Graph    │◄──────►   │  Temporal Timeline│            │
│  │  (cause→effect)  │           │  (when it happened)│          │
│  └────────┬─────────┘           └──────────────────┘            │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │   Belief Layer   │  — Confidence-weighted beliefs           │
│  │   (with evidence)│                                          │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘

Author: Gemini (Alpha Principal Systems Engineer)
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Entity(BaseModel):
    """A concrete entity in the world model.

    Examples of entities: a file, a tool, a process, a concept, a goal.
    Each entity carries metadata about its state, relationships, and provenance.
    """
    id: str = Field(default_factory=lambda: f"entity_{utc_now().strftime('%Y%m%d%H%M%S%f')}")
    name: str
    
    # What kind of thing is this? (ontology)
    type: str = "unknown"  # file, tool, concept, goal, process, etc.
    
    # The agent's current belief about this entity
    description: Optional[str] = None
    
    # Attributes — properties we know about the entity
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Relationships to other entities
    related_to: List[Tuple[str, str]] = field(default_factory=list)  # (other_id, relationship_type)
    
    # Epistemic metadata — how confident are we about this entity?
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    last_observed_at: datetime = Field(default_factory=utc_now)
    evidence_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "name": "filesystem_scan",
                "type": "tool",
                "description": "A tool that scans directory structures",
                "attributes": {"capabilities": ["discovery"], "safe": True},
                "confidence": 0.95,
            }
        }


class WorldModel:
    """The agent's cognitive model of its environment and knowledge base.

    The world model is the Foundation Model's persistent understanding of reality.
    It grows through:
    
    - Observation: Tools provide raw observations (files exist, tools work)
    - Memory retrieval: Related past experiences are recalled as relevant context
    - Evidence accumulation: Confidence in beliefs updates with new evidence
    
    Key design decisions:
    - Entities are distinct from the agent's goals — they exist independently
    - Relationships are directional and typed (A *depends_on* B is not B *depends_on* A)
    - All knowledge carries confidence scores — nothing is assumed certain
    """

    # Entity type registry (ontology)
    ENTITY_TYPES = [
        "file",          # A file in the filesystem
        "directory",     # A directory/folder
        "tool",          # An executable capability
        "concept",       # An abstract idea or domain knowledge
        "process",       # A running system/process
        "goal",          # A goal the agent is pursuing
        "task",          # A unit of work
        "capability",    # What the agent can do
        "constraint",    # Something that limits action
        "resource",      # A resource (CPU, disk space, time)
        "knowledge_base",# The knowledge store itself
    ]

    def __init__(self, workspace_root: Optional[Path] = None):
        self._workspace_root = Path(workspace_root) if workspace_root else Path.cwd() / "alpha"
        
        # Core world state — the agent's model of reality
        self.entities: Dict[str, Entity] = {}
        self.entity_index: Dict[str, str] = {}  # name -> entity_id (for fast lookup by name)
        
        # Relationships indexed for graph queries
        self._reverse_relationships: Dict[str, List[Tuple[str, str]]] = {}

        # Evidence registry — tracks what evidence supports each belief
        self.evidence_registry: Dict[str, List[Dict[str, Any]]] = {}

    def add_entity(self, name: str, entity_type: Optional[str] = None) -> Entity:
        """Register a new entity in the world model."""
        
        entity_id = f"entity_{name.replace(' ', '_')}"  # Simple deterministic ID
        
        if entity_id not in self.entities:
            entity = Entity(
                id=entity_id,
                name=name,
                type=entity_type or "unknown",
            )
            self.entities[entity_id] = entity
            
            # Index by name for easy lookup
            self.entity_index[name.lower()] = entity_id
            
        return self.entities[entity_id]

    def observe(self, observation: str, 
               related_entity_id: Optional[str] = None) -> Entity:
        """Observe something in the world.
        
        This is the primary mechanism for updating the world model from raw perception.
        The agent observes "there exists a file at path X" and creates/updates
        an entity with that information.

        Args:
            observation: A natural language description of what was observed
            related_entity_id: Optional ID of another entity this observation is about
            
        Returns:
            The Entity that was created or updated.
        """
        
        # Parse the observation to extract entity info
        entity_name = self._extract_entity_from_observation(observation)
        
        if not entity_name:
            return None
        
        entity = self.entities.get(entity_id := f"entity_{entity_name.replace(' ', '_')}")
        
        if not entity:
            # Create new entity from observation
            entity_type = self._infer_entity_type_from_observation(observation)
            entity = Entity(
                id=entity_id,
                name=entity_name,
                type=entity_type,
                description=self._summarize_observation(observation),
            )
            self.entities[entity_id] = entity
            
        else:
            # Update existing entity with new observation
            entity.last_observed_at = utc_now()
            if "not found" in observation.lower():
                return None  # Observation refutes existence

        # Link to related entities if provided
        if related_entity_id and related_entity_id in self.entities:
            relationship_type = self._infer_relationship(observation, related_entity_id)
            self._add_bidirectional_relationship(related_entity_id, entity_id, relationship_type)

        return entity

    def _extract_entity_from_observation(self, observation: str) -> Optional[str]:
        """Extract an entity name from a natural language observation."""
        
        # Simple heuristic extraction
        keywords = ["file", "directory", "tool", "capability"]
        
        for kw in keywords:
            if f"{kw} '{observation[:50]}'" in observation.lower() or \
               f"{kw} \"{observation[:50]}\"".lower() in observation.lower():
                # Try to extract the entity name from context
                return observation.split("'")[1].strip().replace('"', '') if "'" in observation else observation.split('"')[1].strip()

        # Fallback: use the entire observation as the entity description
        # and rely on relationships for disambiguation
        return None

    def _infer_entity_type_from_observation(self, observation: str) -> str:
        """Infer what type of entity an observation describes."""
        
        obs_lower = observation.lower()
        
        if "file" in obs_lower or ".py" in obs_lower or ".md" in obs_lower:
            return "file"
        elif "tool" in obs_lower or "capability" in obs_lower or "execute" in obs_lower:
            return "tool"
        elif "concept" in obs_lower or "idea" in obs_lower or "knowledge" in obs_lower:
            return "concept"
        
        return "unknown"

    def _summarize_observation(self, observation: str) -> str:
        """Create a concise summary of an observation."""
        # Simple truncation with context preservation
        if len(observation) > 200:
            return f"[Observation]: {observation[:197]}..."
        return f"[Observed at {utc_now()}] {observation}"

    def _add_bidirectional_relationship(self, source_id: str, target_id: str, 
                                         relationship_type: str) -> None:
        """Add a directional relationship between two entities (bidirectionally indexed)."""
        
        # Forward direction
        if source_id not in self._reverse_relationships:
            self._reverse_relationships[source_id] = []
        self._reverse_relationships[source_id].append((target_id, relationship_type))

        # Reverse lookup index
        if target_id not in self._reverse_relationships:
            self._reverse_relationships[target_id] = []
        
    def _infer_relationship(self, observation_text: str, related_entity_name: str) -> str:
        """Infer the relationship type from context."""
        
        obs_lower = observation_text.lower()
        
        if "uses" in obs_lower or "employs" in obs_lower:
            return "uses"
        elif "requires" in obs_lower:
            return "requires"
        elif "depends on" in obs_lower or "based on" in obs_lower:
            return "depends_on"
        
        # Default relationship
        return "related_to"

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Look up an entity by its natural language name."""
        lower_name = name.lower()
        for key in self.entity_index:
            if key in lower_name or lower_name in key:
                return self.entities.get(self.entity_index[key])
        
        # Direct lookup fallback
        for entity in self.entities.values():
            if name.lower() == entity.name.lower():
                return entity
        
        return None

    def get_related_entities(self, entity_id: str) -> List[Entity]:
        """Get all entities related to a given entity."""
        relationships = self._reverse_relationships.get(entity_id, [])
        
        result = []
        for target_id, _ in relationships:
            if target_id in self.entities:
                result.append(self.entities[target_id])
        
        return result

    def get_causal_chain(self, cause_entity_id: str) -> List[str]:
        """Trace the causal chain starting from a given entity.
        
        Returns a list of entity IDs forming a causal chain (cause → effect).
        """
        # Simple breadth-first traversal of relationships
        visited = set()
        chain = []
        queue = [cause_entity_id]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            chain.append(current)

            for target, rel_type in self._reverse_relationships.get(current, []):
                # Only follow "causes" or "enables" directionally
                if rel_type in ("causes", "enables", "produces"):
                    queue.append(target)

        return chain

    def add_evidence(self, belief_id: str, evidence_text: str, 
                    strength: float = 0.5) -> None:
        """Add evidence that supports a given belief."""
        
        if belief_id not in self.evidence_registry:
            self.evidence_registry[belief_id] = []

        # Check for contradictory evidence (simple heuristic)
        existing_evidence = self.evidence_registry.get(belief_id, [])
        has_contradiction = any(
            e.get("strength", 0.5) < -0.3 
            for e in existing_evidence if "contradictory" in str(e).lower()
        )

        self.evidence_registry[belief_id].append({
            "text": evidence_text,
            "strength": strength,
            "added_at": utc_now().isoformat(),
        })

        # Update belief confidence (Bayesian-like update)
        current_evidence = self.evidence_registry.get(belief_id, [])
        total_strength = sum(e.get("strength", 0.5) for e in current_evidence)
        
        new_confidence = min(1.0, max(-0.3, 
            (total_strength + strength) / max(len(current_evidence), 1)))

        # Update the entity's confidence if it exists
        if belief_id.startswith("entity_"):
            entity = self.entities.get(belief_id)
            if entity:
                entity.confidence = new_confidence

    def get_belief_with_evidence(self, belief_id: str) -> Dict[str, Any]:
        """Get a belief along with all supporting evidence."""
        
        return {
            "belief_id": belief_id,
            "confidence": self._compute_belief_confidence(belief_id),
            "evidence_count": len(self.evidence_registry.get(belief_id, [])),
            "evidence_summary": [e["text"][:100] + "..." for e in 
                                self.evidence_registry.get(belief_id, [])[-3:]],
        }

    def _compute_belief_confidence(self, belief_id: str) -> float:
        """Compute confidence score based on evidence."""
        evidence = self.evidence_registry.get(belief_id, [])
        
        if not evidence:
            return 0.5  # Unformed beliefs are maximally uncertain
        
        # Weight recent evidence more heavily
        now = utc_now()
        weighted_strength = sum(
            e["strength"] * (1.0 / (1.0 + (now - datetime.fromisoformat(e["added_at"]).replace('Z', '+00:00')).total_seconds()/86400)) 
            for e in evidence[:5]  # Only recent 5 pieces
        )

        return weighted_strength / max(len(evidence), 1)

    def summarize_world_state(self) -> str:
        """Generate a human-readable summary of the world model state."""
        
        entity_types = {}
        for entity in self.entities.values():
            etype = entity.type
            entity_types[etype] = entity_types.get(etype, 0) + 1

        lines = [
            f"World Model Summary ({len(self.entities)} entities)",
            "=" * 50,
            "",
        ]

        for etype in sorted(entity_types.keys()):
            count = entity_types[etype]
            if count == 1:
                name = self.entity_index.get(list(self.entities.values())[0].name) or list(self.entities.keys())[0]
                lines.append(f"  {etype}: {list(self.entities.values())[0].name}")
            else:
                lines.append(f"  {etype} ({count}): [various]")

        high_confidence = sum(1 for e in self.entities.values() if e.confidence > 0.8)
        low_confidence = len([e for e in self.entities.values() 
                             if e.confidence < 0.5 and not e.type == "unknown"])
        
        lines.append("")
        lines.append(f"  High confidence entities: {high_confidence}")
        lines.append(f"  Low confidence (uncertain): {low_confidence}")

        return "\n".join(lines)


if __name__ == "__main__":
    print("=== World Model Demo ===\n")

    wm = WorldModel()

    # Build a small world model through observation
    observations = [
        "There exists a file 'alpha/__init__.py' which is the entry point of the project",
        "The tool 'filesystem_scan' can discover directory structures",
        "The workspace contains a foundation_model package with reasoning, memory, and tool layers",
    ]

    for obs in observations:
        wm.observe(observation=obs)

    print(wm.summarize_world_state())
    
    # Query the world model
    fs_tool = wm.get_entity_by_name("filesystem_scan")
    if fs_tool:
        related = wm.get_related_entities(fs_tool.id)
        for r in related[:3]:
            print(f"\n  Entity '{fs_tool.name}' is {r.related_to[0][1]} of:")
            print(f"    → {r.description}")
