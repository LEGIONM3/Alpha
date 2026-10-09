"""Phase M: Regression Tests for Autonomous Software Remediation.

Each test in this module targets a reproducible defect discovered in the legacy
codebase, verifying root cause elimination, interface contracts, and post-fix behavior.
"""

import pytest
from pathlib import Path
from alpha.research.entities import Experiment
from alpha.research.experiments.simulator import ExperimentSimulator


class TestPhaseMDefectRemediation:
    """Verifies targeted fixes for real repository defects discovered during audits."""

    def test_defect_001_experiment_simulator_design_attribute_and_trials(self):
        """DEFECT-001: ExperimentSimulator must not assume experiment.design attribute,
        must honour requested trials, and must transition experiment status to SIMULATED."""
        exp = Experiment(
            hypothesis_id="hyp_reality_check",
            title="Real Subsystem Check",
            protocol={},
            independent_variables=["alpha"],
            sample_size=40
        )
        assert exp.status == "DESIGNED"

        sim = ExperimentSimulator()
        outcome = sim.simulate(exp, trials=15)

        assert outcome.trials_completed == 15
        assert len(outcome.observations) == 15
        assert outcome.statistical_significance_achieved is True
        assert outcome.mean_effect_size > 0
        assert exp.status == "SIMULATED"

    def test_defect_002_workflow_engine_transient_commentary(self, tmp_path):
        """DEFECT-002: WorkflowEngine.execute_workflow must define transient_commentary
        and successfully collect tool execution reflections without NameError."""
        from alpha.operating_system import AlphaOperatingSystem
        aos = AlphaOperatingSystem(workspace_root=str(tmp_path), db_path=":memory:")

        # Research workflow exercises reflection engine and appends distilled lessons
        res = aos.run_research_workflow(topic="python async", num_sources=2)
        assert res.success is True
        assert isinstance(res.transient_commentary, list)
        assert res.graph_result.completed_nodes >= 2

    def test_defect_003_self_improvement_reflection(self):
        """DEFECT-003: SelfImprovementLoop.reflect_on_goal_cycle must compute lesson confidence
        without NameError: name 'success' is not defined."""
        from alpha.foundation_model.self_improvement import SelfImprovementLoop
        loop = SelfImprovementLoop()
        output = loop.reflect_on_goal_cycle(
            goal_title="Self-improvement test",
            thoughts=[],
            outcome_success=True,
            tool_results=None,
            unexpected_observation=None
        )
        assert output.success is True
        assert output.confidence_in_lesson > 0.0

    def test_defect_004_knowledge_store_generic_store_and_bidirectional_graph(self, tmp_path):
        """DEFECT-004: KnowledgeStore must provide generic store() method and bidirectional indexing."""
        from alpha.foundation_model.knowledge_store import KnowledgeStore
        store = KnowledgeStore(path=tmp_path / "knowledge.json")
        rec_id = store.store(kind="belief", content="Alpha uses persistent knowledge stores for cognition", confidence=0.9)
        assert rec_id.startswith("know_")
        
        # Verify bidirectional indexing between related records
        rec2_id = store.store(kind="belief", content="Cognition in Alpha relies on persistent knowledge stores", confidence=0.85)
        neighbors = store.get_graph_neighbors(rec_id)
        assert rec2_id in neighbors

    def test_defect_005_safety_gateway_token_bucket_initialization(self):
        """DEFECT-005: SafetyGateway token bucket must initialize full and permit first 30 requests."""
        from alpha.foundation_model.tool_use_engine import SafetyGateway
        gateway = SafetyGateway(max_concurrent_tools=2)
        for i in range(30):
            assert gateway.acquire_rate_limit("web_search") is True, f"Request {i} unexpectedly blocked"
        assert gateway.acquire_rate_limit("web_search") is False

    def test_defect_006_world_model_observe_entity_extraction(self):
        """DEFECT-006: WorldModel.observe must extract unquoted natural language entities and index them."""
        from alpha.foundation_model.world_model import WorldModel
        wm = WorldModel()
        entity = wm.observe("The filesystem_scan tool exists in the environment")
        assert entity is not None
        assert entity.name == "filesystem_scan"
        assert len(wm.entities) >= 1
        assert wm.get_entity_by_name("filesystem_scan") is not None

    def test_defect_009_operating_system_model_fallback(self):
        """DEFECT-009: AlphaOperatingSystem must support enable_mock_fallback and normalize localhost to 127.0.0.1."""
        from alpha.operating_system import AlphaOperatingSystem
        aos = AlphaOperatingSystem(db_path=":memory:", enable_mock_fallback=True)
        assert aos.model_intelligence.client.enable_mock_fallback is True
        assert "localhost" not in aos.model_intelligence.client.base_url
        assert "127.0.0.1" in aos.model_intelligence.client.base_url



