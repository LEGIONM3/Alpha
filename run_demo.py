"""Interactive demonstration of Alpha Phase 1: Cognitive Scaffolding Layer.

Shows how external scaffolding enables a weak foundation model to execute
complex multi-step tasks, detect errors, reflect, and self-correct.
"""

import sys
import json
from alpha.core.engine import AlphaEngine
from alpha.core.model_adapter import MockWeakModel
from alpha.core.types import KnowledgeType

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)

def main():
    print_header("Alpha Phase 1: Cognitive Scaffolding Layer Demonstration")
    print("Initializing Alpha Cognitive Engine with Low-Reasoning Model Simulator...")

    # Initialize model that makes a mistake on the first JSON step to demonstrate reflection & retry
    weak_model = MockWeakModel(failure_on_first_try=True)
    engine = AlphaEngine(model=weak_model, db_path=":memory:")

    # 1. Populate Knowledge Store
    print("\n[Step 1] Ingesting Project Specifications & Architecture Decisions into Knowledge Store...")
    engine.knowledge.store_document(
        title="Microservice API Security Guidelines",
        content="All public API endpoints require OAuth2 bearer token validation. "
                "Rate limits must be configured to max 100 requests per minute per IP. "
                "Output must always be validated against explicit JSON schemas.",
        tags=["security", "api", "ratelimit"]
    )
    engine.knowledge.store_adr(
        title="Decoupled Scaffolding vs Foundation Weights",
        decision="Keep the foundation model weights static. All intelligence gains must come from external scaffolding.",
        rationale="Small models are fast and cheap; external scaffolding guarantees reliability, memory, and validation."
    )
    print("[OK] Knowledge Store populated with 2 foundational documents.")

    # 2. Populate Memory with Lessons Learned from past runs
    print("\n[Step 2] Injecting Prior Lessons Learned into Memory Manager...")
    engine.memory.store_lesson_learned(
        rule="Always include explicit status field in response dictionaries",
        context_trigger="schema_generation",
        rationale="Prevents client downstream parsing ambiguities"
    )
    print("[OK] Memory Manager initialized with seed operational heuristic.")

    # 3. Present Complex Goal
    goal = "Design and validate a secure API rate limiter specification for payment webhooks"
    print_header("Executing High-Level Goal")
    print(f"Goal: '{goal}'")

    print("\n[Scaffolding Action] Decomposing Goal into Hierarchical Task Tree (DAG)...")
    tree = engine.decomposer.decompose(goal, goal_name="Payment Webhook Rate Limiter")
    
    print("\n[Task Tree Nodes]")
    for node_id, node in tree.nodes.items():
        indent = "  " * node.level.value
        deps = f" [Dependencies: {', '.join(node.dependencies)}]" if node.dependencies else ""
        print(f"{indent}- [{node.level.name}] {node.name} (Complexity: {node.complexity.name}){deps}")

    print("\n[Scaffolding Action] Generating Execution Plan with Resource Budgets & Validation Contracts...")
    plan = engine.planner.create_plan_from_tree(tree)
    print(f"Total Steps: {len(plan.steps)} | Est. Tokens: {plan.total_estimated_tokens} | Timeout Budget: {plan.total_estimated_time_s}s")
    for s in plan.steps:
        print(f"  Step {s.step_number}: '{s.name}' -> Contracts: {[c.description for c in s.validation_contracts]}")

    print_header("Executing Scaffolding Execution Loop")
    result = engine.execute_goal(goal, goal_name="Payment Webhook Rate Limiter")

    print(f"\nExecution Finished! Overall Success: {result['success']}")
    print(f"Completed Steps: {result['completed_steps']}/{result['total_steps']}")

    print_header("Reflection Engine Analysis")
    for r in result["reflection_reports"]:
        status_icon = "[PASSED]" if r["passed"] else "[FAILED -> TRIGGERED REFLECTION RETRY]"
        print(f"\nStep {r['step_number']} [{r['task_id']}] -> {status_icon} (Score: {r['overall_score']:.2f})")
        if r["what_worked"]:
            print(f"  What Worked: {r['what_worked']}")
        if r["what_failed"]:
            print(f"  What Failed: {r['what_failed']}")
        if r["what_can_improve"]:
            print(f"  What Can Improve: {r['what_can_improve']}")
        if r["corrective_prompt_injection"]:
            print("  Corrective Prompt Injected into Small Model on Retry:")
            for line in r["corrective_prompt_injection"].splitlines():
                print(f"    | {line}")

    print_header("Experience Log & Performance Statistics")
    stats = engine.experience.get_statistics()
    print(f"Total Model Executions Recorded: {stats['total_runs']}")
    print(f"Successful Executions:           {stats['successful_runs']}")
    print(f"Failed (Recovered) Executions:   {stats['failed_runs']}")
    print(f"Success Rate:                    {stats['success_rate']*100:.1f}%")
    print(f"Average Execution Reward:        {stats['avg_reward']}")
    print(f"Total Token Usage (Est):         {stats['total_tokens_used']}")

    print("\n" + "=" * 70)
    print(" ALPHA PHASE 1 SCAFFOLDING DEMO COMPLETE: SUCCESSFUL BEHAVIOR AMPLIFICATION")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
