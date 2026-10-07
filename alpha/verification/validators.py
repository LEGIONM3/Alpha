"""Deterministic validators for Alpha OS: Schema, Artifact, Unit Test, File Existence, Consistency, and Contracts."""

import ast
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ValidationResult(BaseModel):
    validator_name: str
    passed: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)

class BaseValidator(ABC):
    @abstractmethod
    def validate(self, target: Any, rules: Dict[str, Any]) -> ValidationResult:
        raise NotImplementedError


class SchemaValidator(BaseValidator):
    """Validates dictionaries or JSON strings against required fields and expected types."""

    def validate(self, target: Any, rules: Dict[str, Any]) -> ValidationResult:
        errors = []
        warnings = []
        data = target

        if isinstance(target, str):
            try:
                data = json.loads(target)
            except Exception as e:
                return ValidationResult(
                    validator_name="SchemaValidator",
                    passed=False,
                    errors=[f"Target is not valid JSON: {str(e)}"]
                )

        if not isinstance(data, dict):
            return ValidationResult(
                validator_name="SchemaValidator",
                passed=False,
                errors=[f"Expected JSON object / dict, got {type(data).__name__}"]
            )

        required_fields = rules.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required schema field: '{field}'")
            elif data[field] is None and not rules.get("allow_null", False):
                errors.append(f"Field '{field}' cannot be null.")

        field_types = rules.get("field_types", {})
        type_map = {
            "str": str, "string": str,
            "int": int, "integer": int,
            "float": float, "number": (int, float),
            "bool": bool, "boolean": bool,
            "dict": dict, "object": dict,
            "list": list, "array": list
        }
        for field, expected_type_str in field_types.items():
            if field in data and data[field] is not None:
                py_type = type_map.get(expected_type_str.lower())
                if py_type and not isinstance(data[field], py_type):
                    errors.append(f"Field '{field}' expected {expected_type_str}, got {type(data[field]).__name__}")

        return ValidationResult(
            validator_name="SchemaValidator",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details={"checked_fields": len(required_fields)}
        )


class ArtifactValidator(BaseValidator):
    """Validates code and document artifacts: non-empty, byte bounds, and syntax validity."""

    def validate(self, target: Any, rules: Dict[str, Any]) -> ValidationResult:
        errors = []
        warnings = []
        content = ""
        file_path = rules.get("file_path")

        if file_path:
            p = Path(file_path)
            if not p.exists():
                return ValidationResult(
                    validator_name="ArtifactValidator",
                    passed=False,
                    errors=[f"Artifact file does not exist: {file_path}"]
                )
            content = p.read_text(encoding="utf-8", errors="ignore")
        elif isinstance(target, str):
            content = target
        else:
            return ValidationResult(
                validator_name="ArtifactValidator",
                passed=False,
                errors=[f"Unsupported artifact input: {type(target)}"]
            )

        min_bytes = rules.get("min_bytes", 1)
        max_bytes = rules.get("max_bytes", 10_000_000)

        byte_len = len(content.encode("utf-8"))
        if byte_len < min_bytes:
            errors.append(f"Artifact byte length {byte_len} is less than minimum {min_bytes}")
        if byte_len > max_bytes:
            errors.append(f"Artifact byte length {byte_len} exceeds maximum {max_bytes}")

        # Check Python syntax if requested
        if rules.get("check_python_syntax", False) or (file_path and file_path.endswith(".py")):
            try:
                ast.parse(content)
            except SyntaxError as se:
                errors.append(f"Python syntax error at line {se.lineno}: {se.msg}")

        return ValidationResult(
            validator_name="ArtifactValidator",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details={"byte_length": byte_len}
        )


class FileExistenceValidator(BaseValidator):
    """Verifies that claimed generated or modified files physically exist on the filesystem."""

    def validate(self, target: Any, rules: Dict[str, Any]) -> ValidationResult:
        errors = []
        paths: List[str] = []

        if isinstance(target, str):
            paths = [target]
        elif isinstance(target, list):
            paths = [str(p) for p in target]
        elif "paths" in rules:
            paths = rules["paths"]

        for p_str in paths:
            p = Path(p_str)
            if not p.exists():
                errors.append(f"Claimed file does not exist on disk: '{p_str}'")
            elif not p.is_file():
                errors.append(f"Path exists but is not a regular file: '{p_str}'")
            elif p.stat().st_size == 0 and not rules.get("allow_empty", False):
                errors.append(f"File exists but is empty (0 bytes): '{p_str}'")

        return ValidationResult(
            validator_name="FileExistenceValidator",
            passed=len(errors) == 0,
            errors=errors,
            details={"paths_verified": len(paths)}
        )


class OutputConsistencyValidator(BaseValidator):
    """Detects failure markers and ensures consistency in output."""

    FAILURE_PATTERNS = [
        r"traceback\s+\(most recent call last\):",
        r"exception:\s+",
        r"syntaxerror:\s+",
        r"fatal error:",
        r"internal server error",
        r"404 not found",
        r"connection refused",
        r"failed to connect"
    ]

    def validate(self, target: Any, rules: Dict[str, Any]) -> ValidationResult:
        errors = []
        warnings = []
        text = str(target).lower()

        ignore_errors = rules.get("ignore_errors", False)
        if not ignore_errors:
            for pat in self.FAILURE_PATTERNS:
                if re.search(pat, text):
                    errors.append(f"Output contains failure marker matching pattern: '{pat}'")

        required_keywords = rules.get("required_keywords", [])
        for kw in required_keywords:
            if kw.lower() not in text:
                errors.append(f"Output missing required keyword: '{kw}'")

        return ValidationResult(
            validator_name="OutputConsistencyValidator",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class ContractValidator(BaseValidator):
    """Evaluates formal assertions and boolean conditions against the target."""

    def validate(self, target: Any, rules: Dict[str, Any]) -> ValidationResult:
        errors = []
        assertions = rules.get("assertions", [])

        # Local context for safe evaluation
        eval_ctx = {"target": target, "len": len, "isinstance": isinstance}
        for assertion in assertions:
            expr = assertion.get("expr", "")
            description = assertion.get("description", expr)
            try:
                passed = bool(eval(expr, {"__builtins__": {}}, eval_ctx))
                if not passed:
                    errors.append(f"Contract Assertion Failed: {description}")
            except Exception as e:
                errors.append(f"Contract Evaluation Error for '{description}': {str(e)}")

        return ValidationResult(
            validator_name="ContractValidator",
            passed=len(errors) == 0,
            errors=errors,
            details={"assertions_checked": len(assertions)}
        )
