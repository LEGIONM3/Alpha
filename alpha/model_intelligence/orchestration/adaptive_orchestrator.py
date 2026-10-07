"""Self-Adaptive Orchestrator: Dynamically selects model, context, strategy, prompt, tools, and memory."""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from alpha.model_intelligence.connector.registry import ModelRegistry
from alpha.model_intelligence.capability_graph.graph import ModelCapabilityGraph
from alpha.model_intelligence.strategies.library import ReasoningStrategyLibrary
from alpha.model_intelligence.prompt_evolution.registry import PromptRegistry
from alpha.model_intelligence.context_engineering.optimizer import ContextOptimizer
from alpha.model_intelligence.digital_twin.simulator import PredictiveModelSimulator
from alpha.model_intelligence.amplification.engine import CognitiveAmplificationEngine
from alpha.model_intelligence.amplification.models import AmplificationConfig, AugmentationType


class TaskExecutionPlan(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    task_query: str
    task_domain: str
    selected_model: str
    selected_strategy: str
    prompt_genome_id: Optional[str] = None
    context_budget_tokens: int = 1500
    active_augmentations: List[str] = Field(default_factory=list)
    selected_tools: List[str] = Field(default_factory=list)
    predicted_accuracy: float
    confidence: float
    reasoning_rationale: str


class SelfAdaptiveOrchestrator:
    """Orchestrates dynamic per-task selection across all dimensions of the Model Intelligence Layer."""

    def __init__(
        self,
        registry: ModelRegistry,
        capability_graph: ModelCapabilityGraph,
        strategy_library: ReasoningStrategyLibrary,
        prompt_registry: PromptRegistry,
        context_optimizer: ContextOptimizer,
        simulator: PredictiveModelSimulator,
        amplification_engine: CognitiveAmplificationEngine
    ):
        self.registry = registry
        self.capability_graph = capability_graph
        self.strategy_library = strategy_library
        self.prompt_registry = prompt_registry
        self.context_optimizer = context_optimizer
        self.simulator = simulator
        self.amplification_engine = amplification_engine

    def detect_domain(self, task_query: str, explicit_domain: Optional[str] = None) -> str:
        if explicit_domain:
            return explicit_domain.lower()
        q = task_query.lower()
        if any(w in q for w in ["code", "function", "class", "script", "debug", "python", "bug"]):
            return "coding"
        elif any(w in q for w in ["architecture", "subsystem", "infrastructure", "schema"]):
            return "architecture"
        elif any(w in q for w in ["research", "investigate", "study", "facts"]):
            return "research"
        elif any(w in q for w in ["plan", "schedule", "milestone"]):
            return "planning"
        elif any(w in q for w in ["simulate", "forecast", "counterfactual"]):
            return "simulation"
        elif any(w in q for w in ["math", "calculate", "equation", "quant"]):
            return "mathematics"
        return "reasoning"

    def plan_task(
        self,
        task_query: str,
        domain: Optional[str] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None
    ) -> TaskExecutionPlan:
        # 1. Determine domain
        resolved_domain = self.detect_domain(task_query, domain)

        # 2. Select optimal model: pick best available from registry for domain
        available_models = self.registry.list_models()
        best_model = "default"
        if available_models:
            # Check capability graph recommendations or default to first
            best_model = available_models[0].name

        # 3. Select optimal reasoning strategy
        strategy = self.strategy_library.select_optimal_strategy(task_query, resolved_domain)

        # 4. Select prompt genome
        best_genome = self.prompt_registry.get_best_genome(domain=resolved_domain)
        genome_id = best_genome.genome_id if best_genome else None

        # 5. Pre-simulate performance via Digital Twin
        pred = self.simulator.predict_performance(
            model_name=best_model,
            task_domain=resolved_domain,
            strategy=strategy
        )

        # 6. Select augmentations dynamically based on risk factors
        augmentations = [AugmentationType.MEMORY, AugmentationType.RETRIEVAL, AugmentationType.PLANNING]
        if pred.hallucination_risk > 0.20 or strategy.verification_required:
            augmentations.append(AugmentationType.VERIFICATION)
            augmentations.append(AugmentationType.REFLECTION)
        if strategy.simulation_required or resolved_domain == "simulation":
            augmentations.append(AugmentationType.SIMULATION)
        if available_tools:
            augmentations.append(AugmentationType.TOOL)

        tool_names = [t.get("name", t.get("function", {}).get("name", "tool")) for t in (available_tools or [])]

        rationale = (
            f"Selected model '{best_model}' and strategy '{strategy.title}' for domain '{resolved_domain}'. "
            f"Expected accuracy {pred.expected_accuracy:.1%}, hallucination risk {pred.hallucination_risk:.1%}. "
            f"Enacting {len(augmentations)} cognitive augmentations."
        )

        return TaskExecutionPlan(
            task_query=task_query,
            task_domain=resolved_domain,
            selected_model=best_model,
            selected_strategy=strategy.mode.value,
            prompt_genome_id=genome_id,
            active_augmentations=[a.value for a in augmentations],
            selected_tools=tool_names,
            predicted_accuracy=pred.expected_accuracy,
            confidence=pred.confidence,
            reasoning_rationale=rationale
        )

    def execute(
        self,
        task_query: str,
        domain: Optional[str] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        memory_items: Optional[List[Dict[str, Any]]] = None,
        world_model_items: Optional[List[Dict[str, Any]]] = None,
        beliefs: Optional[List[Dict[str, Any]]] = None,
        expected_invariants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        # Formulate execution plan
        plan = self.plan_task(task_query, domain, available_tools)

        # Convert plan augmentations to enum set
        enums = [AugmentationType(a) for a in plan.active_augmentations]
        amp_config = AmplificationConfig(
            enabled_augmentations=enums,
            run_verification=(AugmentationType.VERIFICATION in enums),
            run_simulation=(AugmentationType.SIMULATION in enums)
        )

        # Execute through Amplification Engine
        result = self.amplification_engine.execute_amplified(
            task_query=task_query,
            domain=plan.task_domain,
            model_name=plan.selected_model,
            config=amp_config,
            memory_items=memory_items,
            world_model_items=world_model_items,
            beliefs=beliefs,
            tools=available_tools,
            expected_invariants=expected_invariants
        )

        # Update capability graph with empirical execution outcome
        self.capability_graph.record_evaluation(
            capability_name=plan.task_domain,
            score=result.amplified_score,
            evidence=f"Task '{plan.task_id}': amp_factor={result.amplification_factor}x"
        )

        return {
            "plan": plan.model_dump(),
            "amplification_result": result.model_dump(),
            "output": result.amplified_output,
            "success": result.amplified_score >= 0.70
        }
