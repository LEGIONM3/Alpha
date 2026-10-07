"""Tests for Phase 5 Research Entities and Research Graph."""

import pytest
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
    EvidencePolarity,
    EvidenceStrength
)
from alpha.research.graph import (
    ResearchGraph,
    ResearchEdgeType,
    ResearchEdge
)


def test_research_entities_instantiation():
    prob = ResearchProblem(
        title="Scalability bounds under network partition",
        description="Investigating Byzantine fault rates",
        domain="software",
        severity=0.8,
        epistemic_uncertainty=0.85
    )
    assert prob.problem_id.startswith("prob_")
    assert prob.severity == 0.8

    q = ResearchQuestion(
        problem_id=prob.problem_id,
        question_text="What is the critical percolation threshold?",
        domain="software",
        target_variables=["percolation_density", "consensus_latency"],
        falsifiability_criteria="Falsified if latency is constant."
    )
    assert q.question_id.startswith("q_")
    assert "percolation_density" in q.target_variables

    hyp = Hypothesis(
        question_id=q.question_id,
        statement="Latency scales as a power law with density.",
        rationale="Analogy with thermodynamic percolation.",
        domain="software",
        confidence=0.65
    )
    assert hyp.hypothesis_id.startswith("hyp_")
    assert hyp.status == ResearchStatus.PROPOSED

    exp = Experiment(
        hypothesis_id=hyp.hypothesis_id,
        title="Simulated cluster partition testing",
        protocol={"nodes": 100, "partition_ratio": 0.3},
        independent_variables=["partition_ratio"],
        dependent_variables=["latency"]
    )
    assert exp.experiment_id.startswith("exp_")
    assert exp.status == "DESIGNED"

    obs = Observation(
        experiment_id=exp.experiment_id,
        trial_index=1,
        metrics={"latency": 124.5, "delta": 0.82}
    )
    assert obs.observation_id.startswith("obs_")

    ev = Evidence(
        hypothesis_id=hyp.hypothesis_id,
        experiment_id=exp.experiment_id,
        observation_ids=[obs.observation_id],
        polarity=EvidencePolarity.SUPPORT,
        strength=EvidenceStrength.STRONG,
        confidence=0.88,
        p_value=0.005,
        effect_size=0.85
    )
    assert ev.evidence_id.startswith("ev_")
    assert len(ev.provenance_hash) > 0

    finding = Finding(
        hypothesis_id=hyp.hypothesis_id,
        claim="Latency exhibits power-law scaling above 0.28 partition threshold.",
        evidence_ids=[ev.evidence_id],
        confidence=0.85
    )
    assert finding.finding_id.startswith("fnd_")
    assert not finding.replicated

    pred = Prediction(
        source_entity_id=finding.finding_id,
        forecast_statement="Partition of 0.40 will produce latency > 200ms",
        expected_value=200.0
    )
    assert pred.prediction_id.startswith("pred_")

    thy = Theory(
        name="Theory of Partition Phase Transitions",
        description="Unified model of distributed systems under stress",
        domain="software",
        principles=["Percolation invariant", "Bounded consensus horizon"],
        finding_ids=[finding.finding_id]
    )
    assert thy.theory_id.startswith("thy_")

    rep = Replication(
        original_experiment_id=exp.experiment_id,
        finding_id=finding.finding_id,
        replicating_agent="ReplicationAgent",
        is_successful=True,
        deviation_percent=4.2
    )
    assert rep.is_successful

    ref = Refutation(
        target_entity_id=hyp.hypothesis_id,
        target_type="Hypothesis",
        author_agent="CriticAgent",
        argumentation="Counter-evidence demonstrates exponential rather than power law scaling."
    )
    assert ref.target_entity_id == hyp.hypothesis_id

    pub = Publication(
        title="Empirical Proof of Distributed Phase Transitions",
        abstract="We demonstrate phase transition scaling.",
        domain="software",
        author_agent="PublicationAgent",
        theory_ids=[thy.theory_id],
        finding_ids=[finding.finding_id],
        evidence_ids=[ev.evidence_id]
    )
    assert not pub.is_fully_verified()  # 5 layers not yet passed


def test_research_graph_operations_and_lineage():
    graph = ResearchGraph()

    prob = ResearchProblem(title="P1", description="D1", domain="physics")
    q = ResearchQuestion(question_text="Q1", domain="physics", problem_id=prob.problem_id)
    hyp = Hypothesis(statement="H1", rationale="R1", domain="physics", question_id=q.question_id)
    exp = Experiment(hypothesis_id=hyp.hypothesis_id, title="E1", protocol={})
    obs = Observation(experiment_id=exp.experiment_id, metrics={"val": 1.0})
    ev = Evidence(hypothesis_id=hyp.hypothesis_id, experiment_id=exp.experiment_id, observation_ids=[obs.observation_id])
    finding = Finding(hypothesis_id=hyp.hypothesis_id, claim="F1", evidence_ids=[ev.evidence_id])
    thy = Theory(name="T1", description="Desc1", domain="physics", finding_ids=[finding.finding_id])

    graph.add_node(prob)
    graph.add_node(q)
    graph.add_node(hyp)
    graph.add_node(exp)
    graph.add_node(obs)
    graph.add_node(ev)
    graph.add_node(finding)
    graph.add_node(thy)

    graph.add_edge(q.question_id, prob.problem_id, ResearchEdgeType.ADDRESSES_PROBLEM)
    graph.add_edge(hyp.hypothesis_id, q.question_id, ResearchEdgeType.DERIVED_FROM_QUESTION)
    graph.add_edge(exp.experiment_id, hyp.hypothesis_id, ResearchEdgeType.TESTED_BY_EXPERIMENT)
    graph.add_edge(obs.observation_id, exp.experiment_id, ResearchEdgeType.GENERATED_OBSERVATION)
    graph.add_edge(ev.evidence_id, hyp.hypothesis_id, ResearchEdgeType.SUPPORTS_HYPOTHESIS)
    graph.add_edge(finding.finding_id, thy.theory_id, ResearchEdgeType.SYNTHESIZED_INTO_THEORY)
    graph.add_edge(ev.evidence_id, finding.finding_id, ResearchEdgeType.SUPPORTS_FINDING)

    stats = graph.stats()
    assert stats["total_nodes"] == 8
    assert stats["total_edges"] == 7
    assert stats["node_types"]["Theory"] == 1
    assert stats["node_types"]["Hypothesis"] == 1

    # Check incoming / outgoing
    outgoing = graph.get_outgoing(hyp.hypothesis_id)
    assert len(outgoing) == 1
    assert outgoing[0].edge_type == ResearchEdgeType.DERIVED_FROM_QUESTION

    incoming = graph.get_incoming(hyp.hypothesis_id)
    assert len(incoming) == 2  # exp and ev

    # Lineage check from Theory backwards
    lineage = graph.get_lineage(thy.theory_id)
    assert len(lineage) >= 2
