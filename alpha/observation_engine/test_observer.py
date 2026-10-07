"""Test Observer for Project Alpha.

Executes live tests and collects empirical test reality:
- executes pytest, integration tests, and benchmark suites
- collects test failures, assertion tracebacks
- collects warnings
- detects performance regressions (runtime changes against baseline)
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from alpha.observation_engine.observation import Observation


class TestObserver:
    """Executes live tests and converts outcomes into empirical observations."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self._test_baseline_durations: Dict[str, float] = {}

    def execute_test_suite(
        self,
        test_path: str = "tests/test_reality_integration.py",
        timeout: float = 30.0
    ) -> List[Observation]:
        """Executes a live test suite and parses failures, warnings, and latency."""
        observations: List[Observation] = []
        target = (self.workspace_root / test_path).resolve()
        if not target.exists():
            obs = Observation(
                source=f"Test:pytest:{test_path}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence=f"Specified test suite {test_path} does not exist on disk.",
                confidence=0.99,
                category="test_missing"
            )
            return [obs]

        cmd = [sys.executable, "-m", "pytest", str(target), "-q", "--tb=short", "-W", "ignore::DeprecationWarning"]
        t0 = time.perf_counter()
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                text=True,
                capture_output=True,
                timeout=timeout,
                env={"LANG": "C", "PATH": os.environ.get("PATH", "")}
            )
            duration_s = round(time.perf_counter() - t0, 3)

            output_text = res.stdout + "\n" + res.stderr
            lines = [l.strip() for l in output_text.splitlines() if l.strip()]

            # Parse outcomes
            passed_match = re.search(r"(\d+)\s+passed", output_text)
            failed_match = re.search(r"(\d+)\s+failed", output_text)
            warning_match = re.search(r"(\d+)\s+warning", output_text)
            error_match = re.search(r"(\d+)\s+error", output_text)

            passed_count = int(passed_match.group(1)) if passed_match else 0
            failed_count = int(failed_match.group(1)) if failed_match else 0
            warning_count = int(warning_match.group(1)) if warning_match else 0
            error_count = int(error_match.group(1)) if error_match else 0

            # Performance check against baseline
            baseline = self._test_baseline_durations.get(test_path)
            perf_note = ""
            if baseline is not None:
                delta_pct = round(((duration_s - baseline) / max(0.01, baseline)) * 100, 1)
                if delta_pct > 30.0:
                    perf_note = f" [PERFORMANCE REGRESSION: +{delta_pct}% slower than baseline {baseline}s]"
                elif delta_pct < -30.0:
                    perf_note = f" [PERFORMANCE ACCELERATION: {delta_pct}% faster than baseline {baseline}s]"
            self._test_baseline_durations[test_path] = duration_s

            if res.returncode == 0:
                evidence = (
                    f"Test Suite '{test_path}' PASSED: {passed_count} passed in {duration_s}s. "
                    f"Warnings: {warning_count}{perf_note}"
                )
                obs = Observation(
                    source=f"Test:pytest:{test_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence,
                    confidence=0.99,
                    category="test_success"
                )
                observations.append(obs)
            else:
                # Extract failures
                failure_lines = [l for l in lines if "FAILED" in l or "ERROR" in l or "AssertionError" in l][:4]
                evidence = (
                    f"Test Suite '{test_path}' FAILED: {failed_count} failed, {error_count} errors, "
                    f"{passed_count} passed in {duration_s}s. Failure Details: {'; '.join(failure_lines)}{perf_note}"
                )
                obs = Observation(
                    source=f"Test:pytest:{test_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence,
                    confidence=0.99,
                    category="test_failure"
                )
                observations.append(obs)

        except subprocess.TimeoutExpired:
            obs = Observation(
                source=f"Test:pytest:{test_path}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence=f"Test Suite '{test_path}' TIMED OUT after {timeout}s [Performance Stagnation].",
                confidence=0.95,
                category="test_timeout"
            )
            observations.append(obs)
        except Exception as exc:
            obs = Observation(
                source=f"Test:pytest:{test_path}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                evidence=f"Test Suite '{test_path}' execution exception: {exc}",
                confidence=0.85,
                category="test_execution_error"
            )
            observations.append(obs)

        return observations

    def observe_test_suite_inventory(self) -> List[Observation]:
        """Inspects test directory layout and counts available test modules."""
        observations: List[Observation] = []
        tests_dir = self.workspace_root / "tests"
        if not tests_dir.exists():
            return observations

        test_files = sorted(list(tests_dir.glob("test_*.py")))
        evidence = (
            f"Test Suite Inventory: Found {len(test_files)} test modules in tests/. "
            f"Active Suites: {', '.join(p.stem for p in test_files[:6])}"
        )
        obs = Observation(
            source="Test:inventory:tests_dir",
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence=evidence,
            confidence=0.98,
            category="test_inventory"
        )
        observations.append(obs)
        return observations

    def observe_all(self) -> List[Observation]:
        """Collects observations by executing test verification and inventory."""
        results: List[Observation] = []
        results.extend(self.observe_test_suite_inventory())
        unit_suites = [
            "tests/test_tools.py",
            "tests/test_sandbox.py",
            "tests/test_verification.py",
            "tests/test_memory.py",
            "tests/test_decomposer.py"
        ]
        cursor = getattr(self, "_suite_cursor", 0)
        target = unit_suites[cursor % len(unit_suites)]
        self._suite_cursor = cursor + 1
        results.extend(self.execute_test_suite(target, timeout=10.0))
        return results
