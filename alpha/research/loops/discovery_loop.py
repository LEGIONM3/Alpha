"""Continuous Scientific Discovery Loop: Autonomous end-to-end knowledge generation.

Implements the continuous scientific cycle:
Question -> Hypothesis -> Experiment -> Evidence -> Evaluation -> Theory -> Publication -> New Questions
"""

from __future__ import annotations

import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import (
    ResearchProblem,
    ResearchQuestion,
    Hypothesis,
    Experiment,
    Observation,
    Evidence,
    Finding,
    Theory,
    Publication,
    Replication,
    ResearchStatus
)
from alpha.research.graph import ResearchGraph, ResearchEdgeType
from alpha.research.curiosity.unknown_detector import UnknownDetector
from alpha.research.curiosity.question_generator import QuestionGenerator
from alpha.research.hypotheses.generator import HypothesisGenerator
from alpha.research.experiments.planner import ExperimentPlanner
from alpha.research.experiments.simulator import ExperimentSimulator
from alpha.research.experiments.validator import ExperimentValidator
from alpha.research.evidence.ranking import EvidenceRankingEngine
from alpha.research.evidence.marketplace import EvidenceMarketplace
from alpha.research.theories.builder import TheoryBuilder
from alpha.research.theories.evaluator import TheoryEvaluator
from alpha.research.governance.pipeline import ResearchGovernancePipeline, GovernanceAuditResult
from alpha.research.agents.critic_agent import CriticAgent
from alpha.research.agents.replication_agent import ReplicationAgent
from alpha.research.agents.publication_agent import PublicationAgent
from alpha.research.knowledge_economy.ranker import KnowledgeAssetRanker


class DiscoveryCycleRecord(BaseModel):
    cycle_index: int
    domain: str
    question_text: str
    hypothesis_statement: str
    experiment_id: str
    evidence_count: int
    finding_claim: str
    replication_successful: bool
    theory_name: str
    publication_approved: bool
    new_questions_spawned: int
    duration_ms: float
    timestamp: float = Field(default_factory=time.time)


class ScientificDiscoveryLoop:
    """Orchestrates autonomous closed-loop scientific discovery."""

    def __init__(
        self,
        research_graph: Optional[ResearchGraph] = None,
        world_model: Optional[Any] = None,
        asset_ranker: Optional[KnowledgeAssetRanker] = None
    ):
        self.graph = research_graph or ResearchGraph()
        self.world_model = world_model
        self.asset_ranker = asset_ranker or KnowledgeAssetRanker()

        # Discovery subsystems
        self.unknown_detector = UnknownDetector(world_model=world_model, research_graph=self.graph)
        self.question_generator = QuestionGenerator()
        self.hypothesis_generator = HypothesisGenerator()
        self.experiment_planner = ExperimentPlanner()
        self.experiment_simulator = ExperimentSimulator()
        self.experiment_validator = ExperimentValidator()
        self.evidence_ranking = EvidenceRankingEngine()
        self.evidence_marketplace = EvidenceMarketplace()
        self.theory_builder = TheoryBuilder()
        self.theory_evaluator = TheoryEvaluator(min_replication_threshold=1)
        self.governance_pipeline = ResearchGovernancePipeline(world_model=world_model)

        # Scientific agents
        self.critic_agent = CriticAgent()
        self.replication_agent = ReplicationAgent()
        self.publication_agent = PublicationAgent()

        self.cycle_history: List[DiscoveryCycleRecord] = []

    def run_cycle(self, domain: Optional[str] = None, cycle_idx: int = 1) -> DiscoveryCycleRecord:
        """Execute one complete 8-stage scientific discovery loop."""
        start_t = time.time()
        target_domain = domain or "software"

        # Stage 1: Question Discovery (What do we not know?)
        unknowns = self.unknown_detector.detect_unknowns(domains=[target_domain])
        top_unknown = unknowns[0]
        problem = self.unknown_detector.convert_unknown_to_research_problem(top_unknown)
        self.graph.add_node(problem)

        questions = self.question_generator.generate_questions_from_problem(problem, count=1)
        question = questions[0]
        self.graph.add_node(question)
        self.graph.add_edge(question.question_id, problem.problem_id, ResearchEdgeType.ADDRESSES_PROBLEM)

        # Stage 2: Hypothesis Generation
        hypothesis = self.hypothesis_generator.generate_novel_hypothesis(question)
        self.graph.add_node(hypothesis)
        self.graph.add_edge(hypothesis.hypothesis_id, question.question_id, ResearchEdgeType.DERIVED_FROM_QUESTION)

        # Stage 3: Experiment Planning & Simulation
        experiment = self.experiment_planner.design_test(hypothesis, sample_size=80)
        self.experiment_validator.validate(experiment)
        self.graph.add_node(experiment)
        self.graph.add_edge(experiment.experiment_id, hypothesis.hypothesis_id, ResearchEdgeType.TESTED_BY_EXPERIMENT)

        sim_outcome = self.experiment_simulator.simulate(experiment)
        for obs in sim_outcome.observations[:5]:
            self.graph.add_node(obs)
            self.graph.add_edge(obs.observation_id, experiment.experiment_id, ResearchEdgeType.GENERATED_OBSERVATION)

        # Stage 4: Evidence Collection & Marketplace
        evidence = Evidence(
            hypothesis_id=hypothesis.hypothesis_id,
            experiment_id=experiment.experiment_id,
            observation_ids=[obs.observation_id for obs in sim_outcome.observations],
            confidence=round(min(0.98, 0.75 + 0.2 * sim_outcome.mean_effect_size), 3),
            p_value=sim_outcome.p_value,
            effect_size=sim_outcome.mean_effect_size,
            verifier_agent="ExperimentAgent"
        )
        self.graph.add_node(evidence)
        self.graph.add_edge(evidence.evidence_id, hypothesis.hypothesis_id, ResearchEdgeType.SUPPORTS_HYPOTHESIS)
        self.evidence_marketplace.list_evidence(evidence, seller_id="ExperimentAgent")

        # Stage 5: Evaluation & Mandatory Replication
        finding = Finding(
            hypothesis_id=hypothesis.hypothesis_id,
            claim=f"In {target_domain}, empirical intervention produces effect size {sim_outcome.mean_effect_size:.2f} (p={sim_outcome.p_value:.4f})",
            evidence_ids=[evidence.evidence_id],
            confidence=evidence.confidence
        )
        self.graph.add_node(finding)
        self.graph.add_edge(evidence.evidence_id, finding.finding_id, ResearchEdgeType.SUPPORTS_FINDING)

        # Critic stress testing
        self.critic_agent.stress_test_finding(finding, [evidence])

        # Mandatory Replication: "Research without replication is forbidden"
        replication = self.replication_agent.replicate_study(experiment, finding)
        self.graph.add_node(replication)
        self.graph.add_edge(replication.replication_id, experiment.experiment_id, ResearchEdgeType.REPLICATES_EXPERIMENT)

        # Stage 6: Theory Formulation & Evaluation
        theory = self.theory_builder.build_theory(
            name=f"Theory of {target_domain.capitalize()} Invariant Dynamics",
            domain=target_domain,
            findings=[finding],
            cross_domains=hypothesis.cross_domains
        )
        self.graph.add_node(theory)
        self.graph.add_edge(finding.finding_id, theory.theory_id, ResearchEdgeType.SYNTHESIZED_INTO_THEORY)

        audit_report = self.theory_evaluator.evaluate(theory, [finding])

        # Stage 7: Publication & 5-Layer Mandatory Governance
        publication = self.publication_agent.draft_publication(theory, [finding], [evidence])
        self.graph.add_node(publication)
        self.graph.add_edge(theory.theory_id, publication.publication_id, ResearchEdgeType.PUBLISHED_IN)

        gov_audit = self.governance_pipeline.execute_governance_audit(publication, [finding], [evidence])
        if gov_audit.approved and self.asset_ranker:
            self.asset_ranker.register_asset(
                title=publication.title,
                target_entity_type="Publication",
                target_entity_id=publication.publication_id,
                domain=publication.domain,
                value=0.90,
                novelty=publication.novelty_score,
                impact=publication.impact_score,
                confidence=publication.confidence,
                verification=1.0
            )

        # Stage 8: Spawn Follow-up Questions (The Continuous Cycle)
        followup_unknown = self.unknown_detector.detect_unknowns(domains=[target_domain])
        new_q_count = len(followup_unknown)

        duration = (time.time() - start_t) * 1000.0
        record = DiscoveryCycleRecord(
            cycle_index=cycle_idx,
            domain=target_domain,
            question_text=question.question_text,
            hypothesis_statement=hypothesis.statement,
            experiment_id=experiment.experiment_id,
            evidence_count=1,
            finding_claim=finding.claim,
            replication_successful=replication.is_successful,
            theory_name=theory.name,
            publication_approved=gov_audit.approved,
            new_questions_spawned=new_q_count,
            duration_ms=round(duration, 2)
        )
        self.cycle_history.append(record)
        return record

    def run_continuous_cycles(self, num_cycles: int = 5, domains: Optional[List[str]] = None) -> List[DiscoveryCycleRecord]:
        """Run multiple autonomous cycles sequentially without human intervention."""
        domain_list = domains or [
            "engineering", "software", "economics", "psychology",
            "biology", "physics", "mathematics", "design", "product_systems"
        ]
        records = []
        for i in range(num_cycles):
            d = domain_list[i % len(domain_list)]
            rec = self.run_cycle(domain=d, cycle_idx=i + 1)
            records.append(rec)
        return records
