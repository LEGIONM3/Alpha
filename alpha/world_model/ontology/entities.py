"""Universal Ontology Engine: Entity models, types, and schemas for Project Alpha.

Part 1: Universal Ontology Engine
Every object in Alpha becomes a typed Entity with identity, attributes, metadata,
version history, importance, confidence, provenance, and lifecycle state.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LifecycleState(str, Enum):
    """Lifecycle states through which every entity traverses."""
    DRAFT = "draft"
    ACTIVE = "active"
    EVOLVING = "evolving"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DEAD = "dead"


class EntityType(str, Enum):
    """The 25 canonical entity classes in Alpha's universal ontology."""
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    AGENT = "agent"
    SKILL = "skill"
    TOOL = "tool"
    TASK = "task"
    GOAL = "goal"
    MEMORY = "memory"
    EXPERIENCE = "experience"
    DOCUMENT = "document"
    CONCEPT = "concept"
    RULE = "rule"
    BELIEF = "belief"
    OBSERVATION = "observation"
    EVENT = "event"
    CAPABILITY = "capability"
    RESOURCE = "resource"
    RISK = "risk"
    DECISION = "decision"
    HYPOTHESIS = "hypothesis"
    THEORY = "theory"
    PREDICTION = "prediction"
    SIMULATION = "simulation"
    RELATIONSHIP = "relationship"


class ProvenanceRecord(BaseModel):
    """Provenance tracking origin, creator, timestamp, and derivation sources."""
    creator_id: str = "system"
    creator_role: str = "architect"
    source_ids: List[str] = Field(default_factory=list)
    derivation_method: str = "direct"
    created_at: float = Field(default_factory=time.time)
    notes: Optional[str] = None


class EntityVersion(BaseModel):
    """Snapshot of an entity's state at a particular version."""
    version_number: int
    timestamp: float = Field(default_factory=time.time)
    changed_by: str = "system"
    change_summary: str = "initial"
    snapshot: Dict[str, Any] = Field(default_factory=dict)


class Entity(BaseModel):
    """Base Universal Entity in Project Alpha."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType
    name: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    version_history: List[EntityVersion] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    provenance: ProvenanceRecord = Field(default_factory=ProvenanceRecord)
    lifecycle_state: LifecycleState = LifecycleState.ACTIVE

    def snapshot(self, summary: str = "update", changed_by: str = "system") -> EntityVersion:
        """Create a version snapshot of current state."""
        snap = EntityVersion(
            version_number=self.version,
            timestamp=time.time(),
            changed_by=changed_by,
            change_summary=summary,
            snapshot=self.model_dump(exclude={"version_history"})
        )
        self.version_history.append(snap)
        self.version += 1
        return snap

    def transition_lifecycle(self, target: LifecycleState, reason: str = "") -> None:
        """Safely transition lifecycle state."""
        self.snapshot(summary=f"Lifecycle transition: {self.lifecycle_state.value} -> {target.value} ({reason})")
        self.lifecycle_state = target


# ---------------------------------------------------------------------------
# The 25 Concrete Entity Classes
# ---------------------------------------------------------------------------

class PersonEntity(Entity):
    entity_type: EntityType = EntityType.PERSON
    email: Optional[str] = None
    organization_id: Optional[str] = None
    roles: List[str] = Field(default_factory=list)


class OrganizationEntity(Entity):
    entity_type: EntityType = EntityType.ORGANIZATION
    mission: str = ""
    member_ids: List[str] = Field(default_factory=list)


class ProjectEntity(Entity):
    entity_type: EntityType = EntityType.PROJECT
    goal_ids: List[str] = Field(default_factory=list)
    status: str = "in_progress"
    budget_credits: float = 1000.0


class AgentEntity(Entity):
    entity_type: EntityType = EntityType.AGENT
    role: str = "general"
    runtime_id: Optional[str] = None
    fitness_score: float = 0.5
    capability_ids: List[str] = Field(default_factory=list)


class SkillEntity(Entity):
    entity_type: EntityType = EntityType.SKILL
    skill_version: str = "1.0.0"
    domain: str = "general"
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)


class ToolEntity(Entity):
    entity_type: EntityType = EntityType.TOOL
    tool_name: str = ""
    sandbox_level: str = "subprocess"
    permissions: List[str] = Field(default_factory=list)
    latency_ms_avg: float = 0.0


class TaskEntity(Entity):
    entity_type: EntityType = EntityType.TASK
    status: str = "pending"
    assignee_id: Optional[str] = None
    dependency_ids: List[str] = Field(default_factory=list)
    priority: str = "normal"


class GoalEntity(Entity):
    entity_type: EntityType = EntityType.GOAL
    objective: str = ""
    target_metric: str = ""
    current_value: float = 0.0
    target_value: float = 1.0


class MemoryEntity(Entity):
    entity_type: EntityType = EntityType.MEMORY
    layer: str = "working"
    raw_content: Any = None
    abstraction_level: int = 1


class ExperienceEntity(Entity):
    entity_type: EntityType = EntityType.EXPERIENCE
    task_context: str = ""
    action_taken: str = ""
    outcome: str = ""
    reward: float = 0.0


class DocumentEntity(Entity):
    entity_type: EntityType = EntityType.DOCUMENT
    content: str = ""
    format: str = "markdown"
    author_id: str = "system"


class ConceptEntity(Entity):
    entity_type: EntityType = EntityType.CONCEPT
    definition: str = ""
    abstraction_depth: int = 1
    parent_concept_ids: List[str] = Field(default_factory=list)
    sub_concept_ids: List[str] = Field(default_factory=list)
    exemplar_ids: List[str] = Field(default_factory=list)


class RuleEntity(Entity):
    entity_type: EntityType = EntityType.RULE
    condition: str = ""
    action: str = ""
    priority: int = 1
    success_rate: float = 1.0


class BeliefEntity(Entity):
    entity_type: EntityType = EntityType.BELIEF
    statement: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    contradiction_ids: List[str] = Field(default_factory=list)
    decay_rate: float = 0.01
    last_validation: float = Field(default_factory=time.time)


class ObservationEntity(Entity):
    entity_type: EntityType = EntityType.OBSERVATION
    source: str = "sensor"
    raw_data: Any = None
    observed_at: float = Field(default_factory=time.time)


class EventEntity(Entity):
    entity_type: EntityType = EntityType.EVENT
    event_type: str = "generic"
    actor_id: str = "system"
    payload: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: float = Field(default_factory=time.time)


class CapabilityEntity(Entity):
    entity_type: EntityType = EntityType.CAPABILITY
    category: str = "reasoning"
    proficiency: float = 0.8
    constraints: List[str] = Field(default_factory=list)


class ResourceEntity(Entity):
    entity_type: EntityType = EntityType.RESOURCE
    resource_type: str = "compute"
    capacity: float = 100.0
    current_load: float = 0.0
    cost_per_unit: float = 1.0


class RiskEntity(Entity):
    entity_type: EntityType = EntityType.RISK
    severity: float = 0.5  # 0 to 1
    likelihood: float = 0.5  # 0 to 1
    mitigation_plan: str = ""
    impact_area: str = "system"


class DecisionEntity(Entity):
    entity_type: EntityType = EntityType.DECISION
    context: str = ""
    options_considered: List[str] = Field(default_factory=list)
    chosen_option: str = ""
    rationale: str = ""


class HypothesisEntity(Entity):
    entity_type: EntityType = EntityType.HYPOTHESIS
    premise: str = ""
    predicted_outcome: str = ""
    test_method: str = ""
    is_verified: bool = False


class TheoryEntity(Entity):
    entity_type: EntityType = EntityType.THEORY
    axioms: List[str] = Field(default_factory=list)
    explanatory_power: float = 0.8
    supporting_hypothesis_ids: List[str] = Field(default_factory=list)


class PredictionEntity(Entity):
    entity_type: EntityType = EntityType.PREDICTION
    target_variable: str = ""
    projected_value: Any = None
    horizon_seconds: float = 3600.0
    uncertainty_range: List[float] = Field(default_factory=lambda: [0.0, 1.0])


class SimulationEntity(Entity):
    entity_type: EntityType = EntityType.SIMULATION
    parameters: Dict[str, Any] = Field(default_factory=dict)
    run_results: Dict[str, Any] = Field(default_factory=dict)
    counterfactual_delta: Dict[str, Any] = Field(default_factory=dict)


class RelationshipEntity(Entity):
    entity_type: EntityType = EntityType.RELATIONSHIP
    source_id: str = ""
    target_id: str = ""
    relation_type: str = "related_to"
    weight: float = 1.0
    bidirectional: bool = False


ENTITY_CLASS_MAP = {
    EntityType.PERSON: PersonEntity,
    EntityType.ORGANIZATION: OrganizationEntity,
    EntityType.PROJECT: ProjectEntity,
    EntityType.AGENT: AgentEntity,
    EntityType.SKILL: SkillEntity,
    EntityType.TOOL: ToolEntity,
    EntityType.TASK: TaskEntity,
    EntityType.GOAL: GoalEntity,
    EntityType.MEMORY: MemoryEntity,
    EntityType.EXPERIENCE: ExperienceEntity,
    EntityType.DOCUMENT: DocumentEntity,
    EntityType.CONCEPT: ConceptEntity,
    EntityType.RULE: RuleEntity,
    EntityType.BELIEF: BeliefEntity,
    EntityType.OBSERVATION: ObservationEntity,
    EntityType.EVENT: EventEntity,
    EntityType.CAPABILITY: CapabilityEntity,
    EntityType.RESOURCE: ResourceEntity,
    EntityType.RISK: RiskEntity,
    EntityType.DECISION: DecisionEntity,
    EntityType.HYPOTHESIS: HypothesisEntity,
    EntityType.THEORY: TheoryEntity,
    EntityType.PREDICTION: PredictionEntity,
    EntityType.SIMULATION: SimulationEntity,
    EntityType.RELATIONSHIP: RelationshipEntity,
}
