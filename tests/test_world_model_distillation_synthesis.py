"""Tests for Knowledge Distillation (Part 9), Concept Formation (Part 10), and Knowledge Synthesis (Part 11)."""

import pytest
import time
from alpha.world_model.distillation import (
    CompressionEngine,
    AbstractionEngine,
    PatternExtractionEngine,
    DistillationEngine,
)
from alpha.world_model.concepts import (
    ConceptDiscoveryEngine,
    TaxonomyBuilder,
)
from alpha.world_model.synthesis import (
    KnowledgeSynthesisEngine,
    SynthesizedInsight,
)
from alpha.world_model.ontology import ToolEntity, ConceptEntity


def test_distillation_1000_memories_to_10_concepts():
    """Verify transforming 1,000 memories into 10 high-level ConceptEntities."""
    engine = DistillationEngine()

    memories = [
        {"id": f"mem_{i}", "content": f"Memory event regarding cache lookup index {i % 10}", "tag": f"cache_{i%5}"}
        for i in range(1000)
    ]
    assert len(memories) == 1000

    concepts = engine.distill_memories_to_concepts(memories, target_concept_count=10)
    assert len(concepts) == 10
    for c in concepts:
        assert isinstance(c, ConceptEntity)
        assert c.importance > 0.0
        assert c.confidence > 0.0
        assert len(c.exemplar_ids) > 0


def test_distillation_10000_experiences_to_50_rules():
    """Verify transforming 10,000 experiences into 50 operational rules."""
    engine = DistillationEngine()

    actions = ["retry_with_backoff", "route_to_fallback", "increase_pool", "flush_buffer", "throttle_requests"]
    outcomes = ["latency_normal", "error_recovered", "memory_cleared", "throughput_max"]

    experiences = [
        {
            "id": f"exp_{i}",
            "action": actions[i % len(actions)],
            "outcome": outcomes[i % len(outcomes)],
            "reward": 0.8 if i % 3 != 0 else -0.2
        }
        for i in range(10000)
    ]
    assert len(experiences) == 10000

    rules = engine.distill_experiences_to_rules(experiences, target_rule_count=50)
    assert len(rules) == 50
    for r in rules:
        assert r.condition is not None
        assert r.action is not None
        assert r.success_rate >= 0.5


def test_distillation_100000_observations_to_500_principles():
    """Verify transforming 100,000 observations into 500 foundational principles."""
    engine = DistillationEngine()

    sources = ["cpu_sensor", "network_tap", "disk_io", "db_pool"]
    types = ["throughput", "temperature", "queue_depth", "latency"]

    # Generate observations swiftly
    observations = [
        {"id": f"obs_{i}", "source": sources[i % 4], "type": types[i % 4], "value": i % 100}
        for i in range(100000)
    ]
    assert len(observations) == 100000

    t0 = time.perf_counter()
    principles = engine.distill_observations_to_principles(observations, target_principle_count=500)
    dur = time.perf_counter() - t0

    assert len(principles) == 500
    assert dur < 5.0  # Must execute within 5 seconds
    for p in principles:
        assert "principle_id" in p
        assert p["confidence"] >= 0.9
        assert p["empirical_support_count"] > 0


def test_concept_formation_exemplars_and_taxonomy():
    """Verify Dog, Wolf, Fox -> Canine and Redis, Postgres, Qdrant -> Data Storage Systems."""
    c_engine = ConceptDiscoveryEngine()
    tax_builder = TaxonomyBuilder(root_name="Universal Entity")

    # Example 1: Storage Systems
    t1 = ToolEntity(name="Redis", tool_name="redis", attributes={"category": "storage", "type": "in_memory"})
    t2 = ToolEntity(name="Postgres", tool_name="postgres", attributes={"category": "storage", "type": "relational"})
    t3 = ToolEntity(name="Qdrant", tool_name="qdrant", attributes={"category": "storage", "type": "vector"})

    storage_concept = c_engine.form_concept_from_exemplars(
        concept_name="Data Storage Systems",
        definition="Persistent and in-memory state repositories for data retrieval and indexing.",
        exemplar_entities=[t1, t2, t3],
        abstraction_depth=2
    )
    assert storage_concept.name == "Data Storage Systems"
    assert len(storage_concept.exemplar_ids) == 3

    # Taxonomy construction
    cat = tax_builder.add_category("Data Storage Systems", parent_name="Universal Entity")
    tax_builder.add_exemplar("Data Storage Systems", "Redis")
    tax_builder.add_exemplar("Data Storage Systems", "Postgres")
    tax_builder.add_exemplar("Data Storage Systems", "Qdrant")

    lineage = tax_builder.get_lineage("Data Storage Systems")
    assert lineage == ["Universal Entity", "Data Storage Systems"]
    node = tax_builder.get_node("Data Storage Systems")
    assert "Redis" in node.exemplar_names
    assert "Postgres" in node.exemplar_names
    assert "Qdrant" in node.exemplar_names


def test_knowledge_synthesis_cross_domain_insight():
    """Verify input Fact A, Fact B, Fact C -> Output New Insight D."""
    synthesis = KnowledgeSynthesisEngine()

    facts = [
        {"statement": "Subprocess timeouts prevent runaway compute loops in Python.", "domain": "execution"},
        {"statement": "LRU eviction prevents unbounded cache growth in memory layers.", "domain": "memory"},
        {"statement": "Circuit breaker trips isolate failing external REST APIs.", "domain": "networking"}
    ]

    insight = synthesis.synthesize(facts)
    assert isinstance(insight, SynthesizedInsight)
    assert "Unifying 3 independent facts" in insight.statement
    assert insight.analogy is not None
    assert insight.extracted_principle is not None
    assert insight.derived_hypothesis is not None
    assert insight.confidence >= 0.8
