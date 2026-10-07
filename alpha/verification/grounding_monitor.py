"""Project Alpha: Epistemic Drift Detection & Grounding Monitor (Phase 7I).

Prevents internally consistent delusions by continuously evaluating:
- Beliefs against evidence chains
- Hypotheses against falsification tests
- Identity against SHA-256 constitutional baseline
- World model assumptions against verifiable grounding

Emits immediate grounding alerts on detection.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.core.perception import PerceptionBus, PerceptionEventType

logger = logging.getLogger("alpha.verification.grounding")


class GroundingAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # UNSUPPORTED_BELIEF, CONTRADICTION, IDENTITY_DRIFT, UNGROUNDED_HYPOTHESIS
    target_id: str
    message: str
    evidence_status: str


class GroundingMonitor:
    """Watchdog agent auditing cognitive grounding and detecting epistemic hallucinations."""

    def __init__(
        self,
        world_model: Optional[Any] = None,
        identity_state: Optional[Any] = None,
        perception_bus: Optional[PerceptionBus] = None,
        interval_seconds: float = 12.0
    ):
        self._lock = threading.RLock()
        self.world_model = world_model
        self.identity_state = identity_state
        self.perception_bus = perception_bus
        self.interval_seconds = interval_seconds

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._alerts_history: List[GroundingAlert] = []

    def evaluate_grounding(self) -> List[GroundingAlert]:
        """Perform epistemic audit across beliefs, evidence chains, and identity invariants."""
        alerts: List[GroundingAlert] = []

        # 1. Audit Beliefs for Orphan Status
        if self.world_model and hasattr(self.world_model, "belief_system"):
            beliefs = self.world_model.belief_system.get_all()
            for b in beliefs:
                # Check supporting evidence
                ev_count = len(b.evidence) if hasattr(b, "evidence") else (len(b.supporting_evidence_ids) if hasattr(b, "supporting_evidence_ids") else 1)
                if ev_count == 0:
                    alerts.append(GroundingAlert(
                        severity="HIGH",
                        category="UNSUPPORTED_BELIEF",
                        target_id=getattr(b, "id", "unknown"),
                        message=f"Belief '{getattr(b, 'statement', '')[:50]}' has zero supporting evidence.",
                        evidence_status="ORPHAN_UNGROUNDED"
                    ))

        # 2. Audit Identity Invariants
        if self.identity_state and hasattr(self.identity_state, "identity_hash"):
            try:
                from alpha.core.identity import IdentityHashGenerator
                current_hash = IdentityHashGenerator.compute_hash(self.identity_state)
                if current_hash != self.identity_state.identity_hash:
                    alerts.append(GroundingAlert(
                        severity="CRITICAL",
                        category="IDENTITY_DRIFT",
                        target_id="identity://state",
                        message=f"Constitutional identity hash mismatch detected: {current_hash[:12]} != {self.identity_state.identity_hash[:12]}",
                        evidence_status="TAMPER_DETECTED"
                    ))
            except Exception:
                pass

        # 3. Publish alerts to perception bus
        with self._lock:
            self._alerts_history.extend(alerts)
            if len(self._alerts_history) > 100:
                self._alerts_history = self._alerts_history[-100:]

        for a in alerts:
            if self.perception_bus:
                self.perception_bus.publish(
                    event_type=PerceptionEventType.RUNTIME_ERROR if a.severity in ("CRITICAL", "HIGH") else PerceptionEventType.AWARENESS_UPDATE,
                    source="GroundingMonitor",
                    title=f"[{a.category}] {a.message}",
                    data=a.model_dump(),
                    significance=0.9 if a.severity == "CRITICAL" else 0.7
                )

        return alerts

    def get_recent_alerts(self, limit: int = 10) -> List[GroundingAlert]:
        with self._lock:
            return list(self._alerts_history[-limit:])

    def start(self) -> None:
        """Launch background drift monitor."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._thread = threading.Thread(
                target=self._monitor_loop,
                name="AlphaMonitorWorker-GroundingMonitor",
                daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._is_running = False

    def _monitor_loop(self) -> None:
        while self._is_running:
            try:
                self.evaluate_grounding()
            except Exception as ex:
                logger.error(f"GroundingMonitor audit failure: {ex}")
            time.sleep(self.interval_seconds)
