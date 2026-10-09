"""Test Suite for Phase M.1 Model Inference and Fallback Integrity.

Audits and verifies:
1. Valid live Qwen inference against local LM Studio endpoint.
2. Connection refusal handling when endpoint is down.
3. Socket timeout handling during delayed inference.
4. Malformed model output handling and JSON recovery.
5. Recovery after an inference failure.
6. Explicit mock labelling (is_mock=True, telemetry.mock_calls incremented) when opt-in enabled.
7. Explicit failure (RuntimeError / ModelInferenceError) when mocks disabled for live operation.
8. EvidenceGraph strictly rejects orphan beliefs and synthetic claims.
"""

import json
import pytest
import time
from pathlib import Path

from alpha.model_intelligence.connector.client import OpenAICompatibleClient, ChatCompletionResponse
from alpha.model_intelligence.connector.gateway import ModelGateway
from alpha.operating_system import AlphaOperatingSystem
from alpha.reasoning.qwen_reasoner import (
    QwenStrategicReasoner,
    ModelInferenceError,
    EvidenceBundle
)
from alpha.evidence_graph.models import Belief, OrphanBeliefError
from alpha.evidence_graph.graph import EvidenceGraph


class TestModelInferenceAndFallbackIntegrity:

    def test_01_valid_live_qwen_inference(self):
        """Case 1: Authentic inference succeeds against local Qwen endpoint and logs audit record."""
        reasoner = QwenStrategicReasoner(
            endpoint_url="http://127.0.0.1:1234/v1",
            timeout=30.0
        )
        # Verify model is discovered
        active_model = reasoner._ensure_model_discovered()
        assert active_model != ""

        # Test reasoning call
        res = reasoner.generate_reasoning("Echo test: return the exact word 'ALPHA_VERIFIED'.")
        assert isinstance(res, str)
        assert len(res) > 0

        # Verify audit log recorded SUCCESS
        assert len(reasoner.audit_log) >= 1
        last_audit = reasoner.audit_log[-1]
        assert last_audit.status == "SUCCESS"
        assert last_audit.endpoint == "http://127.0.0.1:1234/v1"
        assert last_audit.latency_ms > 0

    def test_02_connection_refusal_when_endpoint_down(self):
        """Case 2: When endpoint is down, live operation fails explicitly without synthetic fallback."""
        # Port 59999 has no server running
        dead_client = OpenAICompatibleClient(
            base_url="http://127.0.0.1:59999/v1",
            enable_mock_fallback=False,
            timeout_seconds=1.0
        )
        with pytest.raises(RuntimeError) as exc_info:
            dead_client.chat_completion(messages=[{"role": "user", "content": "hello"}])
        assert "OpenAICompatibleClient connection failed" in str(exc_info.value)

    def test_03_inference_timeout_handling(self):
        """Case 3: Socket timeout triggers explicit error when mock fallback is disabled."""
        timeout_client = OpenAICompatibleClient(
            base_url="http://127.0.0.1:1234/v1",
            enable_mock_fallback=False,
            timeout_seconds=0.0001  # Instant timeout
        )
        with pytest.raises(RuntimeError) as exc_info:
            timeout_client.chat_completion(messages=[{"role": "user", "content": "Long task"}])
        assert "timed out" in str(exc_info.value).lower() or "connection failed" in str(exc_info.value).lower()

    def test_04_malformed_model_output_json_repair(self):
        """Case 4: Malformed output with thinking tags and broken markdown is cleaned or flagged."""
        reasoner = QwenStrategicReasoner()
        
        # Test 4a: Content wrapped in thinking tags
        raw_think = "<think>Let me analyze the problem</think>{\"salient_observations\": [\"obs1\"], \"candidate_goals\": []}"
        parsed = reasoner._extract_json(raw_think)
        assert isinstance(parsed, dict)
        assert "salient_observations" in parsed
        assert parsed["salient_observations"] == ["obs1"]

        # Test 4b: Markdown code fences
        raw_fence = "```json\n{\"salient_observations\": [\"test_fence\"], \"candidate_goals\": []}\n```"
        parsed_fence = reasoner._extract_json(raw_fence)
        assert isinstance(parsed_fence, dict)
        assert parsed_fence["salient_observations"] == ["test_fence"]

        # Test 4c: Unrecoverable garbage raises ValueError cleanly
        raw_garbage = "Not JSON at all"
        with pytest.raises((ValueError, json.JSONDecodeError)):
            reasoner._extract_json(raw_garbage)

    def test_05_recovery_after_inference_failure(self):
        """Case 5: Reasoner resets active model state and recovers cleanly on subsequent valid calls."""
        reasoner = QwenStrategicReasoner(endpoint_url="http://127.0.0.1:1234/v1", timeout=30.0)
        
        # Simulate transient error by pointing to invalid port temporarily
        reasoner.endpoint_url = "http://127.0.0.1:59999/v1"
        reasoner.active_model = None
        with pytest.raises(ModelInferenceError):
            reasoner.generate_reasoning("test query")

        # Now point back to live endpoint and verify recovery
        reasoner.endpoint_url = "http://127.0.0.1:1234/v1"
        res = reasoner.generate_reasoning("Echo recovery test: return 'RECOVERED'")
        assert isinstance(res, str)
        assert len(res) > 0

    def test_06_mocks_explicitly_labelled_when_opt_in(self):
        """Case 6: Mocks are explicitly opt-in and clearly labelled with is_mock=True."""
        mock_client = OpenAICompatibleClient(
            base_url="http://127.0.0.1:59999/v1",
            enable_mock_fallback=True,
            timeout_seconds=0.5
        )
        resp = mock_client.chat_completion(messages=[{"role": "user", "content": "Explain Turing completeness."}])
        assert resp.is_mock is True
        assert resp.id.startswith("chatcmpl-mock")

        # Gateway telemetry records mock call
        gateway = ModelGateway(client=mock_client, enable_mock_fallback=True)
        res_dict = gateway.chat_completion(messages=[{"role": "user", "content": "Test mock telemetry"}])
        assert res_dict["is_mock"] is True
        assert gateway.telemetry.mock_calls >= 1

    def test_07_live_operation_disables_mocks_by_default(self):
        """Case 7: AlphaOperatingSystem defaults enable_mock_fallback=False for live operation."""
        aos = AlphaOperatingSystem(db_path=":memory:")
        assert aos.enable_mock_fallback is False
        assert aos.model_intelligence.client.enable_mock_fallback is False

    def test_08_evidence_graph_rejects_orphan_beliefs_and_fakes(self, tmp_path):
        """Case 8: Belief without supporting evidence must raise OrphanBeliefError."""
        graph = EvidenceGraph(storage_path=tmp_path / "test_graph.json")

        # Direct graph rejection raises OrphanBeliefError
        with pytest.raises(OrphanBeliefError) as exc_info:
            graph.create_belief(
                statement="Arbitrary claim without supporting evidence",
                supporting_evidence_ids=[]
            )
        assert "A belief without evidence must never exist" in str(exc_info.value)

        # Model instantiation rejection also enforced
        with pytest.raises(Exception) as exc_info2:
            Belief(
                statement="Direct model instantiation without evidence",
                confidence=0.9,
                supporting_evidence=[]
            )
        assert "A belief without evidence must never exist" in str(exc_info2.value)
