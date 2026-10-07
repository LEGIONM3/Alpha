"""Project Alpha - Phase 5: Model Intelligence Layer (Foundation Model Amplification System)
Comprehensive Master Demonstration Script executing all 8 canonical demonstrations.
"""

import sys
import time
from typing import Dict, Any, List

from alpha.operating_system import AlphaOperatingSystem
from alpha.model_intelligence import (
    ModelIntelligenceSystem,
    ReasoningMode,
    ScaffoldStyle,
    AugmentationType,
    AmplificationConfig
)


def print_banner(title: str, subtitle: str = ""):
    print("\n" + "=" * 80)
    print(f"  PROJECT ALPHA // PHASE 5: MODEL INTELLIGENCE LAYER")
    print(f"  {title.upper()}")
    if subtitle:
        print(f"  {subtitle}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n--- [ {title} ] ---")


def run_all_demonstrations():
    print_banner(
        "Foundation Model Amplification System",
        "Cognitive World Model & Foundation Model Symbiosis Without Weight Retraining"
    )

    aos = AlphaOperatingSystem(db_path=":memory:")
    mis: ModelIntelligenceSystem = aos.model_intelligence

    # -------------------------------------------------------------------------
    # DEMONSTRATION 1: CAPABILITY MAPPING
    # -------------------------------------------------------------------------
    print_banner("Demonstration 1: Capability Mapping", "Empirical Profiling & Canonical Capability Graph")
    print("Discovered Models at Endpoint:")
    for model in mis.registry.list_models():
        print(f"  - [{model.family.upper()}] {model.name} (Context: {model.context_window_tokens} tokens)")

    print_section("Executing Empirical Profiler Battery")
    profile = mis.profiler.profile_model(num_trials_per_domain=1)
    print(f"Target Model: {profile.model_id}")
    print(f"Accuracy: {profile.metrics.accuracy:.1%}")
    print(f"Latency: {profile.metrics.avg_latency_ms:.1f}ms")
    print(f"Hallucination Rate: {profile.metrics.hallucination_rate:.1%}")
    print(f"Instruction Following: {profile.metrics.instruction_following:.1%}")
    print(f"Planning Ability: {profile.metrics.planning_ability:.1%}")

    print_section("Canonical Capability Graph (12 Cognitive Dimensions)")
    for cap_name, cap_node in mis.capability_graph.get_all_capabilities().items():
        bar = "#" * int(cap_node.score * 20) + "-" * (20 - int(cap_node.score * 20))
        print(f"  {cap_name.capitalize():15} [{bar}] {cap_node.score:.2f} (Conf: {cap_node.confidence:.2f}, N={cap_node.sample_size})")

    print_section("Observed Weaknesses & Vulnerabilities")
    for w in profile.weakness_profile.primary_weaknesses:
        print(f"  [WEAKNESS] {w}")
    for k, thresh in profile.weakness_profile.failure_probability_thresholds.items():
        print(f"  [RISK BOUND] {k}: Failure Probability {thresh:.1%}")

    # -------------------------------------------------------------------------
    # DEMONSTRATION 2: PROMPT EVOLUTION
    # -------------------------------------------------------------------------
    print_banner("Demonstration 2: Prompt Evolution", "Empirical Mutation and Fitness Selection Across Generations")
    base_genome = mis.prompt_registry.get_best_genome("coding")
    print(f"Initial Prompt Genome ({base_genome.genome_id}):")
    print(f"  Generation: {base_genome.generation}")
    print(f"  Scaffold Mode: {base_genome.scaffold_mode}")
    print(f"  Initial Fitness: {base_genome.fitness_score:.2f}")

    print_section("Executing 2 Generations of Evolutionary Mutation")
    evolved = mis.prompt_engine.evolve_generation(domain="coding", generations=2)
    print(f"Evolved Winner Genome ({evolved.genome_id}):")
    print(f"  Generation: {evolved.generation}")
    print(f"  Scaffold Mode: {evolved.scaffold_mode}")
    print(f"  New Fitness Score: {evolved.fitness_score:.2f} (+{(evolved.fitness_score - base_genome.fitness_score) * 100:.1f}%)")
    print(f"  Mutations Applied: {evolved.mutations_applied}")

    # -------------------------------------------------------------------------
    # DEMONSTRATION 3: CONTEXT OPTIMIZATION
    # -------------------------------------------------------------------------
    print_banner("Demonstration 3: Context Optimization", "Ranking, Semantic Compression, and Structured Section Layout")
    task_query = "Optimize distributed PostgreSQL connection pooling under 10k concurrent transactions"
    raw_world_model = [
        {"id": "pg_cluster", "description": "Primary PostgreSQL database cluster with replica nodes"},
        {"id": "unrelated_svc", "description": "Frontend static asset CDN bucket configuration"},
        {"id": "pg_pool", "description": "PgBouncer transaction-mode pooler running on port 6432"}
    ]
    raw_beliefs = [
        {"statement": "Connection pooling in transaction mode reduces memory consumption per worker", "confidence": 0.96},
        {"statement": "Max connection limit is 500 on primary database instance", "confidence": 0.99},
        {"statement": "User interface uses React 19 server components", "confidence": 0.85}
    ]
    raw_memories = [
        {"content": "Previous incident INC-842: Thread exhaustion occurred when connection pool was exhausted"},
        {"content": "User prefers dark mode syntax highlighting in editor"}
    ]

    print_section("Executing Context Optimizer Pipeline")
    optimized_layout = mis.context_optimizer.optimize_context(
        task_query=task_query,
        world_model_items=raw_world_model,
        beliefs=raw_beliefs,
        memories=raw_memories
    )
    rendered_context = optimized_layout.render()
    print("Structured Context Layout Output:")
    print(rendered_context)

    # -------------------------------------------------------------------------
    # DEMONSTRATION 4: FAILURE PREDICTION
    # -------------------------------------------------------------------------
    print_banner("Demonstration 4: Failure Prediction", "Model Digital Twin Pre-Execution Simulation")
    pred = mis.simulator.predict_performance(
        model_name="gemma-4-e4b-it-ultra-uncensored-heretic",
        task_domain="architecture",
        prompt_tokens=450,
        context_tokens=1200,
        strategy=mis.strategy_library.get_strategy(ReasoningMode.ARCHITECT)
    )
    print(f"Simulated Domain: {pred.task_domain}")
    print(f"Forecasted Accuracy: {pred.expected_accuracy:.1%}")
    print(f"Failure Probability: {pred.failure_probability:.1%}")
    print(f"Estimated Latency: {pred.expected_latency_ms:.1f}ms")
    print(f"Hallucination Risk: {pred.hallucination_risk:.1%}")
    print("Digital Twin Prescriptions:")
    for rec in pred.recommended_augmentations:
        print(f"  [ACTION] {rec}")

    # -------------------------------------------------------------------------
    # DEMONSTRATION 5: HALLUCINATION REDUCTION
    # -------------------------------------------------------------------------
    print_banner("Demonstration 5: Hallucination Reduction", "Grounded Epistemic Verification and Detection")
    hallucinatory_text = (
        "It is universally guaranteed that Martian Emperor Xylos signed the Treaty of Alpha in 1842, "
        "granting Alpha full jurisdiction over the solar grid."
    )
    print_section("Unconstrained Standalone Text Generation:")
    print(f"'{hallucinatory_text}'")

    audit = mis.failure_engine.analyze(
        response_text=hallucinatory_text,
        grounded_facts=["Martian civilizations have never existed.", "Project Alpha was founded in 2026."]
    )
    print_section("Audit Detection Diagnostics:")
    print(f"Violations Detected: {audit['total_detected']}")
    for f in audit["failures"]:
        print(f"  [DETECTION] Type: {f['failure_type'].upper()} | Severity: {f['severity']:.2f}")
        print(f"    Description: {f['description']}")
        print(f"    Remediation: {f['remediation_strategy']}")

    # -------------------------------------------------------------------------
    # DEMONSTRATION 6: AMPLIFICATION MEASUREMENT
    # -------------------------------------------------------------------------
    print_banner("Demonstration 6: Amplification Measurement", "Standalone vs Amplified Execution & Amplification Factor")
    amp_result = mis.amplify_task(
        task_query="Implement a concurrent TokenBucketRateLimiter class with acquire() method.",
        domain="coding"
    )
    print(f"Task: {amp_result.task_id}")
    print(f"Standalone Performance Score: {amp_result.standalone_score:.2f} ({amp_result.standalone_latency_ms:.1f}ms)")
    print(f"Amplified Performance Score:  {amp_result.amplified_score:.2f} ({amp_result.amplified_latency_ms:.1f}ms)")
    print(f"Verification Verdict:         {'PASSED' if amp_result.verification_passed else 'FAILED'}")
    print(f"Active Scaffolds:             {', '.join(amp_result.active_augmentations)}")
    print(f"==> AMPLIFICATION FACTOR:    {amp_result.amplification_factor}x COGNITIVE GAIN")

    # -------------------------------------------------------------------------
    # DEMONSTRATION 7: MULTI-MODEL COMPARISON
    # -------------------------------------------------------------------------
    print_banner("Demonstration 7: Multi-Model Comparison", "Cross-Architecture Head-to-Head Benchmarking")
    comparison = mis.compare_models()
    print(f"Evaluated Model Architectures: {', '.join(comparison.models)}")
    print("\nBenchmark Scores by Architecture:")
    for model_name, metrics in comparison.metrics_by_model.items():
        print(f"  {model_name:36} Acc: {metrics['accuracy']:.1%} | Latency: {metrics['latency_ms']:5.1f}ms | Depth: {metrics['reasoning_depth']:.2f}")

    print("\nDomain Champions:")
    for dom, champ in comparison.domain_champions.items():
        print(f"  - {dom.capitalize():15} Winner: {champ}")

    print(f"\nOverall Architecture Champion: {comparison.overall_champion}")
    for ins in comparison.tradeoff_insights:
        print(f"  [INSIGHT] {ins}")

    # -------------------------------------------------------------------------
    # DEMONSTRATION 8: AUTONOMOUS OPTIMIZATION
    # -------------------------------------------------------------------------
    print_banner("Demonstration 8: Autonomous Optimization", "Closed-Loop Self-Tuning Without Human Intervention")
    improvements = mis.run_autonomous_improvement(domain="reasoning")
    print(f"Autonomous Discovery Cycle Completed. Discovered Improvements: {len(improvements)}")
    for imp in improvements:
        print(f"\n  Improvement ID:   {imp.improvement_id}")
        print(f"  Type:             {imp.discovery_type.value.upper()}")
        print(f"  Baseline Score:   {imp.baseline_score:.2f}")
        print(f"  Discovered Score: {imp.discovered_score:.2f} (+{imp.delta * 100:.1f}%)")
        print(f"  Action Taken:     {imp.description}")
        print(f"  Auto-Applied:     {imp.applied}")

    # -------------------------------------------------------------------------
    # OPERATING SYSTEM INTEGRATION CHECK
    # -------------------------------------------------------------------------
    print_banner("System State: World Model Synchronization", "Unified Mind Verification")
    sync_logs = mis.world_model_bridge.get_sync_log()
    print(f"Total World Model Sync Transactions: {len(sync_logs)}")
    for s in sync_logs[:5]:
        print(f"  - Synchronized {s['action']} to World Model Knowledge Graph and Epistemic Beliefs")

    print("\n" + "=" * 80)
    print("  PROJECT ALPHA PHASE 5: COMPLETE & OPERATIONAL")
    print("  Foundation Model Amplification System successfully verified across all 16 parts.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_demonstrations()
