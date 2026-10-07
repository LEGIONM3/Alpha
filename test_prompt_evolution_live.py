"""Live Prompt Evolution Experiment with real foundation model."""

import json
import time
from alpha.model_intelligence.connector.gateway import ModelGateway
from alpha.model_intelligence.connector.client import OpenAICompatibleClient
from alpha.model_intelligence.prompt_evolution.genome import PromptGenome
from alpha.model_intelligence.prompt_evolution.registry import PromptRegistry
from alpha.model_intelligence.prompt_evolution.engine import PromptEvolutionEngine

def run_live_prompt_evolution():
    print("Initializing live ModelGateway without mock fallback...")
    client = OpenAICompatibleClient(
        base_url="http://localhost:1234/v1",
        default_model="gemma-4-e4b-it-ultra-uncensored-heretic",
        timeout_seconds=30.0,
        enable_mock_fallback=False
    )
    gateway = ModelGateway(
        base_url="http://localhost:1234/v1",
        client=client,
        enable_mock_fallback=False
    )

    registry = PromptRegistry()
    engine = PromptEvolutionEngine(registry=registry, gateway=gateway)

    benchmark_task = "Analyze whether increasing cache size improves database read latency. Output JSON with key 'conclusion'."
    expected_substring = "conclusion"

    print(f"Starting evolutionary cycle for domain 'database' with real model...")
    t0 = time.time()
    winner = engine.evolve_domain_prompts(
        domain="database",
        benchmark_task=benchmark_task,
        expected_substring=expected_substring,
        population_size=3
    )
    dt = time.time() - t0

    print(f"\nEvolutionary Cycle Completed in {round(dt, 2)}s!")
    print(f"Winner Genome ID: {winner.genome_id}")
    print(f"Generation: {winner.generation}")
    print(f"Fitness Score: {winner.fitness_score}")
    print(f"Scaffold Mode: {winner.scaffold_mode}")
    print(f"Format Constraint: {winner.format_constraint}")
    print(f"Mutations Applied: {winner.mutations_applied}")

    # Persist evolved genome
    payload = {
        "domain": "database",
        "winner_genome": winner.model_dump(),
        "evolution_history": engine.evolution_history,
        "runtime_seconds": round(dt, 2)
    }
    with open("data/evolved_prompt_genome.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("Persisted evolved genome to data/evolved_prompt_genome.json")

    return True

if __name__ == "__main__":
    run_live_prompt_evolution()
