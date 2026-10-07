"""World Model Bridge: Bidirectional synchronization between Model Intelligence and Cognitive World Model."""

from typing import List, Dict, Any, Optional
from alpha.model_intelligence.capability_graph.graph import ModelCapabilityGraph
from alpha.model_intelligence.failure_analysis.models import FailureReport
from alpha.model_intelligence.amplification.models import AmplificationResult


class WorldModelBridge:
    """Synchronizes model performance, failures, beliefs, and topology into Alpha's Cognitive World Model."""

    def __init__(self, world_model: Optional[Any] = None):
        self.world_model = world_model
        self._sync_log: List[Dict[str, Any]] = []

    def sync_model_topology(self, model_name: str, family: str, context_window: int):
        """Registers the foundation model into the World Model Universal Knowledge Graph."""
        if not self.world_model:
            return

        entity_id = f"model_{model_name.replace('-', '_').replace('.', '_')}"

        if hasattr(self.world_model, "register_entity"):
            from alpha.world_model.ontology import Entity, EntityType
            self.world_model.register_entity(Entity(
                id=entity_id,
                entity_type=EntityType.RESOURCE,
                name=f"Foundation Model: {model_name}",
                description=f"Managed {family} architecture model with {context_window} context limit.",
                attributes={"family": family, "context_window": context_window},
                confidence=1.0,
                importance=0.9
            ))
        elif hasattr(self.world_model, "graph"):
            self.world_model.graph.add_node(
                node_id=entity_id,
                node_type="resource",
                name=model_name,
                attributes={"family": family, "context_window": context_window}
            )

        self._sync_log.append({"action": "sync_topology", "model_name": model_name})

    def sync_capability_update(self, capability_graph: ModelCapabilityGraph):
        """Synchronizes capability scores and evidence into Epistemic Beliefs and Ontology Capabilities."""
        if not self.world_model:
            return

        for name, node in capability_graph.get_all_capabilities().items():
            statement = f"Model capability '{name}' achieves empirical score {node.score:.2f}."

            if hasattr(self.world_model, "form_belief"):
                self.world_model.form_belief(
                    statement=statement,
                    initial_confidence=node.confidence,
                    sources=[f"capability_profiler_{name}"],
                    domain="model_intelligence"
                )

            self._sync_log.append({"action": "sync_capability", "capability": name, "score": node.score})

    def sync_execution_outcome(self, result: AmplificationResult, model_name: str):
        """Synchronizes execution successes and failures to causal networks and epistemic beliefs."""
        if not self.world_model:
            return

        model_id = f"model_{model_name.replace('-', '_').replace('.', '_')}"
        task_id = result.task_id

        # Record belief regarding amplification efficacy
        if hasattr(self.world_model, "form_belief"):
            self.world_model.form_belief(
                statement=f"Cognitive scaffolding amplified {model_name} execution by {result.amplification_factor}x on task {task_id}.",
                initial_confidence=0.95,
                sources=[f"amplification_engine_task_{task_id}"],
                domain="amplification"
            )

        # Add relationship edge to Knowledge Graph
        if hasattr(self.world_model, "relate") and result.verification_passed:
            from alpha.world_model.graph import RelationType
            try:
                self.world_model.relate(
                    source_id=model_id,
                    target_id="ENT_GOAL_CIV",
                    relation_type=RelationType.IMPROVES,
                    confidence=0.9
                )
            except Exception:
                pass

        self._sync_log.append({
            "action": "sync_execution",
            "task_id": task_id,
            "amplification_factor": result.amplification_factor
        })

    def sync_failure(self, failure: FailureReport, model_name: str):
        """Registers detected failure into World Model Risk registry and causal influence network."""
        if not self.world_model:
            return

        risk_id = f"risk_{failure.failure_id}"
        if hasattr(self.world_model, "register_entity"):
            from alpha.world_model.ontology import Entity, EntityType
            self.world_model.register_entity(Entity(
                id=risk_id,
                entity_type=EntityType.RISK,
                name=f"Model Failure: {failure.failure_type.value}",
                description=failure.description,
                attributes={"remediation": failure.remediation_strategy},
                importance=failure.severity,
                confidence=0.9
            ))

        self._sync_log.append({"action": "sync_failure", "failure_id": failure.failure_id})

    def get_sync_log(self) -> List[Dict[str, Any]]:
        return list(self._sync_log)
