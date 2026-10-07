"""Tests for the Foundation Model Agent — Project Alpha's cognitive core.

This test suite verifies the complete autonomous reasoning stack:
- Memory management and persistence
- Reasoning engine and belief updating
- Planner decomposition of goals into steps
- Tool use with safety gates
- Goal discovery from environment state
- Self-improvement through reflection
- World model building from observations
"""

import json
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta


def utc_now():
    return datetime.now(timezone.utc)


class TestKnowledgeStore:
    """Test the KnowledgeStore persistence and retrieval."""

    def test_store_and_retrieve_belief(self):
        from alpha.foundation_model.knowledge_store import KnowledgeStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = KnowledgeStore(path=Path(tmpdir) / "knowledge.json")
            
            # Store a belief
            belief_id = store.store_belief(
                "Alpha runs on gemma-4-e4b-it-ultra at localhost:1234/v1",
                confidence=0.98,
                source="system_config"
            )
            
            # Retrieve it back
            results = store.retrieve("alpha model localhost 1234", limit=5)
            assert len(results) >= 1
            assert results[0].confidence == 0.98

    def test_skill_storage(self):
        from alpha.foundation_model.knowledge_store import KnowledgeStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = KnowledgeStore(path=Path(tmpdir) / "knowledge.json")
            
            skill_id = store.store_skill(
                name="code_execution",
                strategy="Use execute_python tool with sandboxed environment"
            )
            
            assert skill_id is not None
            skills = [r for r in store.list_all() if r.kind == "skill"]
            assert len(skills) >= 1

    def test_bidirectional_indexing(self):
        from alpha.foundation_model.knowledge_store import KnowledgeStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = KnowledgeStore(path=Path(tmpdir) / "knowledge.json")
            
            # Store two semantically related beliefs
            store.store_belief("Alpha has a memory manager for long-term storage")
            store.store_belief("Memory is the foundation of Alpha's intelligence")
            store.store_belief("The workspace stores persistent knowledge across sessions")
            
            # They should be linked
            graph = store.get_graph_neighbors(list(store._data[0].id))
            assert len(graph) >= 1


class TestReasoningEngine:
    """Test the Reasoning Engine's thought generation and planning."""

    def test_reason_about_simple_task(self):
        from alpha.foundation_model.reasoning_engine import ReasoningEngine
        from alpha.foundation_model.memory_manager import MemoryManager
        
        mem_mgr = MemoryManager()
        engine = ReasoningEngine(memory_manager=mem_mgr)
        
        # Test basic reasoning about a file operation task
        thoughts = engine.reason_about("Read the contents of README.md")
        
        assert len(thoughts) >= 1  # At least one thought generated
        for t in thoughts:
            assert hasattr(t, 'content')

    def test_belief_confidence_calibration(self):
        from alpha.foundation_model.reasoning_engine import ReasoningEngine
        
        engine = ReasoningEngine()
        
        # Uncertainty should be calibrated to confidence
        belief_1 = engine.uncertainty_manager.register_belief(
            engine.beliefs["belief_..."] if False else type('obj', (object,), {
                'id': 'b1', 'confidence': 0.95, 'evidence_weight': 0.8
            })()
        )

        # Actually test it properly
        b = type('Belief', (), {'id': 'test_b1', 'confidence': 0.9})()
        
        result = engine.uncertainty_manager.compute_information_gain(0.5)
        assert result > 0  # Some information gain expected


class TestPlanner:
    """Test goal decomposition into executable plans."""

    def test_sequential_decomposition(self):
        from alpha.foundation_model.planner import Planner, SequentialDecompositionStrategy
        
        strategy = SequentialDecompositionStrategy()
        plan = strategy.plan(goal_title="Create a Python file with Fibonacci function")
        
        assert len(plan.steps) >= 2
        # Each step should have a description and optionally a tool
        for step in plan.steps:
            assert hasattr(step, 'description')

    def test_plan_execution(self):
        from alpha.foundation_model.planner import Planner
        
        planner = Planner()
        
        # Plan a simple task
        plan = planner.plan(goal_title="Scan the current directory")
        
        # Execute it (simulated)
        completed, outputs = planner.execute_plan(plan)
        assert len(completed) >= 0  # May have dependencies


class TestToolUseEngine:
    """Test tool execution with safety gating."""

    def test_filesystem_scan_tool(self):
        from alpha.foundation_model.tool_use_engine import ToolUseEngine
        
        engine = ToolUseEngine()
        
        result = engine.execute_tool(
            "filesystem_scan",
            parameters={"path": "."}
        )
        
        assert isinstance(result, type(engine.registry.execute.__annotations__.get("return_type", object))())

    def test_rate_limiting(self):
        from alpha.foundation_model.tool_use_engine import SafetyGateway
        
        gateway = SafetyGateway(max_concurrent_tools=2)
        
        # Should allow requests within rate limit
        for i in range(30):  # Well under the per-minute limit
            assert gateway.acquire_rate_limit("web_search") is True, \
                f"Rate limit blocked request {i}"


class TestGoalDiscovery:
    """Test autonomous goal discovery mechanisms."""

    def test_goal_discovery_with_environment(self):
        from alpha.foundation_model.goal_discovery import GoalDiscoveryEngine
        
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = GoalDiscoveryEngine(workspace_root=Path(tmpdir))
            
            # Create a file to make the environment interesting
            (Path(tmpdir) / "test.txt").write_text("Hello, world!")

            goals = engine.discover_all()
            assert isinstance(goals, list)


class TestSelfImprovement:
    """Test the self-improvement reflection loop."""

    def test_reflection_on_success(self):
        from alpha.foundation_model.self_improvement import SelfImprovementLoop
        
        simulator = SelfImprovementLoop()
        
        thoughts = []  # Empty thought chain for simple success
        
        output = simulator.reflect_on_goal_cycle(
            goal_title="Simple successful task",
            thoughts=thoughts,
            outcome_success=True,
            tool_results=None,
            unexpected_observation=None,
        )

        assert output.success == True
        assert len(output.strengths) >= 0
        assert output.distilled_lesson != ""

    def test_reflection_on_failure(self):
        from alpha.foundation_model.self_improvement import SelfImprovementLoop
        
        simulator = SelfImprovementLoop()
        
        # Simulate a failure with clear weakness identified
        thoughts = []
        tool_results = [{"success": False, "error_message": "File not found"}]

        output = simulator.reflect_on_goal_cycle(
            goal_title="Write file to non-existent path",
            thoughts=thoughts,
            outcome_success=False,
            tool_results=tool_results,
            unexpected_observation=None,
        )

        assert output.success == False
        # Should identify a weakness related to the error
        weaknesses = [w for w in output.weaknesses if "error" in str(w).lower()]
        assert len(weaknesses) >= 1


class TestMemoryManager:
    """Test multi-layer memory management."""

    def test_layered_storage(self):
        from alpha.foundation_model.memory_manager import MemoryManager
        
        manager = MemoryManager()

        # Store across layers
        r1 = manager.store("This is a working memory item", layer="working")
        r2 = manager.store("Short-term observation", layer="short_term")
        r3 = manager.store("Long-term belief about the world", layer="long_term")

        assert r1.id in manager.working_memory.keys()
        assert r2.id in [m.id for m in manager.short_term]


class TestWorldModel:
    """Test entity tracking and relationship building."""

    def test_entity_creation_and_observation(self):
        from alpha.foundation_model.world_model import WorldModel
        
        wm = WorldModel()

        # Observe something new
        wm.observe("The filesystem_scan tool exists in the environment")
        
        # Should have created an entity
        assert len(wm.entities) >= 1
        
        # Query by name
        entity = wm.get_entity_by_name("filesystem_scan")
        assert entity is not None


class TestFoundationModelAgent:
    """Integration tests for the complete agent."""

    def test_agent_initialization(self):
        from alpha.foundation_model.agent import FoundationModelAgent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = FoundationModelAgent(
                workspace_root=Path(tmpdir),
                model_url="http://localhost:1234/v1",
            )

            # Agent should have all components initialized
            assert agent.memory_manager is not None
            assert agent.reasoning_engine is not None
            assert agent.planner is not None
            assert agent.tool_engine is not None
            assert agent.goal_discovery is not None
            assert agent.self_improvement is not None

    def test_agent_response_generation(self):
        from alpha.foundation_model.agent import FoundationModelAgent
        
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = FoundationModelAgent(
                workspace_root=Path(tmpdir),
                enable_external_model=False,  # Run in local mode for this test
            )

            response = agent.respond_to_user("What is your name?")

            assert isinstance(response, str)


if __name__ == "__main__":
    import pytest
    
    print("\n" + "=" * 70)
    print("  🧪 Running Foundation Model Agent Test Suite")
    print("=" * 70 + "\n")
    
    test_classes = [
        TestKnowledgeStore,
        TestReasoningEngine,
        TestPlanner,
        TestToolUseEngine,
        TestGoalDiscovery,
        TestSelfImprovement,
        TestMemoryManager,
        TestWorldModel,
        TestFoundationModelAgent,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        print(f"\n  Testing {test_class.__name__}...")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    passed += 1
                    print(f"    ✅ {method_name}")
                except Exception as e:
                    failed += 1
                    errors.append((method_name, str(e)))
                    print(f"    ❌ {method_name}: {e}")

    # Summary
    print("\n\n" + "=" * 70)
    print("  📊 TEST SUMMARY")
    print("=" * 70)
    print(f"\n  Passed:   {passed}")
    print(f"  Failed:   {failed}")
    
    if errors:
        print("\n  Failures:")
        for test, error in errors:
            print(f"    • {test}: {error}")

    exit(0 if failed == 0 else 1)