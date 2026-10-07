"""Tests for Evidence, Theory Engine, and 5-Layer Governance Pipeline."""

import pytest
from alpha.research.evidence import (
    EvidenceMarketplace,
    EvidenceRankingEngine,
    EvidenceProvenanceChain,
    EvidenceConflictResolver,
    EvidenceTrustModel
)
from alpha.research.theories import (
    TheoryBuilder,
    TheoryEvaluator,
    TheoryRefiner,
    TheoryRetirement
)
from alpha.research.governance import (
    ResearchGovernancePipeline
)
from alpha.research.entities import (
    Evidence,
    Finding,
    Theory,
    Publication,
    EvidencePolarity,
    EvidenceStrength,
    ResearchStatus
)


def test_evidence_marketplace_and_provenance():
    ev = Evidence(
        hypothesis_id="hyp_1",
        experiment_id="exp_1",
        confidence=0.9,
        p_value=0.01,
        effect_size=0.8
    )
    market = EvidenceMarketplace()
    market.set_balance("agent_A", 100.0)

    listing = market.list_evidence(ev, seller_id="ExperimentAgent")
    stake = market.stake_on_evidence(ev.evidence_id, "agent_A", 30.0)
    assert stake is not None
    assert listing.total_staked == 30.0

    # Settle market on successful replication
    settlement = market.settle_market(ev.evidence_id, replicated_valid=True)
    assert settlement["replicated_valid"]
    assert settlement["payouts"]["agent_A"] == 45.0  # 1.5x payout

    # Provenance Chain
    chain = EvidenceProvenanceChain(chain_id="ch_1", hypothesis_id="hyp_1")
    chain.add_link("OBSERVATION", "obs_1", {"metric": 42})
    chain.add_link("EVIDENCE", ev.evidence_id, ev.model_dump())
    assert chain.verify_integrity()


def test_evidence_conflict_resolution_and_trust_invariant():
    ev_support = Evidence(
        hypothesis_id="hyp_target",
        experiment_id="exp_s",
        polarity=EvidencePolarity.SUPPORT,
        confidence=0.92,
        p_value=0.002,
        effect_size=1.1
    )
    ev_refute = Evidence(
        hypothesis_id="hyp_target",
        experiment_id="exp_r",
        polarity=EvidencePolarity.REFUTE,
        confidence=0.55,
        p_value=0.04,
        effect_size=-0.3
    )

    resolver = EvidenceConflictResolver()
    verdict = resolver.resolve_conflicts("hyp_target", [ev_support, ev_refute])
    assert verdict.resolved
    assert verdict.dominant_polarity == EvidencePolarity.SUPPORT
    assert verdict.recommendation == "ADOPT"

    trust_model = EvidenceTrustModel()
    profile = trust_model.get_or_create_profile("AgentX")
    trust_model.record_outcome("AgentX", was_replicated=True)
    assert profile.replicated_valid_count == 1

    # Invariant: No theory may exist without evidence
    thy_empty = Theory(name="Empty", description="No findings", domain="software")
    assert not trust_model.verify_theory_has_evidence(thy_empty, {})


def test_theory_builder_evaluator_refiner_retirement():
    builder = TheoryBuilder()
    finding = Finding(
        hypothesis_id="hyp_alpha",
        claim="Decentralized backoff reduces packet collision by 42%.",
        evidence_ids=["ev_1"],
        replicated=True,
        replication_count=1,
        adversarial_tested=True,
        confidence=0.88
    )

    thy = builder.build_theory(
        name="Theory of Adaptive Network Backoff",
        domain="software",
        findings=[finding]
    )
    assert thy.theory_id.startswith("thy_")
    assert len(thy.principles) > 0
    assert "trigger_condition" in thy.causal_mechanisms

    # Evaluator: Replication check
    evaluator = TheoryEvaluator(min_replication_threshold=1)
    audit = evaluator.evaluate(thy, [finding])
    assert audit.approved
    assert audit.replication_audit_passed
    assert thy.status == ResearchStatus.SUPPORTED

    # Refiner
    refiner = TheoryRefiner()
    new_finding = Finding(hypothesis_id="hyp_beta", claim="Edge caching amplifies backoff.", replicated=True)
    refined_thy = refiner.refine_theory(thy, [new_finding])
    assert refined_thy.version == 2
    assert len(refined_thy.finding_ids) == 2

    # Retirement
    retire = TheoryRetirement()
    refutation = retire.retire_theory(thy, reason="Superseded by Quantum Routing paradigm")
    assert thy.status == ResearchStatus.RETIRED
    assert refutation.author_agent == "CriticAgent"


def test_mandatory_5_layer_governance_pipeline():
    gov_pipe = ResearchGovernancePipeline()

    finding = Finding(
        hypothesis_id="hyp_governed",
        claim="Resilience invariant confirmed.",
        replicated=True,
        replication_count=2,
        adversarial_tested=True
    )
    ev = Evidence(
        hypothesis_id="hyp_governed",
        experiment_id="exp_gov",
        confidence=0.89,
        p_value=0.005,
        effect_size=0.8
    )
    pub = Publication(
        title="Verified Discovery in Software Resilience",
        abstract="We demonstrate verified distributed resilience invariants.",
        domain="software",
        author_agent="PublicationAgent",
        finding_ids=[finding.finding_id],
        evidence_ids=[ev.evidence_id],
        confidence=0.90
    )

    result = gov_pipe.execute_governance_audit(pub, [finding], [ev])
    assert result.approved
    assert pub.is_fully_verified()
    assert result.cryptographic_signature is not None
    assert pub.governance_signature is not None

    # Check failure if unreplicated
    unreplicated_finding = Finding(hypothesis_id="hyp_bad", claim="Unreplicated", replicated=False)
    pub_bad = Publication(
        title="Unverified claim",
        abstract="Unverified claim abstract",
        domain="software",
        author_agent="PublicationAgent",
        finding_ids=[unreplicated_finding.finding_id],
        evidence_ids=[ev.evidence_id]
    )
    fail_result = gov_pipe.execute_governance_audit(pub_bad, [unreplicated_finding], [ev])
    assert not fail_result.approved
    assert not pub_bad.passed_replication_layer
