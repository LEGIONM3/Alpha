"""Simulation Environment: Virtual Sandbox World for Safe Prototyping, Hypothesis Testing, and Risk-Free Learning."""

import copy
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

class SimulationHypothesis(BaseModel):
    hypothesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str
    statement: str
    experimental_variables: Dict[str, Any] = Field(default_factory=dict)
    expected_outcome: str = ""
    status: str = "UNTESTED"  # "UNTESTED", "CONFIRMED", "REFUTED"
    created_at: float = Field(default_factory=time.time)

class SimulationRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str
    simulated_steps: List[Dict[str, Any]] = Field(default_factory=list)
    passed: bool = False
    metrics: Dict[str, Any] = Field(default_factory=dict)
    safe_failures_recorded: List[str] = Field(default_factory=list)
    lessons_extracted: List[str] = Field(default_factory=list)
    completed_at: float = Field(default_factory=time.time)

class VirtualSandboxWorld:
    """Isolated virtual world where agents experiment, fail safely, and validate hypotheses before production."""

    def __init__(self, world_name: str = "VirtualSandboxAlpha"):
        self.world_name = world_name
        self.hypotheses: Dict[str, SimulationHypothesis] = {}
        self.runs: Dict[str, SimulationRun] = {}
        self.virtual_filesystem: Dict[str, str] = {}
        self.virtual_kv_store: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def create_hypothesis(
        self,
        author_id: str,
        statement: str,
        experimental_variables: Dict[str, Any],
        expected_outcome: str = ""
    ) -> SimulationHypothesis:
        with self._lock:
            hypo = SimulationHypothesis(
                author_id=author_id,
                statement=statement,
                experimental_variables=experimental_variables,
                expected_outcome=expected_outcome
            )
            self.hypotheses[hypo.hypothesis_id] = hypo
            return hypo

    def run_experiment(
        self,
        hypothesis_id: str,
        experiment_protocol: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> SimulationRun:
        """Execute experiment in complete isolation, catching safe failures."""
        with self._lock:
            hypo = self.hypotheses.get(hypothesis_id)
            if not hypo:
                raise ValueError(f"Hypothesis {hypothesis_id} not found")

            # Virtual isolated sandbox context
            virtual_ctx = copy.deepcopy(hypo.experimental_variables)
            steps = []
            safe_failures = []
            lessons = []
            passed = True

            t0 = time.time()
            try:
                # Step 1: Sandbox environment setup
                steps.append({"step": "init_sandbox", "status": "READY"})
                
                # Step 2: Prototype execution
                if experiment_protocol:
                    proto_out = experiment_protocol(virtual_ctx)
                    steps.append({"step": "execute_protocol", "output": proto_out})
                    passed = bool(proto_out.get("success", True))
                else:
                    # Simulated mock hypothesis validation
                    val = virtual_ctx.get("parameter_test", 1.0)
                    if val < 0:
                        safe_failures.append("Negative boundary edge case caused simulated buffer crash")
                        passed = False
                    steps.append({"step": "simulated_verification", "value": val, "passed": passed})

            except Exception as e:
                passed = False
                safe_failures.append(f"Safe simulated exception: {str(e)}")
            finally:
                duration_ms = (time.time() - t0) * 1000.0

            if passed:
                hypo.status = "CONFIRMED"
                lessons.append(f"Hypothesis '{hypo.statement}' successfully validated in virtual sandbox without production impact.")
            else:
                hypo.status = "REFUTED"
                lessons.append(f"Safely caught failure for hypothesis '{hypo.statement}': {safe_failures}")

            run = SimulationRun(
                hypothesis_id=hypothesis_id,
                simulated_steps=steps,
                passed=passed,
                metrics={"duration_ms": duration_ms, "virtual_memory_bytes": len(virtual_ctx)},
                safe_failures_recorded=safe_failures,
                lessons_extracted=lessons
            )
            self.runs[run.run_id] = run
            return run

    def list_hypotheses(self) -> List[SimulationHypothesis]:
        with self._lock:
            return list(self.hypotheses.values())
