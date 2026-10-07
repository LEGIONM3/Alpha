"""Verification Tools for Alpha OS ToolRegistry."""

from typing import Any, Dict, List, Optional
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolPermission,
    ToolParameter,
    ValidationRule
)
from alpha.verification.engine import VerificationEngine

class VerifySchemaTool(BaseTool):
    def __init__(self, engine: Optional[VerificationEngine] = None):
        super().__init__(
            name="verify_schema",
            description="Verifies that a data dictionary or JSON string satisfies required fields and type constraints.",
            capabilities=[ToolCapability.VERIFICATION],
            permissions=[ToolPermission.ANALYTICS],
            parameters={
                "data": ToolParameter(name="data", type="dict", description="Data object or JSON string to validate.", required=True),
                "required_fields": ToolParameter(name="required_fields", type="list", description="List of mandatory field keys.", required=True),
                "field_types": ToolParameter(name="field_types", type="dict", description="Optional mapping of field names to expected type strings.", required=False, default={})
            }
        )
        self.engine = engine or VerificationEngine()

    def run(self, data: Any, required_fields: List[str], field_types: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        report = self.engine.verify(
            target=data,
            checks=[{
                "type": "schema",
                "rules": {
                    "required_fields": required_fields,
                    "field_types": field_types or {}
                }
            }]
        )
        if not report.passed:
            raise AssertionError(f"Schema verification failed: {'; '.join(report.errors)}")
        return {"status": "verified", "passed": True, "score": report.score}


class VerifyArtifactTool(BaseTool):
    def __init__(self, engine: Optional[VerificationEngine] = None):
        super().__init__(
            name="verify_artifact",
            description="Verifies an artifact file or content string: checks size bounds and syntax validity.",
            capabilities=[ToolCapability.VERIFICATION],
            permissions=[ToolPermission.READ_FS],
            parameters={
                "file_path": ToolParameter(name="file_path", type="string", description="Path to file to verify.", required=False, default=""),
                "content": ToolParameter(name="content", type="string", description="Direct content string if file_path not used.", required=False, default=""),
                "min_bytes": ToolParameter(name="min_bytes", type="integer", description="Minimum byte size required.", required=False, default=1),
                "check_python_syntax": ToolParameter(name="check_python_syntax", type="boolean", description="Whether to verify valid Python syntax.", required=False, default=False)
            }
        )
        self.engine = engine or VerificationEngine()

    def run(self, file_path: str = "", content: str = "", min_bytes: int = 1, check_python_syntax: bool = False) -> Dict[str, Any]:
        target = content if content else None
        rules: Dict[str, Any] = {"min_bytes": min_bytes, "check_python_syntax": check_python_syntax}
        if file_path:
            rules["file_path"] = file_path

        report = self.engine.verify(
            target=target,
            checks=[{"type": "artifact", "rules": rules}]
        )
        if not report.passed:
            raise AssertionError(f"Artifact verification failed: {'; '.join(report.errors)}")
        return {"status": "verified", "passed": True, "score": report.score}


class VerifyFileExistenceTool(BaseTool):
    def __init__(self, engine: Optional[VerificationEngine] = None):
        super().__init__(
            name="verify_file_existence",
            description="Verifies that one or more file paths exist on disk, are non-empty, and regular files.",
            capabilities=[ToolCapability.VERIFICATION, ToolCapability.FILESYSTEM],
            permissions=[ToolPermission.READ_FS],
            parameters={
                "paths": ToolParameter(name="paths", type="list", description="List of file paths to check.", required=True)
            }
        )
        self.engine = engine or VerificationEngine()

    def run(self, paths: List[str]) -> Dict[str, Any]:
        report = self.engine.verify(
            target=paths,
            checks=[{"type": "file_existence", "rules": {"paths": paths}}]
        )
        if not report.passed:
            raise AssertionError(f"File existence verification failed: {'; '.join(report.errors)}")
        return {"status": "verified", "paths_checked": len(paths)}


class VerifyOutputConsistencyTool(BaseTool):
    def __init__(self, engine: Optional[VerificationEngine] = None):
        super().__init__(
            name="verify_output_consistency",
            description="Verifies that tool output does not contain anomaly markers or error traces.",
            capabilities=[ToolCapability.VERIFICATION],
            permissions=[ToolPermission.ANALYTICS],
            parameters={
                "output_text": ToolParameter(name="output_text", type="string", description="Output string to inspect.", required=True),
                "required_keywords": ToolParameter(name="required_keywords", type="list", description="Keywords that must appear.", required=False, default=[])
            }
        )
        self.engine = engine or VerificationEngine()

    def run(self, output_text: str, required_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        report = self.engine.verify(
            target=output_text,
            checks=[{
                "type": "consistency",
                "rules": {"required_keywords": required_keywords or []}
            }]
        )
        if not report.passed:
            raise AssertionError(f"Consistency verification failed: {'; '.join(report.errors)}")
        return {"status": "verified", "score": report.score}
