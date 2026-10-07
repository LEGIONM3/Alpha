"""Real Observation Engine for Project Alpha.

Discovers empirical, verifiable observations from external reality:
- Repository source code (AST structure, metrics, classes, functions, imports)
- Markdown documentation (specifications, architecture, mission state)
- Reports (epistemic health, monitoring, benchmarks)
- System logs (event logs, execution history)
- Test results (.pytest_cache, test files, assertion density)
- Runtime telemetry (memory, CPU, thread count, execution metrics)
- Filesystem metadata (file counts, modification timestamps, directory layouts)

Guarantees discovery of NEW information without replaying past observations.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Set

import psutil
from pydantic import BaseModel, Field, model_validator


class ObservationRecord(BaseModel):
    """Represents a verified piece of external reality acquired during the cycle."""
    source: str        # e.g., "SourceCodeFile", "MarkdownDoc", "Report", "LogFile", "TestResult", "RuntimeTelemetry", "FilesystemMetadata"
    timestamp: str     # ISO 8601 format of acquisition time
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    content: str       # The raw, extracted verifiable content
    category: str      # e.g., "CodeStructure", "Documentation", "ReportFinding", "ExecutionLog", "TestOutcome", "SystemTelemetry", "FilesystemStructure"
    hash: str = Field(default="")

    @model_validator(mode="after")
    def compute_hash_if_missing(self) -> "ObservationRecord":
        if not self.hash:
            raw = f"{self.source}:{self.category}:{self.content}"
            h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            object.__setattr__(self, "hash", h)
        return self


class ObservationEngine:
    """The primary module responsible for acquiring verifiable external information

    from the operational environment (filesystem, repository, logs, telemetry).
    Guarantees discovery of NEW information by hashing and deduplication.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self._observed_hashes: Set[str] = set()
        self._file_cursor: int = 0
        self._doc_cursor: int = 0
        self._report_cursor: int = 0
        self._log_offsets: Dict[str, int] = {}
        self._cycle_counter: int = 0

    def reset_state(self) -> None:
        """Reset internal cursors and observed hashes if needed."""
        self._observed_hashes.clear()
        self._file_cursor = 0
        self._doc_cursor = 0
        self._report_cursor = 0
        self._log_offsets.clear()
        self._cycle_counter = 0

    def acquire_observations(
        self,
        targets: Optional[List[str]] = None,
        max_per_category: int = 3
    ) -> List[ObservationRecord]:
        """Acquires genuinely NEW observations based on specified targets.

        If targets is None or empty, samples across all available real sources.
        Filters out any observation whose hash has already been registered.
        """
        self._cycle_counter += 1
        if not targets:
            targets = [
                "codebase",
                "docs",
                "reports",
                "logs",
                "test_results",
                "telemetry",
                "filesystem"
            ]

        candidates: List[ObservationRecord] = []

        for target in targets:
            target_lower = target.lower()
            if target_lower in ("codebase", "source", "source_code"):
                candidates.extend(self._observe_source_code(max_items=max_per_category))
            elif target_lower in ("docs", "documentation", "markdown"):
                candidates.extend(self._observe_markdown_docs(max_items=max_per_category))
            elif target_lower in ("reports", "report"):
                candidates.extend(self._observe_reports(max_items=max_per_category))
            elif target_lower in ("logs", "log"):
                candidates.extend(self._observe_logs(max_items=max_per_category))
            elif target_lower in ("test_results", "tests", "test"):
                candidates.extend(self._observe_test_results(max_items=max_per_category))
            elif target_lower in ("telemetry", "runtime", "runtime_telemetry"):
                candidates.extend(self._observe_runtime_telemetry())
            elif target_lower in ("filesystem", "fs", "metadata"):
                candidates.extend(self._observe_filesystem_metadata())
            elif target_lower == "all":
                candidates.extend(self._observe_source_code(max_items=max_per_category))
                candidates.extend(self._observe_markdown_docs(max_items=max_per_category))
                candidates.extend(self._observe_reports(max_items=max_per_category))
                candidates.extend(self._observe_logs(max_items=max_per_category))
                candidates.extend(self._observe_test_results(max_items=max_per_category))
                candidates.extend(self._observe_runtime_telemetry())
                candidates.extend(self._observe_filesystem_metadata())

        # Filter out previously observed hashes to guarantee NO REPLAY
        new_records: List[ObservationRecord] = []
        for rec in candidates:
            if rec.hash not in self._observed_hashes:
                self._observed_hashes.add(rec.hash)
                new_records.append(rec)

        # Fallback guarantee: If static items were already seen, runtime telemetry
        # with timestamp guarantees progress with empirical telemetry
        if not new_records:
            fresh_telemetry = self._observe_runtime_telemetry(force_unique=True)
            for rec in fresh_telemetry:
                if rec.hash not in self._observed_hashes:
                    self._observed_hashes.add(rec.hash)
                    new_records.append(rec)

        return new_records

    # -------------------------------------------------------------------------
    # Empirical Source Collectors
    # -------------------------------------------------------------------------

    def _observe_source_code(self, max_items: int = 3) -> List[ObservationRecord]:
        """Inspects actual repository Python source files via AST."""
        records: List[ObservationRecord] = []
        alpha_dir = self.workspace_root / "alpha"
        if not alpha_dir.exists():
            return records

        py_files = sorted([p for p in alpha_dir.rglob("*.py") if "__pycache__" not in str(p)])
        if not py_files:
            return records

        count = len(py_files)
        # Advance rotating cursor across available files
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

                content_summary = (
                    f"Module: {rel_path} | Lines: {line_count} | Size: {size_bytes}B | "
                    f"Classes ({len(classes)}): {', '.join(classes[:5]) or 'None'} | "
                    f"Functions ({len(functions)}): {', '.join(functions[:5]) or 'None'} | "
                    f"Imports ({len(imports)}): {', '.join(imports[:5]) or 'None'} | "
                    f"Docstring: {docstring[:80].strip()}"
                )

                rec = ObservationRecord(
                    source=f"SourceCode:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    confidence=0.99,
                    content=content_summary,
                    category="CodeStructure"
                )

                if rec.hash not in self._observed_hashes:
                    records.append(rec)
                    if len(records) >= max_items:
                        self._file_cursor = (idx + 1) % count
                        break
            except Exception as e:
                rec = ObservationRecord(
                    source=f"SourceCode:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    confidence=0.90,
                    content=f"AST parse anomaly in {rel_path}: {e}",
                    category="SyntaxAnomaly"
                )
                if rec.hash not in self._observed_hashes:
                    records.append(rec)
                    if len(records) >= max_items:
                        self._file_cursor = (idx + 1) % count
                        break

        return records

    def _observe_markdown_docs(self, max_items: int = 3) -> List[ObservationRecord]:
        """Inspects markdown documents for architecture specs, missions, and identity."""
        records: List[ObservationRecord] = []
        md_files = sorted(list(self.workspace_root.glob("*.md")) + list((self.workspace_root / "docs").glob("*.md") if (self.workspace_root / "docs").exists() else []))
        if not md_files:
            return records

        count = len(md_files)
        for i in range(count):
            idx = (self._doc_cursor + i) % count
            file_path = md_files[idx]
            rel_path = file_path.relative_to(self.workspace_root).as_posix()

            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
                lines = text.splitlines()
                headers = [line.strip() for line in lines if line.strip().startswith("#")][:6]
                word_count = len(text.split())

                content_summary = (
                    f"Markdown Document: {rel_path} | Words: {word_count} | Lines: {len(lines)} | "
                    f"Top Headings: {' -> '.join(headers) if headers else 'None'}"
                )

                rec = ObservationRecord(
                    source=f"MarkdownDoc:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    confidence=0.95,
                    content=content_summary,
                    category="Documentation"
                )

                if rec.hash not in self._observed_hashes:
                    records.append(rec)
                    if len(records) >= max_items:
                        self._doc_cursor = (idx + 1) % count
                        break
            except Exception as e:
                continue

        return records

    def _observe_reports(self, max_items: int = 3) -> List[ObservationRecord]:
        """Inspects reports and health audits."""
        records: List[ObservationRecord] = []
        report_files = sorted(list(self.workspace_root.glob("*REPORT.md")) + list(self.workspace_root.glob("*.json")))
        if not report_files:
            return records

        count = len(report_files)
        for i in range(count):
            idx = (self._report_cursor + i) % count
            file_path = report_files[idx]
            rel_path = file_path.relative_to(self.workspace_root).as_posix()

            try:
                if file_path.suffix == ".json":
                    data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
                    keys = list(data.keys()) if isinstance(data, dict) else [f"array_len_{len(data)}"]
                    content_summary = (
                        f"JSON Report: {rel_path} | Size: {file_path.stat().st_size}B | "
                        f"Top Keys: {', '.join(str(k) for k in keys[:8])}"
                    )
                else:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                    lines = text.splitlines()
                    title = lines[0].strip() if lines else "Empty Report"
                    content_summary = (
                        f"Audit Report: {rel_path} | Title: {title} | Lines: {len(lines)} | "
                        f"Modified: {datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()}"
                    )

                rec = ObservationRecord(
                    source=f"Report:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    confidence=0.98,
                    content=content_summary,
                    category="ReportFinding"
                )

                if rec.hash not in self._observed_hashes:
                    records.append(rec)
                    if len(records) >= max_items:
                        self._report_cursor = (idx + 1) % count
                        break
            except Exception:
                continue

        return records

    def _observe_logs(self, max_items: int = 3) -> List[ObservationRecord]:
        """Inspects system execution logs."""
        records: List[ObservationRecord] = []
        log_files = [
            self.workspace_root / "observation_log.jsonl",
            self.workspace_root / "reflection_log.jsonl"
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
                    rec = ObservationRecord(
                        source=f"LogFile:{rel_path}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        confidence=0.90,
                        content=f"Log: {rel_path} appended {len(new_lines)} entries. Latest entry snippet: {sample}",
                        category="ExecutionLog"
                    )
                    if rec.hash not in self._observed_hashes:
                        records.append(rec)
                        if len(records) >= max_items:
                            break
                elif last_offset == 0 and size > 0:
                    rec = ObservationRecord(
                        source=f"LogFile:{rel_path}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        confidence=0.90,
                        content=f"Log: {rel_path} exists with {size} bytes logged.",
                        category="ExecutionLog"
                    )
                    if rec.hash not in self._observed_hashes:
                        records.append(rec)
            except Exception:
                continue

        return records

    def _observe_test_results(self, max_items: int = 3) -> List[ObservationRecord]:
        """Inspects pytest cache and test directory state."""
        records: List[ObservationRecord] = []
        tests_dir = self.workspace_root / "tests"
        if not tests_dir.exists():
            return records

        test_files = sorted(list(tests_dir.glob("test_*.py")))
        cache_dir = self.workspace_root / ".pytest_cache" / "v" / "cache"

        # Check lastfailed if present
        lastfailed_path = cache_dir / "lastfailed" if cache_dir.exists() else None
        lastfailed_count = 0
        if lastfailed_path and lastfailed_path.exists():
            try:
                lf_data = json.loads(lastfailed_path.read_text(encoding="utf-8"))
                lastfailed_count = len(lf_data)
            except Exception:
                pass

        content = (
            f"Test Suite Status: {len(test_files)} test modules in tests/ | "
            f"Pytest Cache Available: {cache_dir.exists()} | "
            f"Recorded Failed Tests: {lastfailed_count}"
        )
        rec = ObservationRecord(
            source="TestSuite:LocalDirectory",
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=0.95,
            content=content,
            category="TestOutcome"
        )
        if rec.hash not in self._observed_hashes:
            records.append(rec)

        return records

    def _observe_runtime_telemetry(self, force_unique: bool = False) -> List[ObservationRecord]:
        """Gathers verifiable process and system telemetry."""
        records: List[ObservationRecord] = []
        try:
            proc = psutil.Process(os.getpid())
            mem_info = proc.memory_info()
            cpu_percent = proc.cpu_percent(interval=None)
            threads_count = proc.num_threads()
            open_files_count = len(proc.open_files()) if hasattr(proc, "open_files") else 0
        except Exception:
            mem_info = None
            cpu_percent = 0.0
            threads_count = 1
            open_files_count = 0

        rss_mb = round(mem_info.rss / (1024 * 1024), 2) if mem_info else 0.0
        now_ts = datetime.now(timezone.utc).isoformat()

        content = (
            f"Runtime Telemetry [Cycle #{self._cycle_counter}]: "
            f"PID: {os.getpid()} | Python: {sys.version.split()[0]} | "
            f"Memory RSS: {rss_mb} MB | Threads: {threads_count} | "
            f"Open Files: {open_files_count} | CPU: {cpu_percent}% | "
            f"Timestamp: {now_ts if force_unique else now_ts[:19]}"
        )

        rec = ObservationRecord(
            source="RuntimeTelemetry:Process",
            timestamp=now_ts,
            confidence=0.99,
            content=content,
            category="SystemTelemetry"
        )
        records.append(rec)
        return records

    def _observe_filesystem_metadata(self) -> List[ObservationRecord]:
        """Gathers workspace storage and file distribution metadata."""
        records: List[ObservationRecord] = []
        try:
            ext_counts: Dict[str, int] = {}
            total_size = 0
            for root, dirs, files in os.walk(self.workspace_root):
                if any(ignored in root for ignored in [".git", ".pytest_cache", "__pycache__"]):
                    continue
                for f in files:
                    ext = Path(f).suffix or ".no_ext"
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass

            top_exts = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ext_summary = ", ".join(f"{ext}: {cnt}" for ext, cnt in top_exts)

            content = (
                f"Workspace Filesystem Metadata: Total Files: {sum(ext_counts.values())} | "
                f"Storage Size: {round(total_size / (1024 * 1024), 2)} MB | "
                f"Top File Types: {ext_summary}"
            )

            rec = ObservationRecord(
                source="FilesystemMetadata:WorkspaceRoot",
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.98,
                content=content,
                category="FilesystemStructure"
            )
            records.append(rec)
        except Exception:
            pass

        return records


# Singleton default instance
observation_engine = ObservationEngine()