"""Dependency Analyzer: External library extraction and internal module graph mapping."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

class DependencyAnalysis(BaseModel):
    root_directory: str
    manifests_found: List[str] = Field(default_factory=list)
    external_dependencies: List[str] = Field(default_factory=list)
    internal_module_graph: Dict[str, List[str]] = Field(default_factory=dict)
    unresolved_imports: List[str] = Field(default_factory=list)

class DependencyAnalyzer:
    """Analyzes package manifests and code imports to build an architectural dependency graph."""

    def __init__(self, root_dir: str):
        self.root_path = Path(root_dir).resolve()

    def analyze(self) -> DependencyAnalysis:
        analysis = DependencyAnalysis(root_directory=str(self.root_path))
        
        # 1. Parse external manifests
        self._parse_manifests(analysis)

        # 2. Parse internal code imports
        self._parse_code_imports(analysis)

        return analysis

    def _parse_manifests(self, analysis: DependencyAnalysis) -> None:
        manifest_files = [
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "Cargo.toml"
        ]
        deps: Set[str] = set()

        for fname in manifest_files:
            p = self.root_path / fname
            if p.exists() and p.is_file():
                analysis.manifests_found.append(fname)
                content = p.read_text(encoding="utf-8", errors="ignore")

                if fname == "requirements.txt":
                    for line in content.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            pkg = re.split(r"[=><!~]", line)[0].strip()
                            if pkg:
                                deps.add(pkg)

                elif fname == "package.json":
                    for section in ["dependencies", "devDependencies"]:
                        matches = re.findall(rf'"{section}"\s*:\s*\{{([^}}]*)\}}', content)
                        if matches:
                            for dep_match in re.findall(r'"([^"]+)"\s*:', matches[0]):
                                deps.add(dep_match)

                elif fname == "Cargo.toml":
                    in_deps = False
                    for line in content.splitlines():
                        if line.startswith("[dependencies]"):
                            in_deps = True
                            continue
                        elif line.startswith("["):
                            in_deps = False
                        if in_deps and "=" in line:
                            pkg = line.split("=")[0].strip()
                            if pkg:
                                deps.add(pkg)

        analysis.external_dependencies = sorted(list(deps))

    def _parse_code_imports(self, analysis: DependencyAnalysis) -> None:
        from alpha.filesystem.scanner import ProjectScanner
        scanner = ProjectScanner(str(self.root_path))
        py_files = scanner.find_files("", extension=".py")

        module_graph: Dict[str, Set[str]] = {}
        all_py_modules = {f.relative_path.replace("/", ".").replace(".py", ""): f.relative_path for f in py_files}

        for f in py_files:
            rel_mod = f.relative_path.replace("/", ".").replace(".py", "")
            module_graph[f.relative_path] = set()

            try:
                content = Path(f.path).read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content, filename=f.path)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = alias.name
                        # Check if internal
                        for mod_name, mod_path in all_py_modules.items():
                            if target == mod_name or target.startswith(mod_name + "."):
                                module_graph[f.relative_path].add(mod_path)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        target = node.module
                        for mod_name, mod_path in all_py_modules.items():
                            if target == mod_name or target.startswith(mod_name + "."):
                                module_graph[f.relative_path].add(mod_path)

        analysis.internal_module_graph = {
            k: sorted(list(v)) for k, v in module_graph.items() if v
        }
