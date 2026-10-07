"""Filesystem Intelligence package for Alpha OS."""

from alpha.filesystem.scanner import ProjectScanner, FileMetadata
from alpha.filesystem.indexer import CodebaseIndexer, CodeSymbol
from alpha.filesystem.analyzer import DependencyAnalyzer, DependencyAnalysis
from alpha.filesystem.mapper import DirectoryMapper, ArchitectureSummary
from alpha.filesystem.tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirTool,
    FindFilesTool,
    LocateSymbolsTool,
    AnalyzeDependenciesTool,
    ProjectSummaryTool,
)

__all__ = [
    "ProjectScanner",
    "FileMetadata",
    "CodebaseIndexer",
    "CodeSymbol",
    "DependencyAnalyzer",
    "DependencyAnalysis",
    "DirectoryMapper",
    "ArchitectureSummary",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirTool",
    "FindFilesTool",
    "LocateSymbolsTool",
    "AnalyzeDependenciesTool",
    "ProjectSummaryTool",
]
