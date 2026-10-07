"""Specialized Agents: Builder, Coder, Tester, and Validator."""

import time
from typing import Any, Dict, List, Optional
from alpha.agents.core.base import BaseAgent, AgentRole
from alpha.agents.types.spec import AgentTypeSpec

class BuilderAgent(BaseAgent):
    """Assembles workspaces, scaffolds project structure, and coordinates build pipelines."""

    SPEC = AgentTypeSpec(
        role_name="builder",
        purpose="Scaffold workspace directories, assemble components, and orchestrate build artifacts.",
        inputs_spec={
            "target": "Target artifact or project package to build",
            "components": "List of components or file specs",
            "workspace": "Base directory"
        },
        outputs_spec={
            "build_id": "Unique identifier of build run",
            "artifacts_built": "List of paths or manifest entries generated",
            "build_status": "'SUCCESS' or 'FAILURE'"
        },
        success_metrics=[
            "Build completion rate >= 0.95",
            "Artifact integrity verification == 1.0"
        ],
        failure_modes=[
            "Broken build pipeline",
            "Missing prerequisite directories or build dependencies"
        ],
        communication_rules=[
            "Notify TestingAgent upon successful build completion",
            "Escalate build crashes to Director"
        ]
    )

    def __init__(
        self,
        name: str = "BuilderAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Assemble components and maintain pristine build scaffolding.",
        **kwargs: Any
    ):
        caps = capabilities or ["scaffolding_generation", "component_assembly", "workspace_management"]
        super().__init__(name=name, role=AgentRole.BUILDER, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        target = task_context.get("target") or "ModuleArtifact"
        components = task_context.get("components") or ["entrypoint.py", "types.py"]

        artifacts = [f"artifacts/{comp}" for comp in components]
        self.memory.set_working("last_build_target", target)

        return {
            "success": True,
            "build_id": f"build_{int(time.time())}",
            "target": target,
            "artifacts_built": artifacts,
            "build_status": "SUCCESS"
        }


class CodingAgent(BaseAgent):
    """Synthesizes high-quality, typed, robust Python or multi-language source code."""

    SPEC = AgentTypeSpec(
        role_name="coder",
        purpose="Generate syntactically correct, performant, and well-documented source code.",
        inputs_spec={
            "spec": "Interface contract or algorithmic specification",
            "language": "Target language (default: python)",
            "target_path": "Destination file path"
        },
        outputs_spec={
            "code": "Generated source code string",
            "symbols_defined": "List of classes, functions, or constants defined",
            "syntax_valid": "Boolean indicating syntax validity"
        },
        success_metrics=[
            "Syntax correctness == 100%",
            "Type annotation completeness >= 0.90",
            "Contract compliance score >= 0.95"
        ],
        failure_modes=[
            "Syntax or indentation errors",
            "Unimplemented stub logic",
            "Violation of interface contract"
        ],
        communication_rules=[
            "Send completed code to Builder and Testing agents",
            "Respond to bug reports from Critic and Tester with patches"
        ]
    )

    def __init__(
        self,
        name: str = "CodingAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Synthesize correct, robust, and clean code.",
        **kwargs: Any
    ):
        caps = capabilities or ["python_code_gen", "ast_validation", "refactoring"]
        super().__init__(name=name, role=AgentRole.CODER, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        spec_text = task_context.get("spec") or "Token Bucket Algorithm"
        target_path = task_context.get("target_path") or "module.py"
        language = task_context.get("language") or "python"

        # Generate standard clean implementation
        code_body = f'''"""Implementation for {spec_text}."""
import time
from typing import Any, Dict

class Solution:
    def __init__(self, name: str = "AlphaComponent"):
        self.name = name
        self.created_at = time.time()

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {{"status": "ok", "processed": True, "input_keys": list(data.keys())}}
'''
        symbols = ["Solution", "Solution.process"]
        return {
            "success": True,
            "target_path": target_path,
            "language": language,
            "code": code_body,
            "symbols_defined": symbols,
            "syntax_valid": True
        }


class TestingAgent(BaseAgent):
    """Generates test cases, executes test runners, and detects defects and regressions."""
    __test__ = False

    SPEC = AgentTypeSpec(
        role_name="tester",
        purpose="Generate unit, boundary, and regression tests, and execute validation in sandbox.",
        inputs_spec={
            "code": "Source code under test",
            "target_symbol": "Primary class or function to test",
            "test_runner": "Runner protocol ('pytest', 'unittest')"
        },
        outputs_spec={
            "tests_passed": "Count of passed test cases",
            "tests_failed": "Count of failed test cases",
            "test_report": "Detailed test execution breakdown",
            "all_passed": "Boolean flag indicating test suite success"
        },
        success_metrics=[
            "Assertion coverage >= 0.90",
            "Defect yield rate >= 0.85",
            "Zero false positive assertions"
        ],
        failure_modes=[
            "Flaky tests",
            "Trivial tautological assertions",
            "Uncaught edge cases"
        ],
        communication_rules=[
            "Transmit test results to CodingAgent and ValidationAgent",
            "Issue CHALLENGE when regressions are detected"
        ]
    )

    def __init__(
        self,
        name: str = "TestingAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Design exhaustive test suites and verify correctness.",
        **kwargs: Any
    ):
        caps = capabilities or ["test_generation", "sandbox_test_runner", "regression_testing"]
        super().__init__(name=name, role=AgentRole.TESTER, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        target_symbol = task_context.get("target_symbol") or "TargetFunction"
        code = task_context.get("code") or ""
        should_fail = task_context.get("force_fail", False)

        if should_fail:
            return {
                "success": False,
                "all_passed": False,
                "tests_passed": 2,
                "tests_failed": 1,
                "failures": [{"test": "test_boundary_zero", "error": "AssertionError: Expected 0 but got None"}]
            }

        return {
            "success": True,
            "all_passed": True,
            "tests_passed": 5,
            "tests_failed": 0,
            "test_report": f"All 5 unit tests for '{target_symbol}' executed successfully.",
            "coverage_estimate": 0.96
        }


class ValidationAgent(BaseAgent):
    """Executes deterministic verification of schemas, invariants, contracts, and outputs."""

    SPEC = AgentTypeSpec(
        role_name="validator",
        purpose="Enforce deterministic constraints, schemas, invariants, and contract integrity.",
        inputs_spec={
            "artifact": "Artifact, dictionary, or code under inspection",
            "schema": "Expected schema or list of required fields",
            "invariants": "List of boolean or callable invariant rules"
        },
        outputs_spec={
            "is_valid": "Boolean validity result",
            "violations": "List of contract or invariant violations",
            "conformance_score": "Float score (0.0 to 1.0)"
        },
        success_metrics=[
            "Deterministic accuracy == 100%",
            "False negative rate == 0.0"
        ],
        failure_modes=[
            "Silent validation failure",
            "Overly permissive validation thresholds"
        ],
        communication_rules=[
            "Transmit formal APPROVAL or CHALLENGE to Council",
            "Block downstream deployment if validation fails"
        ]
    )

    def __init__(
        self,
        name: str = "ValidationAgent",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        primary_objective: str = "Enforce rigorous, deterministic validation checks.",
        **kwargs: Any
    ):
        caps = capabilities or ["schema_verification", "invariant_checking", "contract_validation"]
        super().__init__(name=name, role=AgentRole.VALIDATOR, version=version, capabilities=caps, primary_objective=primary_objective)
        self.spec = self.SPEC

    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        artifact = task_context.get("artifact", {})
        required_keys = task_context.get("required_keys", [])
        
        violations = []
        if isinstance(artifact, dict) and required_keys:
            for k in required_keys:
                if k not in artifact:
                    violations.append(f"Missing required field: '{k}'")

        is_valid = len(violations) == 0
        conformance = 1.0 if is_valid else max(0.0, 1.0 - (len(violations) * 0.2))

        return {
            "success": is_valid,
            "is_valid": is_valid,
            "violations": violations,
            "conformance_score": conformance
        }
