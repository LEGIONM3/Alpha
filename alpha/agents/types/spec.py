"""Agent Type Specification: Formal definition of Purpose, Inputs, Outputs, Metrics, Failure Modes, and Rules."""

from typing import Dict, List
from pydantic import BaseModel, Field

class AgentTypeSpec(BaseModel):
    """Formal specification contract for an agent archetype."""
    role_name: str
    purpose: str
    inputs_spec: Dict[str, str] = Field(default_factory=dict)
    outputs_spec: Dict[str, str] = Field(default_factory=dict)
    success_metrics: List[str] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)
    communication_rules: List[str] = Field(default_factory=list)
