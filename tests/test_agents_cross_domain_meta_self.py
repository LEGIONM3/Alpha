"""Tests for Scientific Agents, Cross-Domain Framework, Meta-Research, and Alpha Self-Research."""

import pytest
from alpha.research.agents import (
    LiteratureAgent,
    HypothesisAgent,
    ExperimentAgent,
    CriticAgent,
    ReplicationAgent,
    PublicationAgent,
    MetaResearchAgent
)
from alpha.research.cross_domain import (
    CANONICAL_DOMAINS,
    DomainRegistry,
    CrossDomainSynthesizer
)
from alpha.research.knowledge_economy import (
    KnowledgeAssetRanker
)
from alpha.research.meta_research import (
    ResearchArchives,
    TheoryEvolutionGraph,
    MethodologyEvaluator
)
from alpha.research.competition import (
    ScientificArena
)
from alpha.research.self_research import (
    AlphaSelfResearchBranch
)
from alpha.research.entities import (
    ResearchQuestion,
    Hypothesis,
    Finding,
    Theory,
    Evidence
)


def test_specialized_discovery_agents_collaboration():
    lit_agent = LiteratureAgent()
    hyp_agent = HypothesisAgent()
    exp_agent = ExperimentAgent()
    critic_agent = CriticAgent()
    rep_agent = ReplicationAgent()
    pub_agent = PublicationAgent()
    meta_agent = MetaResearchAgent()

    # Literature survey
    survey = lit_agent.survey_domain("biology")
    assert "established_foundations" in survey

    # Propose hypothesis
    q = ResearchQuestion(question_text="How do cells balance ATP?", domain="biology", target_variables=["ATP", "metabolism"])
    hyp = hyp_agent.propose_hypothesis(q)
    assert hyp.domain == "biology"

    # Critic critique
    critique = critic_agent.critique_hypothesis(hyp)
    assert len(critique["counterarguments"]) > 0

    # Experiment execution
    campaign = exp_agent.run_experimental_campaign(hyp, sample_size=40)
    assert campaign["experiment"] is not None
    assert campaign["evidence"] is not None

    # Finding & Replication
    finding = Finding(hypothesis_id=hyp.hypothesis_id, claim="ATP balance regulates homeostasis.", evidence_ids=[campaign["evidence"].evidence_id])
    rep = rep_agent.replicate_study(campaign["experiment"], finding)
    assert rep.is_successful
    assert finding.replicated

    # Draft publication
    thy = Theory(name="ATP Homeostasis", description="Cellular energy balance", domain="biology", finding_ids=[finding.finding_id])
    pub = pub_agent.draft_publication(thy, [finding], [campaign["evidence"]])
    assert pub.title.startswith("Theoretical and Empirical Foundations")

    # Meta-Research evaluation
    meta_eval = meta_agent.analyze_research_performance(10, 10, 10, 5)
    assert "best_performing_method" in meta_eval


def test_cross_domain_registry_and_100_plus_domains():
    reg = DomainRegistry()
    assert reg.count_domains() >= 100
    all_domains = reg.list_all_domains()
    assert len(all_domains) >= 100

    # Test all 9 canonical domains exist
    for canonical in CANONICAL_DOMAINS:
        assert canonical in all_domains

    # Test synthesis
    synthesizer = CrossDomainSynthesizer(registry=reg)
    synth_res = synthesizer.synthesize("biology", "software")
    assert synth_res.primary_domain == "biology"
    assert "immune" in synth_res.bridging_principle.lower() or "isomorphic" in synth_res.bridging_principle.lower()


def test_knowledge_economy_and_arena():
    ranker = KnowledgeAssetRanker()
    asset1 = ranker.register_asset("Asset A", "Theory", "thy_1", "software", value=0.9, novelty=0.95, impact=0.85)
    asset2 = ranker.register_asset("Asset B", "Theory", "thy_2", "physics", value=0.7, novelty=0.6, impact=0.5)

    ranked = ranker.get_ranked_assets()
    assert ranked[0].asset_id == asset1.asset_id

    arena = ScientificArena()
    h1 = Hypothesis(statement="H1 wins", domain="software", confidence=0.9)
    h2 = Hypothesis(statement="H2 loses", domain="software", confidence=0.4)
    ev = Evidence(hypothesis_id=h1.hypothesis_id, experiment_id="exp_1", confidence=0.95, p_value=0.001, effect_size=1.0)

    tourney = arena.compete_hypotheses([h1, h2], {h1.hypothesis_id: [ev], h2.hypothesis_id: []})
    assert tourney.winner_id == h1.hypothesis_id


def test_meta_research_archives_and_self_research():
    archives = ResearchArchives()
    evo_graph = TheoryEvolutionGraph()

    t_node = evo_graph.record_genesis("thy_orig", "Classical Model", "software")
    rev_node = evo_graph.record_revision("thy_orig", "thy_rev", "Quantum Model", version=2)
    lineage = evo_graph.get_lineage("thy_rev")
    assert lineage == ["thy_orig"]

    evaluator = MethodologyEvaluator()
    methods = evaluator.which_methods_work_best()
    assert len(methods) > 0
    failures = evaluator.which_experiments_fail_most()
    assert len(failures) > 0
    survival = evaluator.which_theories_survive_longest()
    assert "top_surviving_archetype" in survival
    speedup = evaluator.how_does_alpha_learn_faster()
    assert speedup["epistemic_velocity_multiplier"] > 1.0

    # Alpha Self-Research
    self_res = AlphaSelfResearchBranch()
    cycle_res = self_res.run_self_research_cycle()
    assert cycle_res["thrusts_investigated"] == 5
    assert cycle_res["all_safety_certified"]
