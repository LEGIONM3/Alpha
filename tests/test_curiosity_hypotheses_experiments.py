"""Tests for Curiosity Engine, Hypothesis Generation, and Experimentation Subsystems."""

import pytest
from alpha.research.curiosity import (
    UnknownDetector,
    KnowledgeFrontierMapper,
    QuestionGenerator,
    ResearchPrioritizer
)
from alpha.research.hypotheses import (
    HypothesisGenerator,
    HypothesisCompetitionManager
)
from alpha.research.experiments import (
    ExperimentPlanner,
    ExperimentSimulator,
    ExperimentValidator
)
from alpha.research.entities import (
    ResearchProblem,
    Hypothesis,
    ResearchQuestion,
    Evidence,
    EvidencePolarity,
    ResearchStatus
)


def test_unknown_detector_and_curiosity_questions():
    detector = UnknownDetector()
    unknowns = detector.detect_unknowns(domains=["software", "biology", "economics"])
    assert len(unknowns) >= 3

    # Check categories
    categories = {u.category for u in unknowns}
    assert "VOID" in categories
    assert "CONTRADICTION" in categories
    assert "HIGH_UNCERTAINTY" in categories
    assert "CRITICAL_DEPENDENCY" in categories

    # Promotion to ResearchProblem
    prob = detector.convert_unknown_to_research_problem(unknowns[0])
    assert prob.problem_id.startswith("prob_")
    assert prob.epistemic_uncertainty > 0


def test_frontier_mapper_and_prioritizer():
    mapper = KnowledgeFrontierMapper()
    f_map = mapper.generate_frontier_map(domains=["software", "physics"])
    assert "software" in f_map.domains
    assert 0.0 < f_map.global_epistemic_entropy <= 1.0

    # Advance frontier
    mapper.record_advancement("software", delta_theories=2, delta_findings=5)
    updated_map = mapper.generate_frontier_map(domains=["software"])
    assert updated_map.domains["software"].verified_theories_count >= 4

    prioritizer = ResearchPrioritizer()
    q1 = ResearchQuestion(question_text="Q1", domain="software", epistemic_priority=0.9)
    q2 = ResearchQuestion(question_text="Q2", domain="physics", epistemic_priority=0.6)
    prioritizer.add_question(q1)
    prioritizer.add_question(q2)

    top_qs = prioritizer.get_highest_priority_questions(limit=1)
    assert len(top_qs) == 1
    assert top_qs[0].question_id == q1.question_id

    summary = prioritizer.get_backlog_summary()
    assert summary["total_questions"] == 2
    assert summary["top_priority_score"] > 0


def test_question_generator():
    generator = QuestionGenerator()
    q_list = generator.generate_questions_from_problem(
        ResearchProblem(title="P_Alpha", description="Alpha desc", domain="economics"),
        count=3
    )
    assert len(q_list) == 3
    for q in q_list:
        assert len(q.target_variables) > 0
        assert len(q.falsifiability_criteria) > 0

    agenda = generator.generate_research_agenda(q_list)
    assert agenda["total_questions"] == 3
    assert "economics" in agenda["domains_covered"]


def test_hypothesis_generator_and_competition():
    generator = HypothesisGenerator()
    q = ResearchQuestion(
        question_text="How does memory load affect reasoning speed?",
        domain="software",
        target_variables=["memory_pressure", "latency"]
    )
    # 1. Novel hypothesis
    hyp = generator.generate_novel_hypothesis(q)
    assert hyp.hypothesis_id.startswith("hyp_")
    assert hyp.domain == "software"
    assert len(hyp.cross_domains) > 0
    assert hyp.novelty_score >= 0.70

    # 2. Competing rival hypotheses
    rivals = generator.generate_competing_hypotheses(hyp, count=2)
    assert len(rivals) == 2
    assert hyp.hypothesis_id in rivals[0].competing_hypotheses

    # 3. Competition Arena
    comp_mgr = HypothesisCompetitionManager()
    match = comp_mgr.register_competition(hyp, rivals[0])
    assert not match.settled

    # Feed evidence favoring hyp
    ev = Evidence(
        hypothesis_id=hyp.hypothesis_id,
        experiment_id="exp_test",
        polarity=EvidencePolarity.SUPPORT,
        confidence=0.95,
        p_value=0.001,
        effect_size=1.2
    )
    updated_match = comp_mgr.evaluate_evidence_for_match(
        f"{hyp.hypothesis_id}_vs_{rivals[0].hypothesis_id}",
        hyp,
        rivals[0],
        [ev]
    )
    assert updated_match.settled
    assert updated_match.winner_id == hyp.hypothesis_id
    assert hyp.status == ResearchStatus.SUPPORTED
    assert rivals[0].status == ResearchStatus.REFUTED


def test_experiment_planner_simulator_and_validator():
    hyp = Hypothesis(
        statement="Dynamic cache resizing prevents latency spikes.",
        rationale="Analogy with metabolic regulation.",
        domain="software",
        confidence=0.75
    )
    planner = ExperimentPlanner()
    exp = planner.design_test(hyp, sample_size=60)
    assert exp.experiment_id.startswith("exp_")
    assert exp.sample_size == 60
    assert exp.estimated_cost > 0
    assert exp.status == "DESIGNED"

    validator = ExperimentValidator()
    report = validator.validate(exp)
    assert report.is_valid
    assert exp.status == "VALIDATED"

    simulator = ExperimentSimulator(random_seed=123)
    outcome = simulator.simulate(exp, trials=25)
    assert outcome.trials_completed == 25
    assert len(outcome.observations) == 25
    assert outcome.statistical_significance_achieved
    assert outcome.mean_effect_size > 0
    assert exp.status == "SIMULATED"
