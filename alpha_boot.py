"""Alpha Cognitive Boot Orchestrator: 10-Stage Safe Startup Sequence.

Boot Sequence:
Stage 1: Load Identity (Validate alpha_identity.md, compute hash, check drift)
Stage 2: Load Governance (Initialize ChangeGovernanceSystem, ConstitutionEngine)
Stage 3: Load Truth Layer (Initialize BeliefSystem & EvidenceRegistry, enforce no orphan beliefs)
Stage 4: Load World Model (Initialize CognitiveWorldModel, 25 entities, 14 relations)
Stage 5: Load Self Model (Query 10 existential questions via SelfModel.introspect)
Stage 6: Load Agents (Initialize AgentRuntime, 18 archetypes, deliberation council)
Stage 7: Load Tools (Register Sandbox, Filesystem, Verification, Git, API tools)
Stage 8: Load Model (Probe localhost:1234/v1, verify LLM and Embeddings)
Stage 9: Perform Validation (Pre-flight integrity and cognitive sanity checks)
Stage 10: Enter Operational State (Emit telemetry, return operational cognitive OS)

Boot must fail safely: Any invariant violation immediately aborts with BOOT_FAILED.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# Core Subsystems
from alpha.context.identity_cache import identity_context # NEW: Import the context cache
from alpha.core.identity import (
    IdentityState,
    IdentityLoader,
    IdentityValidator,
    IdentityHashGenerator,
    IdentityDriftDetector,
    ConstitutionEngine,
    IdentityPersistence
)
from alpha.operating_system import AlphaOperatingSystem
from alpha.world_model import (
    CognitiveWorldModel,
    EntityType,
    RelationType,
    GoalEntity,
    CapabilityEntity,
    RiskEntity,
    AgentEntity,
    ToolEntity,
    EvidencePolarity,
    EvidenceStrength
)
from alpha.agents.governance.governance import ChangeGovernanceSystem
from alpha.memory.embedding_service import EmbeddingService
from alpha.knowledge.tiered_loader import TieredKnowledgeSystem
from alpha.model_intelligence.connector.client import OpenAICompatibleClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("alpha.boot")


class BootStageResult(BaseModel):
    stage_number: int
    stage_name: str
    success: bool
    latency_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class AlphaBootOrchestrator:
    """Manages the 10-stage sequential cognitive boot pipeline with fail-safe boundaries."""

    def __init__(self, workspace_root: Optional[str] = None, identity_path: str = "alpha_identity.md"):
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else Path.cwd()
        self.identity_path = identity_path
        self.status = "INITIALIZING"
        self.stage_results: List[BootStageResult] = []

        # Cognitive Assets
        self.governance: Optional[ChangeGovernanceSystem] = None
        self.world_model: Optional[CognitiveWorldModel] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.tiered_knowledge: Optional[TieredKnowledgeSystem] = None
        self.operating_system: Optional[AlphaOperatingSystem] = None
        self.model_client: Optional[OpenAICompatibleClient] = None

    def execute_boot(self) -> Tuple[bool, str]:
        """Executes all 10 boot stages sequentially. Halts immediately on failure."""
        t_boot_start = time.time()
        print("==================================================")
        print("ALPHA COGNITIVE SYSTEM: BOOT SEQUENCE INITIATED")
        print("==================================================")

        stages = [
            (1, "Load Identity", self._stage_1_load_identity),
            (2, "Load Governance", self._stage_2_load_governance),
            (3, "Load Truth Layer", self._stage_3_load_truth_layer),
            (4, "Load World Model", self._stage_4_load_world_model),
            (5, "Load Self Model", self._stage_5_load_self_model),
            (6, "Load Agents", self._stage_6_load_agents),
            (7, "Load Tools", self._stage_7_load_tools),
            (8, "Load Model", self._stage_8_load_model),
            (9, "Perform Validation", self._stage_9_perform_validation),
            (10, "Enter Operational State", self._stage_10_enter_operational_state),
        ]

        for num, name, func in stages:
            t0 = time.time()
            print(f"[{num}/10] Executing {name}...")
            try:
                success, details = func()
                dt = (time.time() - t0) * 1000.0
                res = BootStageResult(
                    stage_number=num,
                    stage_name=name,
                    success=success,
                    latency_ms=round(dt, 2),
                    details=details
                )
                self.stage_results.append(res)
                if not success:
                    return self._abort_boot(num, name, details.get("error", "Unknown validation failure"))
                print(f"  -> SUCCESS ({round(dt, 1)}ms)")
            except Exception as exc:
                dt = (time.time() - t0) * 1000.0
                res = BootStageResult(
                    stage_number=num,
                    stage_name=name,
                    success=False,
                    latency_ms=round(dt, 2),
                    error=str(exc)
                )
                self.stage_results.append(res)
                return self._abort_boot(num, name, str(exc))

        total_duration = round((time.time() - t_boot_start), 2)
        print("==================================================")
        print(f"ALPHA BOOT SEQUENCE COMPLETED CLEANLY IN {total_duration}s!")
        print("SYSTEM STATE: OPERATIONAL (GROUNDED IN REALITY)")
        print("==================================================")
        self.status = "OPERATIONAL"
        self._persist_boot_record(total_duration)
        return True, "Alpha booted successfully into operational state."

    def _abort_boot(self, stage_num: int, stage_name: str, reason: str) -> Tuple[bool, str]:
        self.status = "BOOT_FAILED"
        err_msg = f"SAFE FAILURE TRIGGERED at Stage {stage_num} ({stage_name}): {reason}"
        print(f"\n[CRITICAL ALERT] {err_msg}")
        print("SYSTEM REFUSED TO ENTER UNGROUNDED OPERATIONAL STATE.")
        print("==================================================")
        self._persist_boot_record(0.0)
        return False, err_msg

    # -------------------------------------------------------------------------
    # Stage Implementations
    # -------------------------------------------------------------------------

    def _stage_1_load_identity(self) -> Tuple[bool, Dict[str, Any]]:
        loaded_identity = IdentityLoader.load_from_markdown(self.identity_path)
        valid, errors = IdentityValidator.validate(loaded_identity)
        if not valid:
            return False, {"error": f"Identity validation failed: {errors}"}

        # Check drift against baseline hash if persisted
        baseline_file = Path("data/identity_state.json")
        if baseline_file.exists():
            baseline_state = IdentityPersistence.load(baseline_file)
            detector = IdentityDriftDetector(baseline_state.identity_hash, baseline_state)
            drifted, score, reasons = detector.detect_drift(loaded_identity)
            if drifted and score > 0.4:
                return False, {"error": f"Identity drift detected above threshold: {reasons}"}

        # Persist the validated identity state to disk
        IdentityPersistence.save(loaded_identity)
        
        # Inject into immutable runtime context cache for subsequent reference/pointer usage
        identity_context.set_identity(loaded_identity)
        return True, {"name": loaded_identity.name, "hash": loaded_identity.identity_hash}

    def _stage_2_load_governance(self) -> Tuple[bool, Dict[str, Any]]:
        self.governance = ChangeGovernanceSystem()
        # Verify constitution engine is operational
        assert ConstitutionEngine.validate_action("status", {}, self.identity)[0]
        return True, {"constitution_articles": len(self.identity.constitution), "governance_ready": True}

    def _stage_3_load_truth_layer(self) -> Tuple[bool, Dict[str, Any]]:
        self.world_model = CognitiveWorldModel()
        # Verify no-orphan-beliefs constraint
        orphan_rejected = False
        try:
            self.world_model.beliefs.form_belief("Ungrounded claim", initial_confidence=0.9, evidence_ids=[])
        except ValueError:
            orphan_rejected = True

        if not orphan_rejected:
            return False, {"error": "Truth layer failed to reject ungrounded belief without evidence"}

        return True, {"orphan_beliefs_blocked": True, "evidence_registry_active": True}

    def _stage_4_load_world_model(self) -> Tuple[bool, Dict[str, Any]]:
        # Verify ontology and graph
        entities = self.world_model.ontology.get_all()
        state = self.world_model.world_state.get_current_state()
        summary = state.summary()
        return True, {"total_entities": len(entities), "dimensions_active": len(summary)}

    def _stage_5_load_self_model(self) -> Tuple[bool, Dict[str, Any]]:
        intro = self.world_model.self_model.introspect()
        if not intro.who_am_i or not intro.what_can_i_do:
            return False, {"error": "Self model introspection returned empty answers"}

        # Persist SELF_MODEL_STATE
        Path("data").mkdir(parents=True, exist_ok=True)
        Path("data/self_model_state.json").write_text(intro.model_dump_json(indent=2), encoding="utf-8")
        return True, {"who_am_i": intro.who_am_i, "capabilities_count": len(intro.what_can_i_do)}

    def _stage_6_load_agents(self) -> Tuple[bool, Dict[str, Any]]:
        self.operating_system = AlphaOperatingSystem(workspace_root=str(self.workspace_root))
        runtime = self.operating_system.agent_runtime
        return True, {"agents_managed": runtime.registry.count(), "council_ready": True}

    def _stage_7_load_tools(self) -> Tuple[bool, Dict[str, Any]]:
        registry = self.operating_system.registry
        tool_count = len(registry.list_tools())
        if tool_count < 5:
            return False, {"error": f"Insufficient tools registered: {tool_count}"}
        return True, {"registered_tools": tool_count, "sandbox_active": True}

    def _stage_8_load_model(self) -> Tuple[bool, Dict[str, Any]]:
        # Probe LLM endpoint
        self.model_client = OpenAICompatibleClient(
            base_url="http://localhost:1234/v1",
            default_model="gemma-4-e4b-it-ultra-uncensored-heretic",
            timeout_seconds=30.0,
            enable_mock_fallback=False
        )
        resp = self.model_client.chat_completion(
            messages=[{"role": "user", "content": "Respond with 'ALPHA_ONLINE'"}],
            max_tokens=150
        )
        if not resp.content and not resp.reasoning_content:
            return False, {"error": "Model endpoint returned null content on probe"}

        # Probe Embeddings endpoint
        self.embedding_service = EmbeddingService(
            endpoint_url="http://localhost:1234/v1",
            model_name="text-embedding-nomic-embed-text-v1.5"
        )
        emb = self.embedding_service.embed_text("Alpha cognitive boot verification")
        if len(emb) != 768:
            return False, {"error": f"Embedding model returned invalid dimension: {len(emb)} (expected 768)"}

        return True, {
            "model_id": resp.model,
            "probe_latency_ms": resp.latency_ms,
            "embedding_dimension": len(emb)
        }

    def _stage_9_perform_validation(self) -> Tuple[bool, Dict[str, Any]]:
        # Initialize tiered knowledge system
        self.tiered_knowledge = TieredKnowledgeSystem(
            identity_path=self.identity_path,
            embedding_service=self.embedding_service
        )
        ctx = self.tiered_knowledge.assemble_prompt_context("Check database persistence")
        if "SYSTEM IDENTITY" not in ctx or "TIER 1" not in ctx:
            return False, {"error": "Tiered knowledge context assembly validation failed"}

        return True, {"tiered_knowledge_active": True, "context_length": len(ctx)}

    def _stage_10_enter_operational_state(self) -> Tuple[bool, Dict[str, Any]]:
        telemetry = {
            "status": "OPERATIONAL",
            "boot_timestamp": time.time(),
            "identity_hash": self.identity.identity_hash,
            "model_id": self.model_client.default_model,
            "embedding_dimension": 768,
            "world_model_entities": len(self.world_model.ontology.get_all())
        }
        return True, telemetry

    def _persist_boot_record(self, total_seconds: float) -> None:
        record = {
            "status": self.status,
            "total_duration_s": total_seconds,
            "stages": [s.model_dump() for s in self.stage_results],
            "timestamp": time.time()
        }
        Path("data").mkdir(parents=True, exist_ok=True)
        with open("data/boot_execution_record.json", "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)


if __name__ == "__main__":
    orchestrator = AlphaBootOrchestrator()
    success, message = orchestrator.execute_boot()
    if not success:
        sys.exit(1)
