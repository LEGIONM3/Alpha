"""Research Civilization: The Master Engine of Autonomous Scientific Discovery for Project Alpha.

Coordinates:
- Curiosity & Frontier Mapping
- Hypothesis Generation & Competition
- Experiment Planning, Simulation & Validation
- Evidence Marketplace, Chains & Trust Models
- Theory Building, Evaluation, Refinement & Retirement
- 7 Specialized Scientific Discovery Agents
- 9 Canonical Domains + 100+ Research Subdomains
- Knowledge Resource Economy & Asset Ranking
- 5-Layer Mandatory Research Governance (Truth, Governance, Identity, Drift, Replication)
- Meta-Research & Intellectual History Preservation
- Recursive Alpha Self-Research
- Continuous Autonomous Discovery Loops
"""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# Entities & Graph
from alpha.research.entities import (
    ResearchProblem,
    ResearchQuestion,
    Hypothesis,
    Experiment,
    Observation,
    Evidence,
    Finding,
    Theory,
    Prediction,
    Publication,
    Replication,
    Refutation,
    ResearchStatus,
    EvidencePolarity
)
from alpha.research.graph import ResearchGraph, ResearchEdgeType

# Curiosity
from alpha.research.curiosity import (
    UnknownDetector,
    KnowledgeFrontierMapper,
    QuestionGenerator,
    ResearchPrioritizer,
)

# Hypotheses
from alpha.research.hypotheses import (
    HypothesisGenerator,
    HypothesisCompetitionManager,
)

# Experiments
from alpha.research.experiments import (
    ExperimentPlanner,
    ExperimentSimulator,
    ExperimentValidator,
)

# Evidence
from alpha.research.evidence import (
    EvidenceMarketplace,
    EvidenceRankingEngine,
    EvidenceProvenanceChain,
    EvidenceConflictResolver,
    EvidenceTrustModel,
)

# Theories
from alpha.research.theories import (
    TheoryBuilder,
    TheoryEvaluator,
    TheoryRefiner,
    TheoryRetirement,
)

# Specialized Discovery Agents
from alpha.research.agents import (
    LiteratureAgent,
    HypothesisAgent,
    ExperimentAgent,
    CriticAgent,
    ReplicationAgent,
    PublicationAgent,
    MetaResearchAgent,
)

# Cross-Domain Framework
from alpha.research.cross_domain import (
    CANONICAL_DOMAINS,
    DomainRegistry,
    CrossDomainSynthesizer,
)

# Knowledge Economy
from alpha.research.knowledge_economy import (
    KnowledgeAsset,
    KnowledgeAssetRanker,
)

# Governance
from alpha.research.governance import (
    ResearchGovernancePipeline,
    GovernanceAuditResult,
)

# Meta-Research
from alpha.research.meta_research import (
    ResearchArchives,
    TheoryEvolutionGraph,
    MethodologyEvaluator,
)

# Competition
from alpha.research.competition import (
    ScientificArena,
    CompetitionTournamentResult,
)

# Feedback & Self-Research
from alpha.research.feedback import (
    ResearchWorldModelBridge,
    WorldModelFeedbackSummary,
)
from alpha.research.self_research import (
    AlphaSelfResearchBranch,
    ArchitecturalProposal,
)

# Discovery Loops
from alpha.research.loops import (
    ScientificDiscoveryLoop,
    DiscoveryCycleRecord,
)


class ResearchCivilizationTelemetry(BaseModel):
    total_nodes: int
    total_edges: int
    total_problems: int
    total_questions: int
    total_hypotheses: int
    total_experiments: int
    total_observations: int
    total_evidence: int
    total_findings: int
    total_theories: int
    total_publications: int
    total_replications: int
    domains_active: int
    global_epistemic_entropy: float
    knowledge_assets_ranked: int
    autonomous_cycles_completed: int
    timestamp: float = Field(default_factory=time.time)


class ResearchCivilization:
    """Master Architecture Facade for Project Alpha's Phase 5 Research Civilization."""

    def __init__(
        self,
        world_model: Optional[Any] = None,
        change_governance: Optional[Any] = None
    ):
        self.world_model = world_model
        self.change_governance = change_governance
        self._lock = threading.RLock()

        # 1. Knowledge Graph Core
        self.graph = ResearchGraph()

        # 2. Curiosity Engine
        self.unknown_detector = UnknownDetector(world_model=world_model, research_graph=self.graph)
        self.frontier_mapper = KnowledgeFrontierMapper(research_graph=self.graph)
        self.question_generator = QuestionGenerator()
        self.prioritizer = ResearchPrioritizer()

        # 3. Hypotheses
        self.hypothesis_generator = HypothesisGenerator()
        self.hypothesis_competition = HypothesisCompetitionManager()

        # 4. Experiments
        self.experiment_planner = ExperimentPlanner()
        self.experiment_simulator = ExperimentSimulator()
        self.experiment_validator = ExperimentValidator()

        # 5. Evidence
        self.evidence_marketplace = EvidenceMarketplace()
        self.evidence_ranking = EvidenceRankingEngine()
        self.evidence_conflict_resolver = EvidenceConflictResolver()
        self.evidence_trust_model = EvidenceTrustModel()

        # 6. Theories
        self.theory_builder = TheoryBuilder()
        self.theory_evaluator = TheoryEvaluator(min_replication_threshold=1)
        self.theory_refiner = TheoryRefiner()
        self.theory_retirement = TheoryRetirement()

        # 7. Specialized Scientific Agents
        self.literature_agent = LiteratureAgent()
        self.hypothesis_agent = HypothesisAgent()
        self.experiment_agent = ExperimentAgent()
        self.critic_agent = CriticAgent()
        self.replication_agent = ReplicationAgent()
        self.publication_agent = PublicationAgent()
        self.meta_research_agent = MetaResearchAgent()

        # 8. Cross-Domain (100+ Domains)
        self.domain_registry = DomainRegistry()
        self.cross_domain_synthesizer = CrossDomainSynthesizer(registry=self.domain_registry)

        # 9. Knowledge Economy
        self.asset_ranker = KnowledgeAssetRanker()

        # 10. Governance (5-Layer Inviolable Gate)
        self.governance_pipeline = ResearchGovernancePipeline(world_model=world_model)

        # 11. Meta-Research & Archives
        self.archives = ResearchArchives()
        self.theory_evolution_graph = TheoryEvolutionGraph()
        self.methodology_evaluator = MethodologyEvaluator()

        # 12. Scientific Arena
        self.arena = ScientificArena()

        # 13. Feedback & Self-Research
        self.world_model_bridge = ResearchWorldModelBridge(world_model=world_model)
        self.self_research_branch = AlphaSelfResearchBranch(governance_system=change_governance)

        # 14. Discovery Loop Engine
        self.discovery_loop = ScientificDiscoveryLoop(
            research_graph=self.graph,
            world_model=world_model,
            asset_ranker=self.asset_ranker
        )

    # -------------------------------------------------------------------------
    # Core Autonomous Discovery Interfaces
    # -------------------------------------------------------------------------

    def discover_questions(self, domain: str = "software", count: int = 3) -> List[ResearchQuestion]:
        """Proactively detects unknowns and generates prioritized falsifiable questions."""
        with self._lock:
            unknowns = self.unknown_detector.detect_unknowns(domains=[domain])
            top_unk = unknowns[0] if unknowns else None
            if not top_unk:
                return []
            prob = self.unknown_detector.convert_unknown_to_research_problem(top_unk)
            self.graph.add_node(prob)
            self.prioritizer.add_problem(prob)

            questions = self.question_generator.generate_questions_from_problem(prob, count=count)
            for q in questions:
                self.graph.add_node(q)
                self.graph.add_edge(q.question_id, prob.problem_id, ResearchEdgeType.ADDRESSES_PROBLEM)
                self.prioritizer.add_question(q)
            return questions

    def formulate_hypotheses(self, question: ResearchQuestion, count_rivals: int = 2) -> Dict[str, Any]:
        """Formulate novel hypothesis, search literature prior art, and generate competing rivals."""
        with self._lock:
            # Check literature
            lit_check = self.literature_agent.check_prior_art(question.question_text, question.domain)

            # Generate primary hypothesis
            primary = self.hypothesis_agent.propose_hypothesis(question)
            self.graph.add_node(primary)
            self.graph.add_edge(primary.hypothesis_id, question.question_id, ResearchEdgeType.DERIVED_FROM_QUESTION)

            # Generate rivals
            rivals = self.hypothesis_agent.propose_rivals(primary, count=count_rivals)
            for r in rivals:
                self.graph.add_node(r)
                self.graph.add_edge(r.hypothesis_id, question.question_id, ResearchEdgeType.DERIVED_FROM_QUESTION)

            # Critic review
            critique = self.critic_agent.critique_hypothesis(primary)

            return {
                "question": question,
                "literature_check": lit_check,
                "primary_hypothesis": primary,
                "rival_hypotheses": rivals,
                "adversarial_critique": critique
            }

    def run_empirical_campaign(
        self,
        hypothesis: Hypothesis,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """Execute experiment campaign via ExperimentAgent."""
        with self._lock:
            result = self.experiment_agent.run_experimental_campaign(hypothesis, sample_size=sample_size)
            exp = result["experiment"]
            ev = result["evidence"]

            if exp:
                self.graph.add_node(exp)
                self.graph.add_edge(exp.experiment_id, hypothesis.hypothesis_id, ResearchEdgeType.TESTED_BY_EXPERIMENT)

            if ev:
                self.graph.add_node(ev)
                self.graph.add_edge(ev.evidence_id, hypothesis.hypothesis_id, ResearchEdgeType.SUPPORTS_HYPOTHESIS)
                self.evidence_marketplace.list_evidence(ev, seller_id=self.experiment_agent.agent_id)

            return result

    def replicate_study(self, experiment: Experiment, finding: Finding) -> Replication:
        """Mandatory Replication: Replicate study with independent ReplicationAgent."""
        with self._lock:
            rep = self.replication_agent.replicate_study(experiment, finding)
            self.graph.add_node(rep)
            self.graph.add_edge(rep.replication_id, experiment.experiment_id, ResearchEdgeType.REPLICATES_EXPERIMENT)
            self.evidence_trust_model.record_outcome(rep.replicating_agent, rep.is_successful)
            return rep

    def synthesize_and_publish(
        self,
        name: str,
        domain: str,
        findings: List[Finding],
        evidence_list: List[Evidence],
        cross_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Build theory, audit replication, draft publication, and run 5-layer governance audit."""
        with self._lock:
            # 1. Build theory
            theory = self.theory_builder.build_theory(
                name=name,
                domain=domain,
                findings=findings,
                cross_domains=cross_domains
            )
            self.graph.add_node(theory)
            for f in findings:
                self.graph.add_edge(f.finding_id, theory.theory_id, ResearchEdgeType.SYNTHESIZED_INTO_THEORY)

            # Record genealogy
            self.theory_evolution_graph.record_genesis(theory.theory_id, theory.name, theory.domain)

            # 2. Evaluate theory
            theory_audit = self.theory_evaluator.evaluate(theory, findings)

            # 3. Draft publication
            pub = self.publication_agent.draft_publication(theory, findings, evidence_list)
            self.graph.add_node(pub)
            self.graph.add_edge(theory.theory_id, pub.publication_id, ResearchEdgeType.PUBLISHED_IN)

            # 4. Mandatory 5-Layer Governance
            gov_audit = self.governance_pipeline.execute_governance_audit(pub, findings, evidence_list)

            # 5. Archive & Rank Knowledge Asset if approved
            if gov_audit.approved:
                self.archives.archive_publication(pub)
                asset = self.asset_ranker.register_asset(
                    title=pub.title,
                    target_entity_type="Publication",
                    target_entity_id=pub.publication_id,
                    domain=pub.domain,
                    value=0.92,
                    novelty=pub.novelty_score,
                    impact=pub.impact_score,
                    confidence=pub.confidence,
                    verification=1.0
                )
                # Advance frontier
                self.frontier_mapper.record_advancement(domain, delta_theories=1, delta_findings=len(findings))
                # Propagate to world model
                wm_summary = self.world_model_bridge.propagate_discovery_to_world_model(pub, [theory], findings)
            else:
                wm_summary = None

            return {
                "theory": theory,
                "theory_audit": theory_audit,
                "publication": pub,
                "governance_audit": gov_audit,
                "world_model_summary": wm_summary
            }

    def run_autonomous_discovery_mode(self, num_cycles: int = 3, domains: Optional[List[str]] = None) -> List[DiscoveryCycleRecord]:
        """Final autonomous test: Alpha runs without user tasks, continuously expanding the frontier."""
        with self._lock:
            return self.discovery_loop.run_continuous_cycles(num_cycles=num_cycles, domains=domains)

    def self_research(self, thrust: str = "NEW_ARCHITECTURE") -> ArchitecturalProposal:
        """Alpha researches future Alpha."""
        with self._lock:
            return self.self_research_branch.investigate_future_architecture(thrust)

    def get_civilization_telemetry(self) -> ResearchCivilizationTelemetry:
        """Capture comprehensive state of the Research Civilization."""
        with self._lock:
            g_stats = self.graph.stats()
            nt = g_stats["node_types"]
            f_map = self.frontier_mapper.generate_frontier_map()

            return ResearchCivilizationTelemetry(
                total_nodes=g_stats["total_nodes"],
                total_edges=g_stats["total_edges"],
                total_problems=nt.get("ResearchProblem", 0),
                total_questions=nt.get("ResearchQuestion", 0),
                total_hypotheses=nt.get("Hypothesis", 0),
                total_experiments=nt.get("Experiment", 0),
                total_observations=nt.get("Observation", 0),
                total_evidence=nt.get("Evidence", 0),
                total_findings=nt.get("Finding", 0),
                total_theories=nt.get("Theory", 0),
                total_publications=nt.get("Publication", 0),
                total_replications=nt.get("Replication", 0),
                domains_active=self.domain_registry.count_domains(),
                global_epistemic_entropy=f_map.global_epistemic_entropy,
                knowledge_assets_ranked=len(self.asset_ranker.assets),
                autonomous_cycles_completed=len(self.discovery_loop.cycle_history)
            )
