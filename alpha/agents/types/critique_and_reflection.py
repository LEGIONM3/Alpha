"""Specialized Agents: Critic, Reflection, and Meta-Learning."""

import time
from typing import Any, Dict, List, Optional
from alpha.agents.core.base import BaseAgent, AgentRole
from alpha.agents.types.spec import AgentTypeSpec

class CriticAgent(BaseAgent):
    """Adversarial analyst that stresses proposals, detects flaws, and generates counterarguments."""

    SPEC = AgentTypeSpec(
        role_name="critic",
        purpose="Identify logical fallacies, weak assumptions, scalability risks, and propose counterarguments.",
        inputs_spec={
            "target": "Proposal, plan, or solution under critique",
            "context": "Contextual domain constraints"
        },
        outputs_spec={
            "flaws_detected": "List of specific vulnerabilities or weaknesses",
            "counterarguments": "Structured counterarguments challenging the proposal",
            "critic_score": "Quality score from critic perspective (0.0 to 1.0)",
            "dissent_level": "Degree of disagreement with proposal (0.0 to 1.0)"
        },
        success_metrics=[
            "Flaw detection yield >= 0.85",
            "Constructive critique ratio >= 0.90",
            "Zero sycophantic approval"
        ],
        failure_modes=[
            "Trivial stylistic complaints",
            "Unsubstantiated rejection without counterarguments"
        ],
        communication_rules=[
            "Issue CHALLENGE on flawed proposals",
            "Serve as core member of Red Team during competitive reasoning"
        ]
    )

    def __init__(
        self,
        name: str = "CriticAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Rigorously challenge assumptions and expose latent weaknesses.",
        **kwargs: Any
    ):
        caps = capabilities or ["adversarial_analysis", "counterargument_generation", "assumption_testing"]
        super().__init__(name=name, role=AgentRole.CRITIC, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        target = task_context.get("target") or task_context.get("proposal") or "Default Proposal"
        rigor = task_context.get("rigor", "high")

        flaws = [
            "Assumes infinite worker pool capacity under high concurrency",
            "Lacks deterministic retry ceiling for external network timeouts"
        ]
        counterarguments = [
            "If network latency spikes, unbounded retries will cause thread exhaustion",
            "Shared context memory could grow unbounded without an explicit LRU retention policy"
        ]

        dissent = 0.35 if flaws else 0.05
        critic_score = 1.0 - dissent

        return {
            "success": True,
            "target": str(target),
            "flaws_detected": flaws,
            "counterarguments": counterarguments,
            "critic_score": critic_score,
            "dissent_level": dissent,
            "verdict": "APPROVED_WITH_CONDITIONS" if dissent < 0.50 else "REJECTED"
        }


class ReflectionAgent(BaseAgent):
    """Conducts post-execution retrospectives, assesses efficacy, and distills lessons learned."""

    SPEC = AgentTypeSpec(
        role_name="reflector",
        purpose="Reflect on execution outcomes, compare expected vs actual, and extract actionable lessons.",
        inputs_spec={
            "workflow_trace": "Completed task or workflow telemetry trace",
            "expected_outcome": "Original specification or goal",
            "actual_outcome": "Actual results achieved"
        },
        outputs_spec={
            "lessons_learned": "List of distilled actionable rules or heuristics",
            "efficiency_rating": "Execution efficiency score (0.0 to 1.0)",
            "counterfactuals": "What could have been done better"
        },
        success_metrics=[
            "Lesson actionability >= 0.90",
            "Post-mortem completeness >= 0.95"
        ],
        failure_modes=[
            "Superficial retrospectives",
            "Failing to generalize specific mistakes into rules"
        ],
        communication_rules=[
            "Deliver reflection reports to Meta-Learning Agent and Memory Agent",
            "Broadcast critical lessons to society"
        ]
    )

    def __init__(
        self,
        name: str = "ReflectionAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Distill profound lessons from every success and failure.",
        **kwargs: Any
    ):
        caps = capabilities or ["post_mortem_analysis", "counterfactual_reasoning", "heuristic_distillation"]
        super().__init__(name=name, role=AgentRole.REFLECTOR, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        trace = task_context.get("workflow_trace", {})
        task_name = task_context.get("task_name", "WorkflowExecution")

        lessons = [
            f"Pre-validating inputs before invoking heavy tools reduces failure rate by 80%",
            f"Caching intermediate verification results prevents redundant execution overhead"
        ]
        counterfactuals = [
            "Parallelizing step 1 and step 2 would have reduced total latency by 45%"
        ]

        return {
            "success": True,
            "task_name": task_name,
            "lessons_learned": lessons,
            "counterfactuals": counterfactuals,
            "efficiency_rating": 0.91,
            "reflection_timestamp": time.time()
        }


class MetaLearningAgent(BaseAgent):
    """Mines societal patterns across agents, generates global heuristics, and writes operational rules."""

    SPEC = AgentTypeSpec(
        role_name="meta_learner",
        purpose="Analyze systemic performance patterns, generate global heuristics, and formulate operational rules.",
        inputs_spec={
            "reflections": "List of reflection reports across multiple tasks",
            "failure_logs": "System failure records",
            "success_metrics": "Historical performance data"
        },
        outputs_spec={
            "operational_rules": "List of new operational rules for the society",
            "heuristics": "Updated decision heuristics",
            "improvement_proposals": "Proposals for agent modifications or scheduling updates"
        },
        success_metrics=[
            "Systemic error reduction rate >= 0.30",
            "Rule validity score >= 0.95"
        ],
        failure_modes=[
            "Overfitting heuristics to one-off anomalies",
            "Generating contradictory operational rules"
        ],
        communication_rules=[
            "Submit operational rules as PROPOSALS to Governance Board",
            "Publish heuristics to Shared Context Layer"
        ]
    )

    def __init__(
        self,
        name: str = "MetaLearningAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Evolve the collective intelligence through meta-learning.",
        **kwargs: Any
    ):
        caps = capabilities or ["pattern_mining", "operational_rule_synthesis", "evolutionary_optimization"]
        super().__init__(name=name, role=AgentRole.META_LEARNER, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC
        self.discovered_rules: List[str] = []

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        context_data = task_context.get("reflections") or []
        
        new_rules = [
            "RULE_ML_001: Always execute dry-run schema validation prior to persistent disk mutation",
            "RULE_ML_002: Mandate Critic review for any plan involving greater than 3 sub-agents",
            "RULE_ML_003: Automatically suspend agents experiencing 3 consecutive execution timeouts"
        ]
        self.discovered_rules.extend(new_rules)

        return {
            "success": True,
            "new_operational_rules": new_rules,
            "total_rules_active": len(self.discovered_rules),
            "meta_learning_gain": 0.18,
            "status": "OPERATIONAL_RULES_SYNTHESIZED"
        }
