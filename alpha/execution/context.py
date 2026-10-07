"""Execution Context: Thread-safe shared runtime state, variable scoping, and rollback management."""

import re
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from alpha.tools.protocol import ToolResult

class RollbackAction(BaseModel):
    """Encapsulation of a compensatory action to revert a mutated side effect."""
    step_id: str
    description: str

class ExecutionContext:
    """Thread-safe context coordinating data, artifacts, and rollback handlers during plan execution."""

    def __init__(self, initial_vars: Optional[Dict[str, Any]] = None):
        self._lock = threading.RLock()
        self.variables: Dict[str, Any] = initial_vars.copy() if initial_vars else {}
        self.artifacts: Dict[str, Any] = {}
        self.step_results: Dict[str, ToolResult] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self._rollback_actions: List[Tuple[str, str, Callable[[], Any]]] = []

    def set_variable(self, key: str, value: Any) -> None:
        with self._lock:
            self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self.variables.get(key, default)

    def register_step_result(self, step_id: str, result: ToolResult) -> None:
        with self._lock:
            self.step_results[step_id] = result
            self.execution_log.append({
                "step_id": step_id,
                "tool_name": result.tool_name,
                "success": result.success,
                "latency_ms": result.latency_ms
            })
            if result.artifacts_produced:
                for art in result.artifacts_produced:
                    self.artifacts[f"{step_id}:{art}"] = art

    def get_step_result(self, step_id: str) -> Optional[ToolResult]:
        with self._lock:
            return self.step_results.get(step_id)

    def register_artifact(self, name: str, content_or_path: Any) -> None:
        with self._lock:
            self.artifacts[name] = content_or_path

    def get_artifact(self, name: str) -> Optional[Any]:
        with self._lock:
            return self.artifacts.get(name)

    def register_rollback(self, step_id: str, description: str, rollback_fn: Callable[[], Any]) -> None:
        """Register a compensation function to be invoked if downstream execution fails."""
        with self._lock:
            self._rollback_actions.append((step_id, description, rollback_fn))

    def execute_rollbacks(self) -> List[Dict[str, Any]]:
        """Execute registered rollback actions in reverse order (LIFO)."""
        reports: List[Dict[str, Any]] = []
        with self._lock:
            # Process in reverse order
            while self._rollback_actions:
                step_id, desc, fn = self._rollback_actions.pop()
                try:
                    fn()
                    reports.append({
                        "step_id": step_id,
                        "description": desc,
                        "status": "success"
                    })
                except Exception as exc:
                    reports.append({
                        "step_id": step_id,
                        "description": desc,
                        "status": "failed",
                        "error": str(exc)
                    })
        return reports

    def interpolate(self, value: Any) -> Any:
        """Recursively interpolate `{{step_id.output}}` or `{{variable}}` templates."""
        if isinstance(value, str):
            pattern = re.compile(r"\{\{([a-zA-Z0-9_.]+)\}\}")

            def replacer(match):
                key = match.group(1)
                # Check for step_id.output or step_id.field
                if "." in key:
                    parts = key.split(".", 1)
                    step_id, attr = parts[0], parts[1]
                    with self._lock:
                        res = self.step_results.get(step_id)
                        if res:
                            if attr == "output":
                                return str(res.output)
                            elif hasattr(res, attr):
                                return str(getattr(res, attr))
                            elif isinstance(res.output, dict) and attr in res.output:
                                return str(res.output[attr])

                # Check variables
                with self._lock:
                    if key in self.variables:
                        return str(self.variables[key])
                return match.group(0)

            # If the entire string is exactly a single template `{{key}}`, return the raw object
            exact_match = re.fullmatch(r"\{\{([a-zA-Z0-9_.]+)\}\}", value.strip())
            if exact_match:
                key = exact_match.group(1)
                if "." in key:
                    step_id, attr = key.split(".", 1)
                    with self._lock:
                        res = self.step_results.get(step_id)
                        if res:
                            if attr == "output":
                                return res.output
                            elif hasattr(res, attr):
                                return getattr(res, attr)
                            elif isinstance(res.output, dict) and attr in res.output:
                                return res.output[attr]
                with self._lock:
                    if key in self.variables:
                        return self.variables[key]

            return pattern.sub(replacer, value)

        elif isinstance(value, dict):
            return {k: self.interpolate(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.interpolate(v) for v in value]
        return value
