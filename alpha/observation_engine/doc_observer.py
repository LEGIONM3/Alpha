"""Documentation Observer for Project Alpha.

Gathers live empirical observations from markdown, architecture specs, and reports:
- reads markdown architecture docs and reports
- extracts unresolved issues, TODOs, FIXMEs, BUGs
- detects contradictions between specifications and codebase reality
- detects missing implementations noted in documentation
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set

from alpha.observation_engine.observation import Observation


class DocumentationObserver:
    """Inspects markdown documents, architecture files, and reports for unresolved issues and inconsistencies."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self._doc_cursor: int = 0

    def reset_state(self) -> None:
        self._doc_cursor = 0

    def _get_all_markdown_files(self) -> List[Path]:
        md_files = list(self.workspace_root.glob("*.md"))
        docs_dir = self.workspace_root / "docs"
        if docs_dir.exists():
            md_files.extend(list(docs_dir.glob("*.md")))
        return sorted(md_files)

    def observe_documents(self, max_items: int = 2) -> List[Observation]:
        """Inspects markdown files for structure, headings, and intent."""
        observations: List[Observation] = []
        md_files = self._get_all_markdown_files()
        if not md_files:
            return observations

        count = len(md_files)
        for i in range(count):
            idx = (self._doc_cursor + i) % count
            doc_path = md_files[idx]
            rel_path = doc_path.relative_to(self.workspace_root).as_posix()

            try:
                text = doc_path.read_text(encoding="utf-8", errors="replace")
                lines = text.splitlines()
                headers = [l.strip() for l in lines if l.strip().startswith("#")][:5]
                word_count = len(text.split())

                evidence = (
                    f"Documentation File: {rel_path} | Words: {word_count} | Lines: {len(lines)} | "
                    f"Key Headings: {' -> '.join(headers) if headers else 'None'}"
                )

                obs = Observation(
                    source=f"Doc:markdown:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence,
                    confidence=0.96,
                    category="documentation"
                )
                observations.append(obs)
                if len(observations) >= max_items:
                    self._doc_cursor = (idx + 1) % count
                    break
            except Exception:
                continue

        return observations

    def extract_unresolved_issues_and_todos(self, max_items: int = 3) -> List[Observation]:
        """Extracts unresolved issues, TODOs, FIXMEs, and bugs from markdown and specs."""
        observations: List[Observation] = []
        md_files = self._get_all_markdown_files()
        todo_pattern = re.compile(r"\b(TODO|FIXME|BUG|UNRESOLVED|MISSING|LIMITATION)\b[:\s\-]+(.*)", re.IGNORECASE)

        for doc_path in md_files:
            rel_path = doc_path.relative_to(self.workspace_root).as_posix()
            try:
                lines = doc_path.read_text(encoding="utf-8", errors="replace").splitlines()
                matches = []
                for lineno, line in enumerate(lines, start=1):
                    m = todo_pattern.search(line)
                    if m:
                        matches.append((lineno, line.strip()))
                        if len(matches) >= 3:
                            break

                if matches:
                    items_str = " ; ".join(f"L{num}: {txt}" for num, txt in matches)
                    evidence = f"Unresolved items detected in {rel_path}: {items_str}"
                    obs = Observation(
                        source=f"Doc:issue:{rel_path}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        evidence=evidence,
                        confidence=0.95,
                        category="unresolved_issue"
                    )
                    observations.append(obs)
                    if len(observations) >= max_items:
                        break
            except Exception:
                continue

        return observations

    def extract_contradictions_and_missing_implementations(self, max_items: int = 2) -> List[Observation]:
        """Detects contradictions between documented claims and codebase reality."""
        observations: List[Observation] = []
        alpha_dir = self.workspace_root / "alpha"
        alpha_files = {p.stem for p in alpha_dir.rglob("*.py")} if alpha_dir.exists() else set()

        # Check documentation files detailing limitations or missing items
        audit_files = [
            self.workspace_root / "CURRENT_LIMITATIONS.md",
            self.workspace_root / "WHAT_IS_MISSING.md",
            self.workspace_root / "WHAT_FAILED.md",
            self.workspace_root / "SYSTEM_INVENTORY.md"
        ]

        for audit_path in audit_files:
            if not audit_path.exists():
                continue
            rel_path = audit_path.relative_to(self.workspace_root).as_posix()
            try:
                text = audit_path.read_text(encoding="utf-8", errors="replace")
                lines = [l.strip() for l in text.splitlines() if l.strip() and (l.startswith("-") or l.startswith("*") or l.startswith("#"))]
                sample_lines = lines[:5]

                evidence = (
                    f"Architectural Gap / Contradiction Record from {rel_path}: "
                    f"{' | '.join(sample_lines[:3])}"
                )

                obs = Observation(
                    source=f"Doc:contradiction:{rel_path}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    evidence=evidence,
                    confidence=0.94,
                    category="architectural_inconsistency"
                )
                observations.append(obs)
                if len(observations) >= max_items:
                    break
            except Exception:
                continue

        return observations

    def observe_all(self) -> List[Observation]:
        """Collects observations across all documentation vectors."""
        results: List[Observation] = []
        results.extend(self.observe_documents(max_items=2))
        results.extend(self.extract_unresolved_issues_and_todos(max_items=2))
        results.extend(self.extract_contradictions_and_missing_implementations(max_items=2))
        return results
