"""Model Intelligence Layer (Foundation Model Amplification System) for Project Alpha."""

from alpha.model_intelligence.connector.client import OpenAICompatibleClient
from alpha.model_intelligence.connector.registry import ModelRegistry, ModelMetadata, ModelConfiguration
from alpha.model_intelligence.connector.gateway import ModelGateway
from alpha.model_intelligence.profiler.profiler import ModelProfiler
from alpha.model_intelligence.profiler.profiles import CapabilityProfile, WeaknessProfile, FailureProfile, ModelBenchmarkMetrics
from alpha.model_intelligence.capability_graph.graph import ModelCapabilityGraph, CapabilityNode
from alpha.model_intelligence.prompt_evolution.genome import PromptGenome, ScaffoldStyle
from alpha.model_intelligence.prompt_evolution.registry import PromptRegistry
from alpha.model_intelligence.prompt_evolution.engine import PromptEvolutionEngine
from alpha.model_intelligence.context_engineering.compressor import ContextCompressor
from alpha.model_intelligence.context_engineering.ranking import ContextRankingEngine
from alpha.model_intelligence.context_engineering.layout import ContextLayout, ContextLayoutEngine
from alpha.model_intelligence.context_engineering.optimizer import ContextOptimizer, ContextOptimizationConfig
from alpha.model_intelligence.strategies.profiles import ReasoningMode, ReasoningProfile
from alpha.model_intelligence.strategies.library import ReasoningStrategyLibrary
from alpha.model_intelligence.digital_twin.predictions import PredictedPerformance
from alpha.model_intelligence.digital_twin.simulator import PredictiveModelSimulator
from alpha.model_intelligence.failure_analysis.models import FailureType, FailureReport
from alpha.model_intelligence.failure_analysis.detectors import (
    HallucinationDetector,
    ReasoningFailureDetector,
    ConsistencyChecker,
    LogicFailureDetector,
)
from alpha.model_intelligence.failure_analysis.calibration import ConfidenceCalibrationEngine
from alpha.model_intelligence.failure_analysis.engine import FailureAnalysisEngine
from alpha.model_intelligence.amplification.models import AugmentationType, AmplificationConfig, AmplificationResult
from alpha.model_intelligence.amplification.engine import CognitiveAmplificationEngine
from alpha.model_intelligence.orchestration.adaptive_orchestrator import TaskExecutionPlan, SelfAdaptiveOrchestrator
from alpha.model_intelligence.learning_history.records import ExecutionRecord
from alpha.model_intelligence.learning_history.history_store import ModelLearningHistory
from alpha.model_intelligence.multi_model.comparator import MultiModelComparator, ModelComparisonResult
from alpha.model_intelligence.benchmarks.tasks import BenchmarkTask, BenchmarkBatteryGenerator
from alpha.model_intelligence.benchmarks.suite import MassiveEvaluationSuite
from alpha.model_intelligence.improvement.discovery import DiscoveryType, DiscoveredImprovement, AutomatedImprovementDiscovery
from alpha.model_intelligence.integration.world_model_bridge import WorldModelBridge
from alpha.model_intelligence.system import ModelIntelligenceSystem

__all__ = [
    "OpenAICompatibleClient",
    "ModelRegistry",
    "ModelMetadata",
    "ModelConfiguration",
    "ModelGateway",
    "ModelProfiler",
    "CapabilityProfile",
    "WeaknessProfile",
    "FailureProfile",
    "ModelBenchmarkMetrics",
    "ModelCapabilityGraph",
    "CapabilityNode",
    "PromptGenome",
    "ScaffoldStyle",
    "PromptRegistry",
    "PromptEvolutionEngine",
    "ContextCompressor",
    "ContextRankingEngine",
    "ContextLayout",
    "ContextLayoutEngine",
    "ContextOptimizer",
    "ContextOptimizationConfig",
    "ReasoningMode",
    "ReasoningProfile",
    "ReasoningStrategyLibrary",
    "PredictedPerformance",
    "PredictiveModelSimulator",
    "FailureType",
    "FailureReport",
    "HallucinationDetector",
    "ReasoningFailureDetector",
    "ConsistencyChecker",
    "LogicFailureDetector",
    "ConfidenceCalibrationEngine",
    "FailureAnalysisEngine",
    "AugmentationType",
    "AmplificationConfig",
    "AmplificationResult",
    "CognitiveAmplificationEngine",
    "TaskExecutionPlan",
    "SelfAdaptiveOrchestrator",
    "ExecutionRecord",
    "ModelLearningHistory",
    "MultiModelComparator",
    "ModelComparisonResult",
    "BenchmarkTask",
    "BenchmarkBatteryGenerator",
    "MassiveEvaluationSuite",
    "DiscoveryType",
    "DiscoveredImprovement",
    "AutomatedImprovementDiscovery",
    "WorldModelBridge",
    "ModelIntelligenceSystem",
]
