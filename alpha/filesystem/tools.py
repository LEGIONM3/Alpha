"""Standard Filesystem Intelligence Tools for Alpha OS."""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolPermission,
    ToolParameter,
    ValidationRule
)
from alpha.filesystem.scanner import ProjectScanner
from alpha.filesystem.indexer import CodebaseIndexer
from alpha.filesystem.analyzer import DependencyAnalyzer
from alpha.filesystem.mapper import DirectoryMapper

class ReadFileTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="fs_read_file",
            description="Reads the text content of a file from the repository or workspace.",
            capabilities=[ToolCapability.FILESYSTEM],
            permissions=[ToolPermission.READ_FS],
            parameters={
                "file_path": ToolParameter(name="file_path", type="string", description="Relative or absolute path to the file to read.", required=True),
                "max_lines": ToolParameter(name="max_lines", type="integer", description="Maximum number of lines to read.", required=False, default=1000)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="file_path", error_message="file_path cannot be empty.")
            ]
        )
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, file_path: str, max_lines: int = 1000) -> str:
        p = Path(file_path)
        if not p.is_absolute():
            p = self.workspace_root / p

        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not p.is_file():
            raise IsADirectoryError(f"Target path is a directory, not a file: {file_path}")

        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            lines = [f.readline() for _ in range(max_lines)]
        return "".join(lines)


class WriteFileTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="fs_write_file",
            description="Writes text content to a file, creating parent directories if necessary. Supports rollbacks.",
            capabilities=[ToolCapability.FILESYSTEM],
            permissions=[ToolPermission.WRITE_FS],
            parameters={
                "file_path": ToolParameter(name="file_path", type="string", description="Relative or absolute path to write.", required=True),
                "content": ToolParameter(name="content", type="string", description="Text content to write into the file.", required=True),
                "overwrite": ToolParameter(name="overwrite", type="boolean", description="Whether to overwrite existing file.", required=False, default=True)
            },
            validation_rules=[
                ValidationRule(rule_type="non_empty", target_field="file_path", error_message="file_path cannot be empty.")
            ],
            is_reversible=True
        )
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, file_path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        p = Path(file_path)
        if not p.is_absolute():
            p = self.workspace_root / p

        existed = p.exists()
        previous_content = None
        if existed:
            if not overwrite:
                raise FileExistsError(f"File already exists and overwrite=False: {file_path}")
            previous_content = p.read_text(encoding="utf-8", errors="ignore")

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

        return {
            "status": "success",
            "file_path": str(p),
            "bytes_written": len(content.encode("utf-8")),
            "existed_prior": existed,
            "__artifacts__": [str(p)],
            "__metadata__": {
                "previous_content": previous_content,
                "file_path": str(p)
            }
        }


class ListDirTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="fs_list_dir",
            description="Lists entries in a specified directory.",
            capabilities=[ToolCapability.FILESYSTEM],
            permissions=[ToolPermission.READ_FS],
            parameters={
                "dir_path": ToolParameter(name="dir_path", type="string", description="Directory path to list. Empty string defaults to root.", required=False, default="")
            }
        )
        self.workspace_root = Path(workspace_root).resolve()

    def run(self, dir_path: str = "") -> List[Dict[str, Any]]:
        p = Path(dir_path) if dir_path else self.workspace_root
        if not p.is_absolute():
            p = self.workspace_root / p

        if not p.exists() or not p.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        entries = []
        for item in sorted(p.iterdir()):
            entries.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size_bytes": item.stat().st_size if item.is_file() else 0
            })
        return entries


class FindFilesTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="fs_find_files",
            description="Searches for files matching a query substring or file extension.",
            capabilities=[ToolCapability.FILESYSTEM, ToolCapability.SEARCH],
            permissions=[ToolPermission.READ_FS],
            parameters={
                "query": ToolParameter(name="query", type="string", description="Substring pattern to search for in file paths.", required=True),
                "extension": ToolParameter(name="extension", type="string", description="Filter by extension e.g. '.py'.", required=False, default=None)
            }
        )
        self.scanner = ProjectScanner(workspace_root)

    def run(self, query: str, extension: Optional[str] = None) -> List[Dict[str, Any]]:
        matches = self.scanner.find_files(query, extension=extension)
        return [m.model_dump() for m in matches]


class LocateSymbolsTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="fs_locate_symbols",
            description="Locates code symbols (functions, classes, methods) in the repository using AST analysis.",
            capabilities=[ToolCapability.FILESYSTEM, ToolCapability.SEARCH],
            permissions=[ToolPermission.READ_FS],
            parameters={
                "name_query": ToolParameter(name="name_query", type="string", description="Name or partial name of class, function, or method.", required=True),
                "symbol_kind": ToolParameter(name="symbol_kind", type="string", description="Optional filter: 'class', 'function', or 'method'.", required=False, default=None)
            }
        )
        self.indexer = CodebaseIndexer(workspace_root)

    def run(self, name_query: str, symbol_kind: Optional[str] = None) -> List[Dict[str, Any]]:
        symbols = self.indexer.locate_symbols(name_query, symbol_kind=symbol_kind)
        return [s.model_dump() for s in symbols]


class AnalyzeDependenciesTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="fs_analyze_dependencies",
            description="Analyzes package manifests and cross-module code imports in the codebase.",
            capabilities=[ToolCapability.FILESYSTEM, ToolCapability.ANALYTICS],
            permissions=[ToolPermission.READ_FS]
        )
        self.analyzer = DependencyAnalyzer(workspace_root)

    def run(self) -> Dict[str, Any]:
        return self.analyzer.analyze().model_dump()


class ProjectSummaryTool(BaseTool):
    def __init__(self, workspace_root: str):
        super().__init__(
            name="fs_project_summary",
            description="Generates an architectural summary and directory tree of the repository.",
            capabilities=[ToolCapability.FILESYSTEM, ToolCapability.ANALYTICS],
            permissions=[ToolPermission.READ_FS]
        )
        self.mapper = DirectoryMapper(workspace_root)

    def run(self) -> Dict[str, Any]:
        return self.mapper.generate_summary().model_dump()
