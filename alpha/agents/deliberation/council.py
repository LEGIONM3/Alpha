"""Council Reasoning: Multi-Agent Deliberation, Disagreement, Counterarguments, and Consensus."""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.agents.core.runtime import AgentRuntime
from alpha.agents.core.base import AgentRole
from alpha.agents.types import (
    ResearchAgent,
    PlannerAgent,
    ArchitectAgent,
    CriticAgent,
    RiskAgent,
    ValidationAgent,
    DirectorAgent,
    KnowledgeAgent
)

class CouncilVerdict(BaseModel):
    """Immutable verdict synthesized by the Final Deliberation Council."""
    verdict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    selected_plan: Dict[str, Any]
    alternative_plans: List[Dict[str, Any]]
    counterarguments: List[str]
    identified_risks: List[Dict[str, Any]]
    evidence_score: float
    disagreement_level: float
    confidence_score: float
    consensus_status: str  # "UNANIMOUS", "SUPERMAJORITY", "DIVIDED"
    rationale: str
    deliberation_time_ms: float
    timestamp: float = Field(default_factory=time.time)

class CouncilDeliberationSystem:
    """Multi-Agent Deliberation pipeline replacing single-agent naive reasoning."""

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self._ensure_council_agents()

    def _ensure_council_agents(self) -> None:
        """Spawn core council representatives if not already present."""
        roles_needed = [
            (ResearchAgent, "CouncilResearcher", AgentRole.RESEARCHER),
            (KnowledgeAgent, "CouncilKnowledge", AgentRole.KNOWLEDGE),
            (PlannerAgent, "CouncilPlanner", AgentRole.PLANNER),
            (ArchitectAgent, "CouncilArchitect", AgentRole.ARCHITECT),
            (CriticAgent, "CouncilCritic", AgentRole.CRITIC),
            (RiskAgent, "CouncilRisk", AgentRole.RISK),
            (ValidationAgent, "CouncilValidator", AgentRole.VALIDATOR),
            (DirectorAgent, "CouncilDirector", AgentRole.DIRECTOR)
        ]
        for cls, name, role in roles_needed:
            if not self.runtime.registry.get_by_role(role):
                self.runtime.lifecycle.spawn(cls, name=name, role=role)

    def deliberate(self, question: str, context: Optional[Dict[str, Any]] = None) -> CouncilVerdict:
        """Execute full multi-stage deliberation pipeline."""
        t0 = time.perf_counter()
        ctx = context or {}

        # Stage 1: Research Team
        researcher = self.runtime.scheduler.select_agent(role=AgentRole.RESEARCHER)
        knowledge = self.runtime.scheduler.select_agent(role=AgentRole.KNOWLEDGE)
        
        research_res = researcher.execute_task({"topic": question, "context": ctx}) if researcher else {}
        evidence_score = float(research_res.get("confidence", 0.85))

        # Stage 2: Planning & Architecture Team
        planner = self.runtime.scheduler.select_agent(role=AgentRole.PLANNER)
        architect = self.runtime.scheduler.select_agent(role=AgentRole.ARCHITECT)

        plan_res = planner.execute_task({"goal": question, "research": research_res}) if planner else {}
        arch_res = architect.execute_task({"requirements": question}) if architect else {}

        selected_plan = {
            "primary_strategy": plan_res.get("steps", []),
            "architecture": arch_res.get("components", []),
            "critical_path": plan_res.get("critical_path", [])
        }
        alternative_plans = plan_res.get("alternative_plans", [])

        # Stage 3: Critique & Risk Team
        critic = self.runtime.scheduler.select_agent(role=AgentRole.CRITIC)
        risk_agent = self.runtime.scheduler.select_agent(role=AgentRole.RISK)

        critic_res = critic.execute_task({"proposal": selected_plan, "question": question}) if critic else {}
        risk_res = risk_agent.execute_task({"plan": selected_plan}) if risk_agent else {}

        counterarguments = critic_res.get("counterarguments", [])
        dissent_level = float(critic_res.get("dissent_level", 0.20))
        identified_risks = risk_res.get("identified_risks", [])
        risk_score = float(risk_res.get("risk_score", 0.25))

        # Stage 4: Verification Team
        validator = self.runtime.scheduler.select_agent(role=AgentRole.VALIDATOR)
        val_res = validator.execute_task({"artifact": selected_plan, "required_keys": ["primary_strategy", "architecture"]}) if validator else {}
        is_valid = bool(val_res.get("is_valid", True))

        # Stage 5: Final Council Synthesis (Presided by Director)
        director = self.runtime.scheduler.select_agent(role=AgentRole.DIRECTOR)
        if director:
            director.execute_task({"directive": question, "plan": selected_plan})

        # Calculate composite confidence score:
        # Base from evidence, penalized by dissent, risk, and validation penalty
        validation_factor = 1.0 if is_valid else 0.5
        raw_confidence = (evidence_score * 0.5 + (1.0 - dissent_level) * 0.3 + (1.0 - risk_score) * 0.2) * validation_factor
        confidence_score = round(max(0.0, min(1.0, raw_confidence)), 3)

        if dissent_level < 0.15:
            consensus = "UNANIMOUS"
        elif dissent_level < 0.40:
            consensus = "SUPERMAJORITY"
        else:
            consensus = "DIVIDED"

        deliberation_time_ms = max(0.01, (time.perf_counter() - t0) * 1000.0)

        rationale = (
            f"Deliberation resolved with consensus status '{consensus}'. "
            f"Evaluated {len(counterarguments)} counterarguments and {len(identified_risks)} risk factors. "
            f"Evidence confidence: {evidence_score:.2f}, Dissent: {dissent_level:.2f}, Composite Confidence: {confidence_score:.2f}."
        )

        return CouncilVerdict(
            question=question,
            selected_plan=selected_plan,
            alternative_plans=alternative_plans,
            counterarguments=counterarguments,
            identified_risks=identified_risks,
            evidence_score=evidence_score,
            disagreement_level=dissent_level,
            confidence_score=confidence_score,
            consensus_status=consensus,
            rationale=rationale,
            deliberation_time_ms=deliberation_time_ms
        )
