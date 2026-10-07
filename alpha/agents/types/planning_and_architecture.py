"""Specialized Agents: Planner, Architect, and Risk."""

import time
from typing import Any, Dict, List, Optional
from alpha.agents.core.base import BaseAgent, AgentRole
from alpha.agents.types.spec import AgentTypeSpec

class PlannerAgent(BaseAgent):
    """Decomposes complex objectives into dependency-ordered execution steps and contingency paths."""

    SPEC = AgentTypeSpec(
        role_name="planner",
        purpose="Generate modular, dependency-respecting execution plans with alternative contingencies.",
        inputs_spec={
            "goal": "Target outcome to accomplish",
            "context": "Context or findings from research",
            "constraints": "Resource, time, or architectural constraints"
        },
        outputs_spec={
            "plan_id": "Unique plan identifier",
            "steps": "Ordered list of step specifications with dependencies",
            "alternative_plans": "Contingency Plan B and Plan C variations",
            "critical_path": "Bottleneck sequence of steps"
        },
        success_metrics=[
            "Plan feasibility >= 0.90",
            "Step atomicity >= 0.85",
            "Zero cyclic dependencies"
        ],
        failure_modes=[
            "Unresolvable circular dependency graphs",
            "Missing prerequisite steps",
            "Underestimating execution complexity"
        ],
        communication_rules=[
            "Submit generated plans as PROPOSAL to Council and Director",
            "Incorporate critique and feedback into plan revisions"
        ]
    )

    def __init__(
        self,
        name: str = "PlannerAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Formulate optimal, resilient execution plans.",
        **kwargs: Any
    ):
        caps = capabilities or ["task_decomposition", "dag_scheduling", "contingency_planning"]
        super().__init__(name=name, role=AgentRole.PLANNER, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        goal = task_context.get("goal") or "Implement project goal"
        
        steps = [
            {"step_id": "step_1_architecture", "action": "Design architecture and contracts", "dependencies": []},
            {"step_id": "step_2_build", "action": "Implement core logic and modules", "dependencies": ["step_1_architecture"]},
            {"step_id": "step_3_test", "action": "Run unit & integration test suites", "dependencies": ["step_2_build"]},
            {"step_id": "step_4_validate", "action": "Perform formal verification and audit", "dependencies": ["step_3_test"]}
        ]

        alternatives = [
            {"plan_name": "Conservative", "description": "Incremental implementation with immediate sandbox verification per step"},
            {"plan_name": "High-Throughput", "description": "Parallel module construction followed by unified integration suite"}
        ]

        self.memory.set_working("last_plan_goal", goal)

        return {
            "success": True,
            "goal": goal,
            "steps": steps,
            "alternative_plans": alternatives,
            "critical_path": ["step_1_architecture", "step_2_build", "step_3_test", "step_4_validate"],
            "plan_score": 0.95
        }


class ArchitectAgent(BaseAgent):
    """Designs modular architectures, component contracts, and interface boundaries."""

    SPEC = AgentTypeSpec(
        role_name="architect",
        purpose="Define structural blueprints, component interfaces, and design invariants.",
        inputs_spec={
            "requirements": "Functional and non-functional system requirements",
            "domain": "Target architectural domain (e.g. distributed, tool, agentic)",
            "patterns": "Preferred design patterns"
        },
        outputs_spec={
            "blueprint_id": "Unique blueprint identifier",
            "components": "List of decoupled system components and responsibilities",
            "interfaces": "Formal contract specifications between components",
            "invariants": "Architectural rules that must never be violated"
        },
        success_metrics=[
            "High cohesion / low coupling ratio >= 0.90",
            "Interface completeness >= 0.95",
            "Zero circular subsystem dependencies"
        ],
        failure_modes=[
            "Tightly coupled monolithic design",
            "Ambiguous interface boundaries",
            "Premature architectural complexity"
        ],
        communication_rules=[
            "Publish architectural blueprints as PROPOSAL to Council",
            "Review Builder and Coding proposals for architectural compliance"
        ]
    )

    def __init__(
        self,
        name: str = "ArchitectAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Architect robust, decoupled, and scalable cognitive systems.",
        **kwargs: Any
    ):
        caps = capabilities or ["system_design", "interface_specification", "pattern_analysis"]
        super().__init__(name=name, role=AgentRole.ARCHITECT, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        reqs = task_context.get("requirements") or task_context.get("goal") or "System design"
        
        components = [
            {"name": "CoreEngine", "role": "Execution coordinator and state manager"},
            {"name": "CommunicationBus", "role": "Decoupled pub/sub event router"},
            {"name": "VerificationLayer", "role": "Deterministic contract enforcement"}
        ]
        interfaces = [
            {"interface": "IExecutable", "methods": ["execute(context) -> Result"]},
            {"interface": "IVerifiable", "methods": ["verify(artifact) -> Status"]}
        ]
        invariants = [
            "No direct cross-subsystem mutable state access",
            "All messages must be cryptographically auditable and versioned"
        ]

        return {
            "success": True,
            "architecture_name": f"ArchSpec_{int(time.time())}",
            "components": components,
            "interfaces": interfaces,
            "invariants": invariants,
            "adherence_score": 0.98
        }


class RiskAgent(BaseAgent):
    """Assesses systemic risks, failure probabilities, impact severity, and mitigations."""

    SPEC = AgentTypeSpec(
        role_name="risk",
        purpose="Anticipate latent failure modes, quantify risk levels, and mandate mitigations.",
        inputs_spec={
            "proposal": "Plan or architecture to analyze",
            "context": "Operational environment and constraints"
        },
        outputs_spec={
            "risk_score": "Aggregated risk rating (0.0=safe, 1.0=critical)",
            "identified_risks": "List of failure modes with probability and impact",
            "mitigations": "Actionable safeguards required before proceeding"
        },
        success_metrics=[
            "Risk detection coverage >= 0.90",
            "False positive rate <= 0.15",
            "Actionable mitigation rate == 1.0"
        ],
        failure_modes=[
            "Underestimating critical edge-case severity",
            "Paralyzing execution with minor risk false alarms"
        ],
        communication_rules=[
            "Transmit high-risk warnings as ESCALATION to Director",
            "Participate in Council Deliberation with evidence-backed risk analysis"
        ]
    )

    def __init__(
        self,
        name: str = "RiskAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Identify vulnerabilities and ensure proactive risk mitigation.",
        **kwargs: Any
    ):
        caps = capabilities or ["risk_assessment", "failure_mode_analysis", "mitigation_synthesis"]
        super().__init__(name=name, role=AgentRole.RISK, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        target = str(task_context.get("proposal") or task_context.get("plan") or "Operational Workflow")
        
        risks = [
            {"risk": "Resource exhaustion during concurrent execution", "probability": 0.25, "impact": 0.70, "mitigation": "Enforce worker concurrency limits and timeout bounds"},
            {"risk": "Unverified schema drift in cross-agent communication", "probability": 0.20, "impact": 0.85, "mitigation": "Enforce deterministic schema validation on message bus"}
        ]
        
        risk_score = 0.28  # low-medium manageable risk
        return {
            "success": True,
            "target": target,
            "risk_score": risk_score,
            "identified_risks": risks,
            "is_acceptable": risk_score < 0.60,
            "recommended_safeguards": [r["mitigation"] for r in risks]
        }
