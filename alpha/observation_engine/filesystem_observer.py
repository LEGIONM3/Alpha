"""Filesystem Observer for Project Alpha.

Gathers live empirical observations from:
- repository files & structure
- source code (AST structure, classes, functions, imports, docstrings, syntax checks)
- logs (observation, reflection, thought logs, errors, line offsets)
- configuration files (JSON state configs, pyproject, pytest.ini)
- test outputs (.pytest_cache, lastfailed, nodeids)
- generated reports (*REPORT.md, audit findings)
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from alpha.observation_engine.observation import Observation


class FilesystemObserver:
    """Collects empirical observations directly from local filesystem reality."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self._file_cursor: int = 0
        self._config_cursor: int = 0
        self._report_cursor: int = 0
        self._log_offsets: Dict[str, int] = {}

    def reset_state(self) -> None:
        self._file_cursor = 0
        self._config_cursor = 0
        self._report_cursor = 0
        self._log_offsets.clear()

    def observe_source_code(self, max_items: int = 3) -> List[Observation]:
        """Inspects live repository Python source files via AST."""
        observations: List[Observation] = []
        alpha_dir = self.workspace_root / "alpha"
        if not alpha_dir.exists():
            return observations

        py_files = sorted([p for p in alpha_dir.rglob("*.py") if "__pycache__" not in str(p)])
        if not py_files:
            return observations

        count = len(py_files)
        for i in range(count):
            idx = (self._file_cursor + i) % count
            file_path = py_files[idx]
            rel_path = file_path.relative_to(self.workspace_root).as_posix()

            try:
                code_text = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(code_text, filename=str(file_path))

                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                imports = []
                for n in ast.walk(tree):
                    if isinstance(n, ast.Import):
                        for a in n.names:
                            imports.append(a.name)
                    elif isinstance(n, ast.ImportFrom) and n.module:
                        imports.append(n.module)

                docstring = ast.get_docstring(tree) or "No module docstring"
                line_count = len(code_text.splitlines())
                size_bytes = file_path.stat().st_size

                evidence_summary = (
                    f"Source Module: {rel_path} | Lines: {line_count} | Size: {size_bytes}B | "
                    f"Classes ({len(classes)}): {', '.join(classes[:5]) or 'None'} | "
                    f"Functions ({len(functions)}): {', '.join(functions[:5]) or 'None'} | "
                    f"Imports ({len(imports)}): {', '.join(imports[:5]) or 'None'} | "
                    f"Docstring: {docstring[:80].strip()}"
                )

                obs = Observation(
                    source=f"Filesystem:source_code:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence_summary,
                    confidence=0.99,
                    category="source_code"
                )
                observations.append(obs)
                if len(observations) >= max_items:
                    self._file_cursor = (idx + 1) % count
                    break

            except Exception as e:
                obs = Observation(
                    source=f"Filesystem:source_code:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=f"AST parse syntax anomaly in {rel_path}: {e}",
                    confidence=0.90,
                    category="syntax_anomaly"
                )
                observations.append(obs)
                if len(observations) >= max_items:
                    self._file_cursor = (idx + 1) % count
                    break

        return observations

    def observe_config_files(self, max_items: int = 2) -> List[Observation]:
        """Inspects active configuration files, state payloads, and settings."""
        observations: List[Observation] = []
        config_candidates = [
            self.workspace_root / "ACTIVE_COGNITIVE_STATE.json",
            self.workspace_root / "MISSION_STATE.json",
            self.workspace_root / "EPISTEMIC_HEALTH.json",
            self.workspace_root / "pyproject.toml",
            self.workspace_root / "pytest.ini",
            self.workspace_root / ".gitignore"
        ]
        existing_configs = [p for p in config_candidates if p.exists()]
        if not existing_configs:
            return observations

        count = len(existing_configs)
        for i in range(count):
            idx = (self._config_cursor + i) % count
            cfg_path = existing_configs[idx]
            rel_path = cfg_path.relative_to(self.workspace_root).as_posix()

            try:
                if cfg_path.suffix == ".json":
                    data = json.loads(cfg_path.read_text(encoding="utf-8", errors="replace"))
                    keys = list(data.keys()) if isinstance(data, dict) else [f"items_count_{len(data)}"]
                    evidence = (
                        f"Configuration JSON: {rel_path} | Size: {cfg_path.stat().st_size}B | "
                        f"Active Top Keys: {', '.join(str(k) for k in keys[:8])}"
                    )
                else:
                    text = cfg_path.read_text(encoding="utf-8", errors="replace")
                    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
                    evidence = (
                        f"Configuration File: {rel_path} | Non-empty Lines: {len(lines)} | "
                        f"Sample Rules: {'; '.join(lines[:4])}"
                    )

                obs = Observation(
                    source=f"Filesystem:config:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence,
                    confidence=0.98,
                    category="configuration"
                )
                observations.append(obs)
                if len(observations) >= max_items:
                    self._config_cursor = (idx + 1) % count
                    break

            except Exception:
                continue

        return observations

    def observe_logs(self, max_items: int = 2) -> List[Observation]:
        """Inspects runtime execution and thought logs for events, progress, and errors."""
        observations: List[Observation] = []
        log_files = [
            self.workspace_root / "observation_log.jsonl",
            self.workspace_root / "reflection_log.jsonl",
            self.workspace_root / "thought_log.jsonl"
        ]

        for log_path in log_files:
            if not log_path.exists():
                continue
            rel_path = log_path.relative_to(self.workspace_root).as_posix()
            try:
                size = log_path.stat().st_size
                last_offset = self._log_offsets.get(rel_path, 0)
                if size <= last_offset and last_offset > 0:
                    continue

                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_offset)
                    new_lines = [line.strip() for line in f.readlines() if line.strip()]
                    self._log_offsets[rel_path] = f.tell()

                if new_lines:
                    sample = new_lines[-1][:200]
                    obs = Observation(
                        source=f"Filesystem:log:{rel_path}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        evidence=f"Log: {rel_path} appended {len(new_lines)} entries. Recent entry: {sample}",
                        confidence=0.92,
                        category="logs"
                    )
                    observations.append(obs)
                    if len(observations) >= max_items:
                        break
                elif last_offset == 0 and size > 0:
                    obs = Observation(
                        source=f"Filesystem:log:{rel_path}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        evidence=f"Log: {rel_path} active with {size} bytes logged.",
                        confidence=0.90,
                        category="logs"
                    )
                    observations.append(obs)
                    if len(observations) >= max_items:
                        break
            except Exception:
                continue

        return observations

    def observe_test_outputs(self) -> List[Observation]:
        """Inspects pytest cache directory and records test execution state."""
        observations: List[Observation] = []
        cache_dir = self.workspace_root / ".pytest_cache" / "v" / "cache"
        if not cache_dir.exists():
            return observations

        lastfailed_path = cache_dir / "lastfailed"
        failed_count = 0
        failed_keys = []
        if lastfailed_path.exists():
            try:
                lf_data = json.loads(lastfailed_path.read_text(encoding="utf-8"))
                failed_count = len(lf_data)
                failed_keys = list(lf_data.keys())[:3]
            except Exception:
                pass

        nodeids_path = cache_dir / "nodeids"
        total_nodeids = 0
        if nodeids_path.exists():
            try:
                nodes = json.loads(nodeids_path.read_text(encoding="utf-8"))
                total_nodeids = len(nodes)
            except Exception:
                pass

        evidence = (
            f"Pytest Cache State: Cached Nodes: {total_nodeids} | Recorded Last Failures: {failed_count} "
            f"({', '.join(failed_keys) if failed_keys else 'None'})"
        )
        obs = Observation(
            source="Filesystem:test_output:.pytest_cache",
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence=evidence,
            confidence=0.96,
            category="test_output"
        )
        observations.append(obs)
        return observations

    def observe_generated_reports(self, max_items: int = 2) -> List[Observation]:
        """Inspects generated architecture and audit reports."""
        observations: List[Observation] = []
        report_files = sorted(list(self.workspace_root.glob("*REPORT.md")))
        if not report_files:
            return observations

        count = len(report_files)
        for i in range(count):
            idx = (self._report_cursor + i) % count
            report_path = report_files[idx]
            rel_path = report_path.relative_to(self.workspace_root).as_posix()

            try:
                text = report_path.read_text(encoding="utf-8", errors="replace")
                lines = text.splitlines()
                title = lines[0].strip() if lines else "Empty Report"
                mtime = datetime.fromtimestamp(report_path.stat().st_mtime, tz=timezone.utc).isoformat()
                evidence = (
                    f"Generated Report: {rel_path} | Title: {title} | Lines: {len(lines)} | "
                    f"Last Modified: {mtime}"
                )

                obs = Observation(
                    source=f"Filesystem:report:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence,
                    confidence=0.97,
                    category="generated_reports"
                )
                observations.append(obs)
                if len(observations) >= max_items:
                    self._report_cursor = (idx + 1) % count
                    break
            except Exception:
                continue

        return observations

    def observe_all(self) -> List[Observation]:
        """Collects observations across all filesystem categories."""
        results: List[Observation] = []
        results.extend(self.observe_source_code(max_items=3))
        results.extend(self.observe_config_files(max_items=2))
        results.extend(self.observe_logs(max_items=2))
        results.extend(self.observe_test_outputs())
        results.extend(self.observe_generated_reports(max_items=2))
        return results
