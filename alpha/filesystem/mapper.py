"""Directory Mapper: Visual tree generation and architectural summarization."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from alpha.filesystem.scanner import ProjectScanner, DEFAULT_IGNORED_DIRS

class ArchitectureSummary(BaseModel):
    project_root: str
    total_files: int
    total_lines_of_code: int
    languages_detected: Dict[str, int] = Field(default_factory=dict)
    key_entrypoints: List[str] = Field(default_factory=list)
    test_files_count: int = 0
    directory_structure: str = ""

class DirectoryMapper:
    """Produces visual tree representations and architectural project summaries."""

    def __init__(self, root_dir: str):
        self.root_path = Path(root_dir).resolve()
        self.scanner = ProjectScanner(str(self.root_path))

    def generate_tree(self, max_depth: int = 3) -> str:
        """Generate an ASCII directory tree string."""
        lines: List[str] = [f"{self.root_path.name}/"]
        self._build_tree(self.root_path, "", lines, current_depth=0, max_depth=max_depth)
        return "\n".join(lines)

    def _build_tree(self, directory: Path, prefix: str, lines: List[str], current_depth: int, max_depth: int) -> None:
        if current_depth >= max_depth:
            return

        try:
            entries = sorted(
                [e for e in directory.iterdir() if e.name not in DEFAULT_IGNORED_DIRS and not e.name.startswith(".")],
                key=lambda x: (not x.is_dir(), x.name.lower())
            )
        except PermissionError:
            return

        for idx, entry in enumerate(entries):
            is_last = (idx == len(entries) - 1)
            connector = "\\-- " if is_last else "|-- "
            child_prefix = "    " if is_last else "|   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                self._build_tree(entry, prefix + child_prefix, lines, current_depth + 1, max_depth)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    def generate_summary(self) -> ArchitectureSummary:
        """Analyze repository architecture and return structured summary."""
        files = self.scanner.scan()
        lang_counts: Dict[str, int] = {}
        total_loc = 0
        entrypoints: List[str] = []
        test_count = 0

        common_entrypoint_names = {
            "main.py", "app.py", "run_demo.py", "index.js", "server.js", "main.rs", "lib.rs", "setup.py"
        }

        for f in files:
            ext = f.extension or "no_ext"
            lang_counts[ext] = lang_counts.get(ext, 0) + 1
            total_loc += f.line_count

            name = Path(f.path).name.lower()
            if name in common_entrypoint_names:
                entrypoints.append(f.relative_path)

            if "test" in f.relative_path.lower():
                test_count += 1

        tree_str = self.generate_tree(max_depth=3)

        return ArchitectureSummary(
            project_root=str(self.root_path),
            total_files=len(files),
            total_lines_of_code=total_loc,
            languages_detected=lang_counts,
            key_entrypoints=entrypoints,
            test_files_count=test_count,
            directory_structure=tree_str
        )
