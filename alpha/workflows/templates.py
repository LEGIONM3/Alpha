"""Agentic Workflow Templates: Pre-configured DAGs for Research, Coding, Debugging, Analysis, and Validation."""

from typing import Any, Dict, List, Optional
from alpha.execution.graph import ExecutionGraph, ExecutionNode

def build_research_workflow(topic: str, num_sources: int = 3) -> ExecutionGraph:
    """DAG: Research Topic -> Extract Content -> Summarize & Cite -> Verify Output."""
    graph = ExecutionGraph(name=f"ResearchWorkflow_{topic[:20]}")

    node_search = ExecutionNode(
        node_id="research_search",
        tool_name="browser_search",
        arguments={"query": topic, "num_results": num_sources},
        depends_on=[],
        is_critical=True
    )

    node_summarize = ExecutionNode(
        node_id="research_summarize",
        tool_name="browser_summarize",
        arguments={
            "url": f"https://research.alpha/{topic.replace(' ', '_')}",
            "title": f"Synthesis of {topic.title()}",
            "text": "{{research_search.output}}"
        },
        depends_on=["research_search"],
        is_critical=True
    )

    node_verify = ExecutionNode(
        node_id="research_verify",
        tool_name="verify_output_consistency",
        arguments={
            "output_text": "{{research_summarize.output}}",
            "required_keywords": []
        },
        depends_on=["research_summarize"],
        is_critical=False
    )

    graph.add_node(node_search)
    graph.add_node(node_summarize)
    graph.add_node(node_verify)
    return graph


def build_coding_workflow(
    goal: str,
    target_file: str,
    code_content: str,
    test_file: str,
    test_content: str
) -> ExecutionGraph:
    """DAG: Write Code -> Verify Syntax -> Write Test -> Execute Sandbox -> Run Tests."""
    graph = ExecutionGraph(name=f"CodingWorkflow_{goal[:20]}")

    node_write_src = ExecutionNode(
        node_id="write_source_code",
        tool_name="fs_write_file",
        arguments={"file_path": target_file, "content": code_content, "overwrite": True},
        depends_on=[],
        is_critical=True
    )

    node_verify_src = ExecutionNode(
        node_id="verify_source_code",
        tool_name="verify_artifact",
        arguments={"file_path": target_file, "check_python_syntax": True, "min_bytes": 10},
        depends_on=["write_source_code"],
        is_critical=True
    )

    node_write_test = ExecutionNode(
        node_id="write_test_code",
        tool_name="fs_write_file",
        arguments={"file_path": test_file, "content": test_content, "overwrite": True},
        depends_on=["verify_source_code"],
        is_critical=True
    )

    node_exec_sandbox = ExecutionNode(
        node_id="execute_in_sandbox",
        tool_name="sandbox_execute_code",
        arguments={"language": "python", "code": code_content},
        depends_on=["verify_source_code"],
        is_critical=True
    )

    node_run_tests = ExecutionNode(
        node_id="run_unit_tests",
        tool_name="sandbox_run_unit_tests",
        arguments={"test_target": test_file},
        depends_on=["write_test_code", "execute_in_sandbox"],
        is_critical=True
    )

    graph.add_node(node_write_src)
    graph.add_node(node_verify_src)
    graph.add_node(node_write_test)
    graph.add_node(node_exec_sandbox)
    graph.add_node(node_run_tests)
    return graph


def build_debug_workflow(
    buggy_file: str,
    function_name: str,
    patched_file_content: str,
    test_verification_code: str
) -> ExecutionGraph:
    """DAG: Read Buggy -> Locate Symbol -> Patch File -> Verify Artifact -> Test Execution."""
    graph = ExecutionGraph(name=f"DebugWorkflow_{function_name}")

    node_read = ExecutionNode(
        node_id="read_buggy_source",
        tool_name="fs_read_file",
        arguments={"file_path": buggy_file},
        depends_on=[],
        is_critical=True
    )

    node_locate = ExecutionNode(
        node_id="locate_problem_symbol",
        tool_name="fs_locate_symbols",
        arguments={"name_query": function_name},
        depends_on=["read_buggy_source"],
        is_critical=True
    )

    node_patch = ExecutionNode(
        node_id="apply_patch",
        tool_name="fs_write_file",
        arguments={"file_path": buggy_file, "content": patched_file_content, "overwrite": True},
        depends_on=["locate_problem_symbol"],
        is_critical=True
    )

    node_verify = ExecutionNode(
        node_id="verify_patched_artifact",
        tool_name="verify_artifact",
        arguments={"file_path": buggy_file, "check_python_syntax": True},
        depends_on=["apply_patch"],
        is_critical=True
    )

    node_test = ExecutionNode(
        node_id="test_patched_code",
        tool_name="sandbox_execute_code",
        arguments={"language": "python", "code": test_verification_code},
        depends_on=["verify_patched_artifact"],
        is_critical=True
    )

    graph.add_node(node_read)
    graph.add_node(node_locate)
    graph.add_node(node_patch)
    graph.add_node(node_verify)
    graph.add_node(node_test)
    return graph


def build_analysis_workflow(repo_path: str = "") -> ExecutionGraph:
    """DAG: Project Summary || Dependency Analysis || Git Summary -> Verify Coherence."""
    graph = ExecutionGraph(name="AnalysisWorkflow")

    node_summary = ExecutionNode(
        node_id="project_summary",
        tool_name="fs_project_summary",
        arguments={},
        depends_on=[],
        is_critical=True
    )

    node_deps = ExecutionNode(
        node_id="dependency_analysis",
        tool_name="fs_analyze_dependencies",
        arguments={},
        depends_on=[],
        is_critical=True
    )

    node_git = ExecutionNode(
        node_id="git_summary",
        tool_name="git_summarize",
        arguments={"repo_path": repo_path},
        depends_on=[],
        is_critical=False
    )

    node_verify = ExecutionNode(
        node_id="verify_analysis",
        tool_name="verify_output_consistency",
        arguments={"output_text": "{{project_summary.output}}"},
        depends_on=["project_summary", "dependency_analysis"],
        is_critical=True
    )

    graph.add_node(node_summary)
    graph.add_node(node_deps)
    graph.add_node(node_git)
    graph.add_node(node_verify)
    return graph


def build_validation_workflow(
    data_dict: Dict[str, Any],
    file_to_check: str,
    required_keys: List[str]
) -> ExecutionGraph:
    """DAG: Schema Check || File Existence -> Artifact Verification -> Consistency Verification."""
    graph = ExecutionGraph(name="ValidationWorkflow")

    node_schema = ExecutionNode(
        node_id="validate_schema",
        tool_name="verify_schema",
        arguments={"data": data_dict, "required_fields": required_keys},
        depends_on=[],
        is_critical=True
    )

    node_file = ExecutionNode(
        node_id="validate_file",
        tool_name="verify_file_existence",
        arguments={"paths": [file_to_check]},
        depends_on=[],
        is_critical=True
    )

    node_artifact = ExecutionNode(
        node_id="validate_artifact",
        tool_name="verify_artifact",
        arguments={"file_path": file_to_check, "min_bytes": 1},
        depends_on=["validate_file"],
        is_critical=True
    )

    node_consistency = ExecutionNode(
        node_id="validate_consistency",
        tool_name="verify_output_consistency",
        arguments={"output_text": str(data_dict)},
        depends_on=["validate_schema", "validate_artifact"],
        is_critical=True
    )

    graph.add_node(node_schema)
    graph.add_node(node_file)
    graph.add_node(node_artifact)
    graph.add_node(node_consistency)
    return graph
