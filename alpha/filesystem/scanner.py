"""Project Scanner: Traversal, filtering, hash computing, and file metadata extraction."""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

DEFAULT_IGNORED_DIRS: Set[str] = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    "target", "dist", "build", ".pytest_cache", ".mypy_cache", ".idea", ".vscode"
}

DEFAULT_IGNORED_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".bin", ".lock"
}

class FileMetadata(BaseModel):
    path: str
    relative_path: str
    extension: str
    size_bytes: int
    line_count: int = 0
    sha256: str
    is_binary: bool = False

class ProjectScanner:
    """Recursively scans a repository root, indexing file sizes, hashes, and language classifications."""

    def __init__(
        self,
        root_dir: str,
        ignored_dirs: Optional[Set[str]] = None,
        ignored_extensions: Optional[Set[str]] = None,
        max_file_size_bytes: int = 2_000_000
    ):
        self.root_path = Path(root_dir).resolve()
        self.ignored_dirs = ignored_dirs or DEFAULT_IGNORED_DIRS
        self.ignored_extensions = ignored_extensions or DEFAULT_IGNORED_EXTENSIONS
        self.max_file_size_bytes = max_file_size_bytes

    def scan(self, pattern: Optional[str] = None) -> List[FileMetadata]:
        """Scan directory and return list of file metadata objects."""
        results: List[FileMetadata] = []
        if not self.root_path.exists():
            return results

        for root, dirs, files in os.walk(self.root_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs and not d.startswith(".")]

            for file_name in files:
                file_path = Path(root) / file_name
                ext = file_path.suffix.lower()

                if ext in self.ignored_extensions:
                    continue

                if pattern and pattern.lower() not in file_name.lower():
                    continue

                try:
                    stat = file_path.stat()
                    if stat.st_size > self.max_file_size_bytes:
                        continue

                    # Check binary vs text
                    is_binary = False
                    line_count = 0
                    sha256_hash = hashlib.sha256()

                    with open(file_path, "rb") as f:
                        chunk = f.read(4096)
                        if b"\0" in chunk:
                            is_binary = True
                        sha256_hash.update(chunk)
                        while True:
                            more = f.read(65536)
                            if not more:
                                break
                            sha256_hash.update(more)

                    if not is_binary:
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                line_count = sum(1 for _ in f)
                        except Exception:
                            pass

                    rel_path = str(file_path.relative_to(self.root_path)).replace("\\", "/")
                    results.append(FileMetadata(
                        path=str(file_path),
                        relative_path=rel_path,
                        extension=ext,
                        size_bytes=stat.st_size,
                        line_count=line_count,
                        sha256=sha256_hash.hexdigest(),
                        is_binary=is_binary
                    ))
                except (PermissionError, FileNotFoundError):
                    continue

        return results

    def find_files(self, query: str, extension: Optional[str] = None) -> List[FileMetadata]:
        """Find files matching a substring query or extension."""
        all_files = self.scan()
        matched = []
        q = query.lower()
        for f in all_files:
            if extension and f.extension != extension.lower():
                continue
            if q in f.relative_path.lower():
                matched.append(f)
        return matched
