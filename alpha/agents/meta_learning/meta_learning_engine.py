"""Meta Learning Framework: Failure & Success Pattern Mining, Rule Generation, and Lesson Publishing."""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.agents.knowledge_society.knowledge_society import SharedKnowledgeLayer

class OperationalRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: f"RULE_OPS_{uuid.uuid4().hex[:6].upper()}")
    condition: str
    directive: str
    origin_pattern: str
    confidence: float = 0.90
    is_active: bool = True
    created_at: float = Field(default_factory=time.time)

class MetaHeuristic(BaseModel):
    heuristic_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    principle: str
    weight: float = 1.0

class MetaLearningFramework:
    """Extracts systemic intelligence from societal execution traces."""

    def __init__(self, knowledge_layer: Optional[SharedKnowledgeLayer] = None):
        self.knowledge_layer = knowledge_layer
        self.failure_log: List[Dict[str, Any]] = []
        self.success_log: List[Dict[str, Any]] = []
        self.rules: Dict[str, OperationalRule] = {}
        self.heuristics: List[MetaHeuristic] = []
        self._lock = threading.RLock()
        self._seed_core_rules()

    def _seed_core_rules(self) -> None:
        r1 = OperationalRule(
            rule_id="RULE_CORE_001",
            condition="When executing arbitrary generated code",
            directive="Always execute in isolated sandbox subprocess with timeout <= 30s",
            origin_pattern="Subprocess safety standard"
        )
        self.rules[r1.rule_id] = r1

    def record_failure(self, task_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            self.failure_log.append({
                "timestamp": time.time(),
                "task_type": task_type,
                "error": error_message,
                "context": context or {}
            })

    def record_success(self, task_type: str, details: Dict[str, Any], latency_ms: float) -> None:
        with self._lock:
            self.success_log.append({
                "timestamp": time.time(),
                "task_type": task_type,
                "details": details,
                "latency_ms": latency_ms
            })

    def mine_patterns(self) -> Dict[str, Any]:
        """Mine recurring patterns from failure and success telemetry."""
        with self._lock:
            failure_types: Dict[str, int] = {}
            for f in self.failure_log:
                tt = f["task_type"]
                failure_types[tt] = failure_types.get(tt, 0) + 1

            success_types: Dict[str, int] = {}
            for s in self.success_log:
                tt = s["task_type"]
                success_types[tt] = success_types.get(tt, 0) + 1

            return {
                "total_failures": len(self.failure_log),
                "total_successes": len(self.success_log),
                "top_failure_domains": failure_types,
                "top_success_domains": success_types,
                "mined_at": time.time()
            }

    def generate_operational_rules(self) -> List[OperationalRule]:
        """Synthesize operational rules to prevent recurring failures."""
        with self._lock:
            new_rules = []
            patterns = self.mine_patterns()

            if patterns["total_failures"] > 0:
                rule = OperationalRule(
                    condition="When task exhibits failure rate > 10%",
                    directive="Mandate CriticAgent adversarial review prior to execution dispatch",
                    origin_pattern="Automated failure analysis",
                    confidence=0.92
                )
                self.rules[rule.rule_id] = rule
                new_rules.append(rule)

            # High success heuristic rule
            if patterns["total_successes"] > 0:
                rule_s = OperationalRule(
                    condition="When task type matches high-success pattern",
                    directive="Apply fast-path parallel execution without intermediate checkpoints",
                    origin_pattern="High throughput success clustering",
                    confidence=0.95
                )
                self.rules[rule_s.rule_id] = rule_s
                new_rules.append(rule_s)

            return new_rules

    def publish_lessons_to_society(self) -> int:
        """Publish learned rules as verified knowledge into the shared knowledge layer."""
        if not self.knowledge_layer:
            return 0
        with self._lock:
            published_count = 0
            for r in self.rules.values():
                self.knowledge_layer.publish(
                    key=f"rule:{r.rule_id}",
                    title=f"Operational Rule {r.rule_id}",
                    content=f"Condition: {r.condition} -> Directive: {r.directive}",
                    author_id="meta_learning_agent",
                    author_role="meta_learner",
                    tags=["operational_rule", "meta_learning"],
                    auto_verify=True
                )
                published_count += 1
            return published_count

    def get_active_rules(self) -> List[OperationalRule]:
        with self._lock:
            return [r for r in self.rules.values() if r.is_active]
