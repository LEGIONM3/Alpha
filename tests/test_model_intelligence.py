"""Unit and integration test suite for Project Alpha's Model Intelligence Layer (Phase 5)."""

import pytest
from typing import Dict, Any

from alpha.operating_system import AlphaOperatingSystem
from alpha.model_intelligence import (
    OpenAICompatibleClient,
    ModelRegistry,
    ModelGateway,
    ModelProfiler,
    ModelCapabilityGraph,
    PromptGenome,
    ScaffoldStyle,
    PromptRegistry,
    PromptEvolutionEngine,
    ContextCompressor,
    ContextRankingEngine,
    ContextLayoutEngine,
    ContextOptimizer,
    ReasoningMode,
    ReasoningProfile,
    ReasoningStrategyLibrary,
    PredictedPerformance,
    PredictiveModelSimulator,
    FailureType,
    FailureReport,
    HallucinationDetector,
    ReasoningFailureDetector,
    ConsistencyChecker,
    LogicFailureDetector,
    ConfidenceCalibrationEngine,
    FailureAnalysisEngine,
    AugmentationType,
    AmplificationConfig,
    AmplificationResult,
    CognitiveAmplificationEngine,
    TaskExecutionPlan,
    SelfAdaptiveOrchestrator,
    ModelLearningHistory,
    MultiModelComparator,
    BenchmarkBatteryGenerator,
    MassiveEvaluationSuite,
    AutomatedImprovementDiscovery,
    WorldModelBridge,
    ModelIntelligenceSystem
)


def test_connector_gateway_and_registry():
    """Part 1: Model Gateway, Client fallback, and Model Registry."""
    registry = ModelRegistry()
    assert len(registry.list_models()) >= 4
    gemma = registry.get_model("gemma-4-e4b-it-ultra-uncensored-heretic")
    assert gemma is not None
    assert gemma.context_window_tokens == 8192

    gateway = ModelGateway(registry=registry, enable_mock_fallback=True)
    resp = gateway.chat_completion(
        messages=[{"role": "user", "content": "Explain Turing completeness."}],
        temperature=0.2
    )
    assert "choices" in resp
    assert len(resp["choices"]) > 0
    assert len(resp["choices"][0]["message"]["content"]) > 0
    assert gateway.telemetry.total_calls >= 1


def test_profiler_and_capability_graph():
    """Parts 2 & 3: Profiling Framework and Capability Graph with 12 canonical capabilities."""
    graph = ModelCapabilityGraph()
    all_caps = graph.get_all_capabilities()
    assert len(all_caps) >= 12
    assert "coding" in all_caps
    assert "reasoning" in all_caps
    assert "architecture" in all_caps

    gateway = ModelGateway(enable_mock_fallback=True)
    profiler = ModelProfiler(gateway=gateway, capability_graph=graph)
    profile = profiler.profile_model(num_trials_per_domain=1)

    assert profile.metrics.accuracy >= 0.5
    assert profile.metrics.hallucination_rate <= 0.5
    assert profile.weakness_profile is not None
    assert profile.failure_profile is not None
    assert graph.get_capability("coding").sample_size >= 1


def test_prompt_evolution_engine():
    """Part 4: Prompt Genome, Registry, and Empirical Mutation Engine."""
    p_reg = PromptRegistry()
    initial_count = len(p_reg.list_genomes())
    assert initial_count >= 1

    gateway = ModelGateway(enable_mock_fallback=True)
    engine = PromptEvolutionEngine(gateway=gateway, registry=p_reg)
    evolved = engine.evolve_generation(domain="coding", generations=1)

    assert evolved is not None
    assert evolved.generation >= 2
    assert evolved.domain == "coding"
    assert len(p_reg.list_genomes()) > initial_count


def test_context_engineering_system():
    """Part 5: Compressor, Ranking, Layout Engine, and Context Optimizer."""
    compressor = ContextCompressor()
    text = "Important rule: Do not delete data.\nImportant rule: Do not delete data.\nSecondary guideline."
    compressed = compressor.compress_text(text, max_tokens=50)
    assert "Important rule: Do not delete data." in compressed
    assert compressed.count("Important rule: Do not delete data.") == 1  # Deduplicated

    ranking = ContextRankingEngine()
    candidates = [
        {"content": "Quantum physics algorithms", "confidence": 0.9, "importance": 0.8},
        {"content": "Database indexing B-tree optimization", "confidence": 0.95, "importance": 0.9},
    ]
    ranked = ranking.rank_fragments(candidates, "database index optimization")
    assert "Database" in ranked[0]["content"]

    optimizer = ContextOptimizer()
    layout = optimizer.optimize_context(
        task_query="Fix memory leak in Python cache",
        world_model_items=[{"id": "cache_svc", "description": "High throughput cache"}],
        beliefs=[{"statement": "Cache uses LRU eviction", "confidence": 0.95}],
        memories=[{"content": "Previous cache fix applied weakref"}],
    )
    rendered = layout.render()
    assert "WORLD MODEL" in rendered
    assert "GROUNDED BELIEFS" in rendered
    assert "LRU eviction" in rendered


def test_reasoning_strategy_library():
    """Part 6: Reasoning Strategy Library with 10 cognitive modes."""
    library = ReasoningStrategyLibrary()
    strategies = library.list_strategies()
    assert len(strategies) == 10

    modes = {s.mode for s in strategies}
    for m in [ReasoningMode.ARCHITECT, ReasoningMode.CODING, ReasoningMode.CRITIC,
              ReasoningMode.VERIFICATION, ReasoningMode.SIMULATION, ReasoningMode.PLANNING]:
        assert m in modes

    strat = library.select_optimal_strategy("Design a distributed consensus protocol with fault tolerance")
    assert strat.mode == ReasoningMode.ARCHITECT

    code_strat = library.select_optimal_strategy("Fix null pointer exception in binary search algorithm")
    assert code_strat.mode == ReasoningMode.CODING


def test_predictive_model_simulator():
    """Part 7: Model Digital Twin forecasting performance and failure vectors."""
    simulator = PredictiveModelSimulator()
    pred = simulator.predict_performance(
        model_name="gemma-4-e4b-it-ultra-uncensored-heretic",
        task_domain="coding",
        prompt_tokens=300,
        context_tokens=600
    )
    assert 0.0 <= pred.expected_accuracy <= 1.0
    assert 0.0 <= pred.failure_probability <= 1.0
    assert pred.expected_latency_ms > 0
    assert 0.0 <= pred.hallucination_risk <= 1.0
    assert len(pred.recommended_augmentations) > 0


def test_failure_analysis_engine():
    """Part 8: Hallucination, Reasoning, Consistency, and Logic Detectors with Calibration."""
    h_detector = HallucinationDetector()
    h_fails = h_detector.detect(
        "This is a 100% verified fact that Martians built Stonehenge.",
        grounded_facts=[]
    )
    assert len(h_fails) >= 1
    assert h_fails[0].failure_type == FailureType.HALLUCINATION

    l_detector = LogicFailureDetector()
    l_fails = l_detector.detect("This assertion is always true and also never true simultaneously.")
    assert len(l_fails) >= 1
    assert l_fails[0].failure_type == FailureType.LOGIC_CONTRADICTION

    c_checker = ConsistencyChecker()
    c_fails = c_checker.detect(["The transaction succeeded completely.", "No, the transaction failed and was aborted."])
    assert len(c_fails) >= 1
    assert c_fails[0].failure_type == FailureType.INCONSISTENCY

    calibrator = ConfidenceCalibrationEngine()
    for _ in range(5):
        calibrator.record_prediction(0.9, True)
    for _ in range(5):
        calibrator.record_prediction(0.9, False)
    ece = calibrator.calculate_expected_calibration_error()
    assert ece > 0.0
    calibrated = calibrator.calibrate(raw_confidence=0.99, domain_historical_accuracy=0.6)
    assert calibrated < 0.99


def test_cognitive_amplification_engine():
    """Part 9: Full 7-step Cognitive Amplification Engine and Amplification Factor."""
    gateway = ModelGateway(enable_mock_fallback=True)
    engine = CognitiveAmplificationEngine(gateway=gateway)

    result = engine.execute_amplified(
        task_query="Implement a thread-safe token bucket rate limiter in Python.",
        domain="coding",
        beliefs=[{"statement": "Token bucket requires mutex lock"}],
        expected_invariants=["Lock", "tokens"]
    )
    assert result.amplified_score > 0.70
    assert result.amplification_factor >= 1.0
    assert result.amplified_latency_ms > 0
    assert len(result.active_augmentations) >= 5


def test_self_adaptive_orchestration():
    """Part 10: Self-Adaptive Orchestrator dynamically choosing execution plan."""
    mis = ModelIntelligenceSystem(enable_mock_fallback=True)
    res = mis.orchestrate("Architect a high availability failover subsystem for Alpha.")
    assert res["success"] is True
    assert "plan" in res
    assert res["plan"]["selected_strategy"] in ["architect", "coding", "planning", "analyst"]
    assert "amplification_result" in res


def test_model_learning_history():
    """Part 11: Longitudinal Model Learning History tracking."""
    history = ModelLearningHistory()
    history.record_run(
        model_name="gemma-4-e4b",
        task_domain="coding",
        strategy_used="coding",
        prompt="Write quicksort",
        output="def quicksort...",
        score=0.95,
        latency_ms=120.0,
        had_failure=False,
        amplification_factor=1.65
    )
    summary = history.get_summary()
    assert summary["total_executions"] == 1
    assert summary["overall_avg_score"] == 0.95
    assert summary["avg_amplification_factor"] == 1.65


def test_multi_model_comparator():
    """Part 12: Multi-Model Comparator across Gemma, Llama, Qwen, DeepSeek, GPT-OSS."""
    comparator = MultiModelComparator()
    result = comparator.compare_models()
    assert len(result.models) >= 4
    assert result.overall_champion != ""
    assert "coding" in result.domain_champions
    assert len(result.tradeoff_insights) >= 3


def test_massive_evaluation_suite():
    """Part 13: 1000+ benchmark task battery procedural generation."""
    generator = BenchmarkBatteryGenerator()
    tasks = generator.generate_full_battery(count_per_domain=150)
    assert len(tasks) == 1050  # 7 domains * 150 tasks

    suite = MassiveEvaluationSuite(generator=generator)
    gateway = ModelGateway(enable_mock_fallback=True)
    amp_engine = CognitiveAmplificationEngine(gateway=gateway)
    sample_results = suite.evaluate_sample(amplification_engine=amp_engine, sample_size_per_domain=1)

    assert sample_results["total_battery_size"] == 1050
    assert sample_results["domains_evaluated"] == 7
    assert sample_results["overall_amplification_factor"] > 1.0


def test_automated_improvement_discovery():
    """Part 14: Autonomous discovery of superior prompts, contexts, and strategies."""
    mis = ModelIntelligenceSystem(enable_mock_fallback=True)
    improvements = mis.run_autonomous_improvement(domain="reasoning")
    assert len(improvements) >= 1
    assert all(imp.applied for imp in improvements)


def test_world_model_bridge_integration():
    """Part 15: Synchronization between Model Intelligence and Cognitive World Model."""
    from alpha.world_model import CognitiveWorldModel
    wm = CognitiveWorldModel()
    bridge = WorldModelBridge(world_model=wm)

    bridge.sync_model_topology("gemma-4-e4b", "Gemma", 8192)
    assert len(bridge.get_sync_log()) >= 1

    # Verify model registered in World Model Knowledge Graph
    node = wm.knowledge_graph.get_node("model_gemma_4_e4b")
    assert node is not None
    assert "gemma" in node.name.lower()


def test_master_operating_system_phase5_integration():
    """Part 16: Master AlphaOperatingSystem integration and high-level interfaces."""
    aos = AlphaOperatingSystem(db_path=":memory:")
    assert hasattr(aos, "model_intelligence")
    assert aos.model_intelligence is not None

    # Test OS-level amplification
    amp_res = aos.amplify_model_execution("Design a multi-region distributed lock algorithm", domain="architecture")
    assert amp_res.amplified_score >= 0.70
    assert amp_res.amplification_factor >= 1.0

    # Test OS-level multi-model comparison
    comp_res = aos.compare_foundation_models()
    assert len(comp_res.models) >= 4
