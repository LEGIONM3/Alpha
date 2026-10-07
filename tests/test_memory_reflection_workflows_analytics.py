"""Tests for Tool Memory, Tool Reflection, Workflow Engine, Analytics, and Alpha Operating System."""

import tempfile
from pathlib import Path
import pytest
from alpha.operating_system import AlphaOperatingSystem
from alpha.tools.protocol import ToolResult
from alpha.memory.tool_memory import ToolMemoryStore
from alpha.reflection.tool_reflection import ToolReflectionEngine
from alpha.analytics.tracker import PerformanceAnalytics
from alpha.workflows.templates import (
    build_research_workflow,
    build_coding_workflow,
    build_debug_workflow,
    build_analysis_workflow,
    build_validation_workflow
)

def test_tool_memory_and_reflection():
    aos = AlphaOperatingSystem(db_path=":memory:")
    tool_mem = aos.tool_memory
    reflector = aos.tool_reflection

    # Execute dummy tool result
    res = ToolResult(
        call_id="call_1",
        tool_name="fs_read_file",
        success=True,
        output="sample file content line 1\nline 2",
        latency_ms=120.0
    )

    report = reflector.reflect_on_tool_execution(
        tool_name="fs_read_file",
        inputs={"file_path": "test.txt"},
        result=res,
        task_intent="inspect configuration"
    )

    assert report.was_correct is True
    assert report.was_necessary is True
    assert report.was_efficient is True
    assert len(report.distilled_lesson) > 0

    # Verify history recorded in tool memory store
    history = tool_mem.get_tool_history(tool_name="fs_read_file", limit=5)
    assert len(history) >= 1
    assert history[0].tool_name == "fs_read_file"

    # Verify memory manager ingested observation and lesson
    observations = aos.cognitive_engine.memory.working_memory.recent_observations
    assert len(observations) >= 1

def test_performance_analytics():
    analytics = PerformanceAnalytics(db_path=":memory:")
    analytics.record_event("browser_search", success=True, latency_ms=100.0, reward=1.0)
    analytics.record_event("browser_search", success=True, latency_ms=150.0, reward=1.0)
    analytics.record_event("sandbox_execute_code", success=False, latency_ms=250.0, reward=-0.5, error_type="SyntaxError")

    overall = analytics.get_tool_metrics()
    assert overall["total_invocations"] == 3
    assert overall["successes"] == 2
    assert overall["failures"] == 1
    assert overall["success_rate"] == round(2/3, 4)

    b_metrics = analytics.get_tool_metrics("browser_search")
    assert b_metrics["total_invocations"] == 2
    assert b_metrics["success_rate"] == 1.0

    dist = analytics.get_tool_usage_distribution()
    assert dist["browser_search"] == 2
    assert dist["sandbox_execute_code"] == 1

    report_md = analytics.generate_report()
    assert "Alpha Operating System" in report_md
    assert "browser_search" in report_md

def test_workflows_end_to_end():
    with tempfile.TemporaryDirectory() as tmp_dir:
        aos = AlphaOperatingSystem(workspace_root=tmp_dir, db_path=":memory:")

        # 1. Research Workflow
        r_res = aos.run_research_workflow(topic="python concurrency", num_sources=2)
        assert r_res.success is True
        assert r_res.graph_result.completed_nodes >= 2
        assert len(r_res.reflections) >= 2

        # 2. Coding Workflow
        src_file = str(Path(tmp_dir) / "math_ops.py")
        t_file = str(Path(tmp_dir) / "test_math_ops.py")
        code = "def add(a, b):\n    return a + b\n"
        test_code = "from math_ops import add\ndef test_add():\n    assert add(2, 3) == 5\n"

        c_res = aos.run_coding_workflow(
            goal="implement adder",
            target_file=src_file,
            code_content=code,
            test_file=t_file,
            test_content=test_code
        )
        assert c_res.success is True
        assert c_res.graph_result.completed_nodes == 5

        # 3. Debug Workflow
        buggy_file = str(Path(tmp_dir) / "service.py")
        Path(buggy_file).write_text("def run():\n    return 'broken'\n", encoding="utf-8")
        patched_code = "def run():\n    return 'fixed'\n"
        test_verif = "from service import run\nassert run() == 'fixed'\n"

        d_res = aos.run_debug_workflow(
            buggy_file=buggy_file,
            function_name="run",
            patched_file_content=patched_code,
            test_verification_code=test_verif
        )
        assert d_res.success is True
        assert d_res.graph_result.completed_nodes == 5

        # 4. Analysis Workflow
        a_res = aos.run_analysis_workflow(repo_path=tmp_dir)
        assert a_res.success is True
        assert a_res.graph_result.completed_nodes >= 3

        # 5. Validation Workflow
        v_res = aos.run_validation_workflow(
            data_dict={"version": "2.0.0", "active": True},
            file_to_check=src_file,
            required_keys=["version", "active"]
        )
        assert v_res.success is True
        assert v_res.graph_result.completed_nodes == 4
