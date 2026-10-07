"""Model Intelligence System: Master facade integrating all 15 Model Intelligence components."""

from typing import List, Dict, Any, Optional

from alpha.model_intelligence.connector.client import OpenAICompatibleClient
from alpha.model_intelligence.connector.registry import ModelRegistry
from alpha.model_intelligence.connector.gateway import ModelGateway
from alpha.model_intelligence.profiler.profiler import ModelProfiler
from alpha.model_intelligence.capability_graph.graph import ModelCapabilityGraph
from alpha.model_intelligence.prompt_evolution.genome import PromptGenome
from alpha.model_intelligence.prompt_evolution.registry import PromptRegistry
from alpha.model_intelligence.prompt_evolution.engine import PromptEvolutionEngine
from alpha.model_intelligence.context_engineering.compressor import ContextCompressor
from alpha.model_intelligence.context_engineering.ranking import ContextRankingEngine
from alpha.model_intelligence.context_engineering.layout import ContextLayoutEngine
from alpha.model_intelligence.context_engineering.optimizer import ContextOptimizer
from alpha.model_intelligence.strategies.library import ReasoningStrategyLibrary
from alpha.model_intelligence.digital_twin.simulator import PredictiveModelSimulator
from alpha.model_intelligence.failure_analysis.engine import FailureAnalysisEngine
from alpha.model_intelligence.amplification.engine import CognitiveAmplificationEngine
from alpha.model_intelligence.amplification.models import AmplificationConfig, AmplificationResult
from alpha.model_intelligence.orchestration.adaptive_orchestrator import SelfAdaptiveOrchestrator, TaskExecutionPlan
from alpha.model_intelligence.learning_history.history_store import ModelLearningHistory
from alpha.model_intelligence.multi_model.comparator import MultiModelComparator, ModelComparisonResult
from alpha.model_intelligence.benchmarks.suite import MassiveEvaluationSuite
from alpha.model_intelligence.improvement.discovery import AutomatedImprovementDiscovery, DiscoveredImprovement
from alpha.model_intelligence.integration.world_model_bridge import WorldModelBridge


class ModelIntelligenceSystem:
    """Master Architecture Facade for Project Alpha's Model Intelligence Layer."""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:1234/v1",
        world_model: Optional[Any] = None,
        enable_mock_fallback: bool = True
    ):
        # 1. Connector
        self.client = OpenAICompatibleClient(base_url=endpoint_url, enable_mock_fallback=enable_mock_fallback)
        self.registry = ModelRegistry()
        self.gateway = ModelGateway(client=self.client, registry=self.registry)

        # 2. Capability Graph & Profiler
        self.capability_graph = ModelCapabilityGraph()
        self.profiler = ModelProfiler(gateway=self.gateway, capability_graph=self.capability_graph)

        # 3. Prompt Evolution
        self.prompt_registry = PromptRegistry()
        self.prompt_engine = PromptEvolutionEngine(gateway=self.gateway, registry=self.prompt_registry)

        # 4. Context Engineering
        self.compressor = ContextCompressor()
        self.ranking_engine = ContextRankingEngine()
        self.layout_engine = ContextLayoutEngine()
        self.context_optimizer = ContextOptimizer(self.compressor, self.ranking_engine, self.layout_engine)

        # 5. Reasoning Strategy Library
        self.strategy_library = ReasoningStrategyLibrary()

        # 6. Digital Twin
        self.simulator = PredictiveModelSimulator(capability_graph=self.capability_graph, registry=self.registry)

        # 7. Failure Analysis
        self.failure_engine = FailureAnalysisEngine()

        # 8. Cognitive Amplification
        self.amplification_engine = CognitiveAmplificationEngine(
            gateway=self.gateway,
            strategy_library=self.strategy_library,
            context_optimizer=self.context_optimizer,
            failure_engine=self.failure_engine,
            simulator=self.simulator
        )

        # 9. Self-Adaptive Orchestration
        self.orchestrator = SelfAdaptiveOrchestrator(
            registry=self.registry,
            capability_graph=self.capability_graph,
            strategy_library=self.strategy_library,
            prompt_registry=self.prompt_registry,
            context_optimizer=self.context_optimizer,
            simulator=self.simulator,
            amplification_engine=self.amplification_engine
        )

        # 10. Learning History
        self.learning_history = ModelLearningHistory()

        # 11. Multi-Model Comparator
        self.multi_model = MultiModelComparator(registry=self.registry, capability_graph=self.capability_graph)

        # 12. Massive Evaluation Suite
        self.eval_suite = MassiveEvaluationSuite()

        # 13. Automated Improvement Discovery
        self.improvement_discovery = AutomatedImprovementDiscovery(
            evolution_engine=self.prompt_engine,
            prompt_registry=self.prompt_registry,
            capability_graph=self.capability_graph,
            strategy_library=self.strategy_library
        )

        # 14. World Model Bridge
        self.world_model = world_model
        self.world_model_bridge = WorldModelBridge(world_model=world_model)

        # Auto-discover local models and sync topology
        self.bootstrap()

    def bootstrap(self):
        """Discovers active local models and synchronizes initial topology."""
        models = self.gateway.discover_and_register_active_models()
        for m in models:
            self.world_model_bridge.sync_model_topology(
                model_name=m.name,
                family=m.family,
                context_window=m.context_window
            )

    def amplify_task(
        self,
        task_query: str,
        domain: str = "reasoning",
        model_name: Optional[str] = None,
        config: Optional[AmplificationConfig] = None
    ) -> AmplificationResult:
        """Executes task with full cognitive amplification and records longitudinal history."""
        res = self.amplification_engine.execute_amplified(
            task_query=task_query,
            domain=domain,
            model_name=model_name,
            config=config
        )

        # Record to learning history
        self.learning_history.record_run(
            model_name=model_name or "default",
            task_domain=domain,
            strategy_used=res.details.get("strategy_selected", "analyst"),
            prompt=task_query,
            output=res.amplified_output,
            score=res.amplified_score,
            latency_ms=res.amplified_latency_ms,
            had_failure=not res.verification_passed,
            amplification_factor=res.amplification_factor
        )

        # Sync to World Model
        self.world_model_bridge.sync_execution_outcome(res, model_name=model_name or "default")

        return res

    def orchestrate(
        self,
        task_query: str,
        domain: Optional[str] = None,
        available_tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Self-adaptive end-to-end task execution."""
        return self.orchestrator.execute(
            task_query=task_query,
            domain=domain,
            available_tools=available_tools
        )

    def profile_active_model(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Profiles the active model across benchmark batteries and updates capability graph."""
        profile = self.profiler.profile_model(model_name)
        self.world_model_bridge.sync_capability_update(self.capability_graph)
        return profile.model_dump()

    def compare_models(self) -> ModelComparisonResult:
        """Compares local model against industry architectures (Qwen, DeepSeek, Llama, Gemma, GPT OSS)."""
        return self.multi_model.compare_models()

    def run_eval_battery(self, sample_size: int = 5) -> Dict[str, Any]:
        """Executes a sample of the 1000+ benchmark task battery across all 7 domains."""
        return self.eval_suite.evaluate_sample(
            amplification_engine=self.amplification_engine,
            sample_size_per_domain=sample_size
        )

    def run_autonomous_improvement(self, domain: str = "reasoning") -> List[DiscoveredImprovement]:
        """Runs autonomous discovery cycle for prompt, context, and strategy optimization."""
        return self.improvement_discovery.run_discovery_cycle(domain=domain)
