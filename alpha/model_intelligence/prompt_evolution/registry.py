"""Prompt Registry: Catalog of prompt genomes, versions, and fitness rankings."""

from __future__ import annotations

from typing import Dict, List, Optional
from alpha.model_intelligence.prompt_evolution.genome import PromptGenome


class PromptRegistry:
    """Manages prompt genome library, versions, and empirical leaderboards."""

    def __init__(self):
        self._genomes: Dict[str, PromptGenome] = {}
        self._by_domain: Dict[str, List[str]] = {}
        self._seed_default_genomes()

    def _seed_default_genomes(self) -> None:
        domains = ["coding", "architecture", "reasoning", "planning", "research", "general"]
        for dom in domains:
            g = PromptGenome(
                genome_id=f"genome_base_{dom}",
                domain=dom,
                role_directive=f"You are Alpha's specialized {dom.capitalize()} Intelligence Subsystem.",
                scaffold_mode="plan_then_execute" if dom in ("coding", "planning") else "chain_of_thought",
                format_constraint="strict_json" if dom in ("coding", "planning") else "concise_text",
                fitness_score=0.75
            )
            self.register(g)

    def register(self, genome: PromptGenome) -> PromptGenome:
        self._genomes[genome.genome_id] = genome
        if genome.domain not in self._by_domain:
            self._by_domain[genome.domain] = []
        if genome.genome_id not in self._by_domain[genome.domain]:
            self._by_domain[genome.domain].append(genome.genome_id)
        return genome

    def get(self, genome_id: str) -> Optional[PromptGenome]:
        return self._genomes.get(genome_id)

    def get_best_for_domain(self, domain: str) -> PromptGenome:
        gids = self._by_domain.get(domain, [])
        if not gids:
            return self.get_best_for_domain("general")
        candidates = [self._genomes[gid] for gid in gids if gid in self._genomes]
        return max(candidates, key=lambda g: g.fitness_score)

    def list_domain_leaderboard(self, domain: str) -> List[PromptGenome]:
        gids = self._by_domain.get(domain, [])
        candidates = [self._genomes[gid] for gid in gids if gid in self._genomes]
        return sorted(candidates, key=lambda g: g.fitness_score, reverse=True)

    def list_genomes(self) -> List[PromptGenome]:
        return list(self._genomes.values())

    def get_best_genome(self, domain: str = "general") -> PromptGenome:
        return self.get_best_for_domain(domain)

    def count(self) -> int:
        return len(self._genomes)
