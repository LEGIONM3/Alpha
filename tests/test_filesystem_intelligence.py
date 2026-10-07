"""Tests for Filesystem Intelligence: Scanner, Indexer, Analyzer, Mapper, and Tools."""

import os
import tempfile
from pathlib import Path
import pytest
from alpha.filesystem.scanner import ProjectScanner
from alpha.filesystem.indexer import CodebaseIndexer
from alpha.filesystem.analyzer import DependencyAnalyzer
from alpha.filesystem.mapper import DirectoryMapper
from alpha.filesystem.tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirTool,
    FindFilesTool,
    LocateSymbolsTool,
    ProjectSummaryTool
)

@pytest.fixture
def sample_project():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        # Create files
        (root / "pkg").mkdir()
        (root / "tests").mkdir()
        
        main_py = root / "pkg" / "main.py"
        main_py.write_text(
            '"""Main module docstring."""\n'
            'import os\n'
            'from pkg.utils import compute_val\n\n'
            'class Worker:\n'
            '    """Worker class docstring."""\n'
            '    def execute(self, task_name):\n'
            '        return compute_val(task_name)\n\n'
            'def run_all():\n'
            '    w = Worker()\n'
            '    return w.execute("job")\n',
            encoding="utf-8"
        )

        utils_py = root / "pkg" / "utils.py"
        utils_py.write_text(
            'def compute_val(val):\n'
            '    return str(val).upper()\n',
            encoding="utf-8"
        )

        reqs = root / "requirements.txt"
        reqs.write_text("pydantic>=2.0\npytest>=8.0\n", encoding="utf-8")

        yield str(root)

def test_project_scanner(sample_project):
    scanner = ProjectScanner(sample_project)
    files = scanner.scan()
    rel_paths = [f.relative_path for f in files]

    assert "pkg/main.py" in rel_paths
    assert "pkg/utils.py" in rel_paths
    assert "requirements.txt" in rel_paths

    # Hash and line count checks
    main_meta = next(f for f in files if f.relative_path == "pkg/main.py")
    assert main_meta.line_count > 5
    assert len(main_meta.sha256) == 64

def test_codebase_indexer(sample_project):
    indexer = CodebaseIndexer(sample_project)
    symbols = indexer.index_file(str(Path(sample_project) / "pkg" / "main.py"))

    sym_names = [s.name for s in symbols]
    assert "Worker" in sym_names
    assert "Worker.execute" in sym_names
    assert "run_all" in sym_names

    worker_sym = next(s for s in symbols if s.name == "Worker")
    assert worker_sym.kind == "class"
    assert "Worker class docstring" in worker_sym.docstring

    loc_symbols = indexer.locate_symbols("compute_val")
    assert len(loc_symbols) >= 1
    assert loc_symbols[0].name == "compute_val"

def test_dependency_analyzer(sample_project):
    analyzer = DependencyAnalyzer(sample_project)
    analysis = analyzer.analyze()

    assert "pydantic" in analysis.external_dependencies
    assert "pytest" in analysis.external_dependencies
    assert "requirements.txt" in analysis.manifests_found

    # Check internal graph
    assert "pkg/main.py" in analysis.internal_module_graph

def test_directory_mapper(sample_project):
    mapper = DirectoryMapper(sample_project)
    tree_str = mapper.generate_tree()
    assert "pkg/" in tree_str
    assert "main.py" in tree_str

    summary = mapper.generate_summary()
    assert summary.total_files >= 3
    assert summary.languages_detected.get(".py", 0) == 2

def test_filesystem_tools(sample_project):
    write_tool = WriteFileTool(sample_project)
    read_tool = ReadFileTool(sample_project)
    list_tool = ListDirTool(sample_project)
    find_tool = FindFilesTool(sample_project)
    sym_tool = LocateSymbolsTool(sample_project)
    sum_tool = ProjectSummaryTool(sample_project)

    # 1. Write file
    w_res = write_tool.run(file_path="pkg/generated.py", content="HELLO = 'WORLD'")
    assert w_res["status"] == "success"

    # 2. Read file
    content = read_tool.run(file_path="pkg/generated.py")
    assert "HELLO = 'WORLD'" in content

    # 3. List dir
    entries = list_tool.run(dir_path="pkg")
    entry_names = [e["name"] for e in entries]
    assert "generated.py" in entry_names

    # 4. Find files
    found = find_tool.run(query="generated")
    assert len(found) == 1

    # 5. Locate symbols
    syms = sym_tool.run(name_query="Worker")
    assert len(syms) >= 1

    # 6. Project summary
    summary = sum_tool.run()
    assert summary["total_files"] >= 4
