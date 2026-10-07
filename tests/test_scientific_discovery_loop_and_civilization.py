"""Tests for Scientific Discovery Loop and Research Civilization Master Facade."""

import pytest
from alpha.research.loops import ScientificDiscoveryLoop
from alpha.research.civilization import ResearchCivilization
from alpha.operating_system import AlphaOperatingSystem


def test_scientific_discovery_loop_single_cycle():
    loop = ScientificDiscoveryLoop()
    record = loop.run_cycle(domain="economics", cycle_idx=1)

    assert record.cycle_index == 1
    assert record.domain == "economics"
    assert len(record.question_text) > 0
    assert len(record.hypothesis_statement) > 0
    assert record.replication_successful
    assert record.publication_approved
    assert record.new_questions_spawned > 0


def test_scientific_discovery_loop_continuous_cycles():
    loop = ScientificDiscoveryLoop()
    records = loop.run_continuous_cycles(num_cycles=3, domains=["software", "biology", "physics"])

    assert len(records) == 3
    for rec in records:
        assert rec.replication_successful
        assert rec.publication_approved


def test_research_civilization_master_facade():
    civilization = ResearchCivilization()

    # 1. Proactive question discovery
    questions = civilization.discover_questions(domain="psychology", count=2)
    assert len(questions) == 2

    # 2. Formulate hypotheses & rivals
    hyp_bundle = civilization.formulate_hypotheses(questions[0], count_rivals=2)
    assert hyp_bundle["primary_hypothesis"] is not None
    assert len(hyp_bundle["rival_hypotheses"]) == 2

    # 3. Empirical campaign
    camp = civilization.run_empirical_campaign(hyp_bundle["primary_hypothesis"], sample_size=50)
    assert camp["experiment"] is not None
    assert camp["evidence"] is not None

    # 4. Independent replication
    finding = civilization.graph.get_nodes_by_type("Finding")
    # create finding for study
    from alpha.research.entities import Finding
    f = Finding(
        hypothesis_id=hyp_bundle["primary_hypothesis"].hypothesis_id,
        claim="Attention span degrades with cognitive friction.",
        evidence_ids=[camp["evidence"].evidence_id]
    )
    rep = civilization.replicate_study(camp["experiment"], f)
    assert rep.is_successful

    # 5. Synthesize & publish with 5-layer governance
    pub_result = civilization.synthesize_and_publish(
        name="Cognitive Attention Invariants",
        domain="psychology",
        findings=[f],
        evidence_list=[camp["evidence"]]
    )
    assert pub_result["governance_audit"].approved
    assert pub_result["publication"].is_fully_verified()

    # 6. Capture telemetry
    telemetry = civilization.get_civilization_telemetry()
    assert telemetry.total_nodes > 0
    assert telemetry.total_publications >= 1
    assert telemetry.domains_active >= 100


def test_alpha_operating_system_research_integration():
    alpha_os = AlphaOperatingSystem()
    assert hasattr(alpha_os, "research_civilization")

    # Autonomous discovery cycle via Alpha OS
    record = alpha_os.run_autonomous_discovery_cycle(domain="software")
    assert record.publication_approved
    assert record.replication_successful

    # Self-research
    prop = alpha_os.self_research_architecture("NEW_REASONING")
    assert prop.thrust == "NEW_REASONING"
    assert prop.governance_approved

    # Telemetry
    telemetry = alpha_os.get_research_telemetry()
    assert telemetry.total_nodes > 0
