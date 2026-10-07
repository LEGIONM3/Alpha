"""Codebase Indexer: AST-based and regex symbol extraction for functions, classes, and variables."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class CodeSymbol(BaseModel):
    name: str
    kind: str  # "class", "function", "method", "variable"
    file_path: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)

class CodebaseIndexer:
    """Extracts symbols, function signatures, and docstrings across code files."""

    def __init__(self, root_dir: str):
        self.root_path = Path(root_dir).resolve()

    def index_file(self, file_path: str) -> List[CodeSymbol]:
        """Index all symbols in a given file."""
        p = Path(file_path)
        if not p.is_absolute():
            p = self.root_path / p

        if not p.exists() or p.is_dir():
            return []

        rel_path = str(p.relative_to(self.root_path) if p.is_relative_to(self.root_path) else p).replace("\\", "/")
        ext = p.suffix.lower()

        if ext == ".py":
            return self._index_python(p, rel_path)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            return self._index_javascript(p, rel_path)
        elif ext == ".rs":
            return self._index_rust(p, rel_path)
        return []

    def _index_python(self, path: Path, rel_path: str) -> List[CodeSymbol]:
        symbols: List[CodeSymbol] = []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(path))
        except Exception:
            return symbols

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                end_lineno = getattr(node, "end_lineno", node.lineno)
                symbols.append(CodeSymbol(
                    name=node.name,
                    kind="class",
                    file_path=rel_path,
                    line_start=node.lineno,
                    line_end=end_lineno,
                    docstring=doc
                ))
                # Index class methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_doc = ast.get_docstring(item)
                        params = [a.arg for a in item.args.args]
                        m_end = getattr(item, "end_lineno", item.lineno)
                        symbols.append(CodeSymbol(
                            name=f"{node.name}.{item.name}",
                            kind="method",
                            file_path=rel_path,
                            line_start=item.lineno,
                            line_end=m_end,
                            docstring=method_doc,
                            parameters=params
                        ))

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                params = [a.arg for a in node.args.args]
                end_lineno = getattr(node, "end_lineno", node.lineno)
                symbols.append(CodeSymbol(
                    name=node.name,
                    kind="function",
                    file_path=rel_path,
                    line_start=node.lineno,
                    line_end=end_lineno,
                    docstring=doc,
                    parameters=params
                ))

        return symbols

    def _index_javascript(self, path: Path, rel_path: str) -> List[CodeSymbol]:
        symbols: List[CodeSymbol] = []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return symbols

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            # function name(...)
            fn_match = re.search(r"function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)", line)
            if fn_match:
                symbols.append(CodeSymbol(
                    name=fn_match.group(1),
                    kind="function",
                    file_path=rel_path,
                    line_start=idx,
                    line_end=idx,
                    parameters=[p.strip() for p in fn_match.group(2).split(",") if p.strip()]
                ))
            # class Name
            cls_match = re.search(r"class\s+([a-zA-Z0-9_$]+)", line)
            if cls_match:
                symbols.append(CodeSymbol(
                    name=cls_match.group(1),
                    kind="class",
                    file_path=rel_path,
                    line_start=idx,
                    line_end=idx
                ))
        return symbols

    def _index_rust(self, path: Path, rel_path: str) -> List[CodeSymbol]:
        symbols: List[CodeSymbol] = []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return symbols

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            fn_match = re.search(r"(?:pub\s+)?fn\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)", line)
            if fn_match:
                symbols.append(CodeSymbol(
                    name=fn_match.group(1),
                    kind="function",
                    file_path=rel_path,
                    line_start=idx,
                    line_end=idx,
                    parameters=[p.strip() for p in fn_match.group(2).split(",") if p.strip()]
                ))
            st_match = re.search(r"(?:pub\s+)?(?:struct|enum|trait)\s+([a-zA-Z0-9_]+)", line)
            if st_match:
                symbols.append(CodeSymbol(
                    name=st_match.group(1),
                    kind="struct",
                    file_path=rel_path,
                    line_start=idx,
                    line_end=idx
                ))
        return symbols

    def locate_symbols(
        self,
        name_query: str,
        symbol_kind: Optional[str] = None,
        file_pattern: Optional[str] = None
    ) -> List[CodeSymbol]:
        """Search all symbols matching query, kind, and optional file pattern."""
        from alpha.filesystem.scanner import ProjectScanner
        scanner = ProjectScanner(str(self.root_path))
        files = scanner.scan()
        results: List[CodeSymbol] = []
        query_lower = name_query.lower()

        for f in files:
            if file_pattern and file_pattern.lower() not in f.relative_path.lower():
                continue
            file_symbols = self.index_file(f.path)
            for sym in file_symbols:
                if symbol_kind and sym.kind != symbol_kind:
                    continue
                if query_lower in sym.name.lower():
                    results.append(sym)

        return results
