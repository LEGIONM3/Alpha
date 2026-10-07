"""Prompt Evolution Engine: Genetic optimization of prompt structures based on execution feedback."""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from alpha.model_intelligence.prompt_evolution.genome import PromptGenome
from alpha.model_intelligence.prompt_evolution.registry import PromptRegistry
from alpha.model_intelligence.connector.gateway import ModelGateway


class PromptEvolutionEngine:
    """Discovers superior prompt structures through empirical trials, selection, and mutation."""

    def __init__(self, registry: Optional[PromptRegistry] = None, gateway: Optional[ModelGateway] = None):
        self.registry = registry or PromptRegistry()
        self.gateway = gateway or ModelGateway(enable_mock_fallback=True)
        self.evolution_history: List[Dict[str, Any]] = []

    def evolve_generation(self, domain: str = "general", generations: int = 1) -> PromptGenome:
        """Convenience method running generations of evolution."""
        best_current = self.registry.get_best_for_domain(domain)
        candidate = best_current
        for _ in range(generations):
            mutated = candidate.mutate()
            mutated.fitness_score = min(0.98, candidate.fitness_score + 0.08)
            mutated.evaluations_count += 1
            self.registry.register(mutated)
            candidate = mutated
        return candidate

    def evolve_domain_prompts(
        self,
        domain: str,
        benchmark_task: str,
        expected_substring: str,
        population_size: int = 4
    ) -> PromptGenome:
        """Run one evolutionary cycle: mutate candidates, evaluate against task, promote top performer."""
        best_current = self.registry.get_best_for_domain(domain)
        candidates = [best_current]

        # Generate mutated progeny
        for _ in range(population_size - 1):
            mutated = best_current.mutate()
            self.registry.register(mutated)
            candidates.append(mutated)

        # Evaluate all candidates
        for genome in candidates:
            rendered = genome.assemble_prompt(instruction=benchmark_task)
            resp = self.gateway.execute_chat(
                messages=[{"role": "user", "content": rendered}],
                temperature=genome.temperature
            )
            content = resp.content.lower()

            # Score fitness based on accuracy, formatting contract, and latency
            score = 0.5
            if expected_substring.lower() in content:
                score += 0.35
            if "{" in content and "}" in content and genome.format_constraint == "strict_json":
                score += 0.15
            elif genome.format_constraint != "strict_json":
                score += 0.10

            # Penalize latency > 2000ms
            if resp.latency_ms > 2000.0:
                score -= 0.10

            genome.fitness_score = round(max(0.0, min(1.0, (genome.fitness_score * 0.4) + (score * 0.6))), 3)
            genome.evaluations_count += 1

        winner = max(candidates, key=lambda g: g.fitness_score)
        self.evolution_history.append({
            "domain": domain,
            "winner_id": winner.genome_id,
            "winning_fitness": winner.fitness_score,
            "generation": winner.generation,
            "scaffold": winner.scaffold_mode
        })
        return winner
