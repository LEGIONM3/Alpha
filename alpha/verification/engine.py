"""Verification Engine: Multi-stage deterministic verification pipeline."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from alpha.verification.validators import (
    BaseValidator,
    ValidationResult,
    SchemaValidator,
    ArtifactValidator,
    FileExistenceValidator,
    OutputConsistencyValidator,
    ContractValidator
)

class VerificationReport(BaseModel):
    passed: bool
    score: float
    total_checks: int
    passed_checks: int
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validator_results: List[ValidationResult] = Field(default_factory=list)

class VerificationEngine:
    """Orchestrates deterministic validation across schemas, artifacts, files, consistency, and contracts."""

    def __init__(self):
        self._validators: Dict[str, BaseValidator] = {
            "schema": SchemaValidator(),
            "artifact": ArtifactValidator(),
            "file_existence": FileExistenceValidator(),
            "consistency": OutputConsistencyValidator(),
            "contract": ContractValidator()
        }

    def register_validator(self, name: str, validator: BaseValidator) -> None:
        self._validators[name] = validator

    def verify(self, target: Any, checks: List[Dict[str, Any]]) -> VerificationReport:
        """Run a suite of verification checks against a target output or artifact."""
        results: List[ValidationResult] = []
        all_errors: List[str] = []
        all_warnings: List[str] = []

        total = len(checks)
        passed_count = 0

        for check in checks:
            v_type = check.get("type", "").lower()
            rules = check.get("rules", {})

            validator = self._validators.get(v_type)
            if not validator:
                all_errors.append(f"Unknown validator type: '{v_type}'")
                continue

            res = validator.validate(target, rules)
            results.append(res)
            if res.passed:
                passed_count += 1
            else:
                all_errors.extend(res.errors)
            all_warnings.extend(res.warnings)

        score = (passed_count / total) if total > 0 else 1.0

        return VerificationReport(
            passed=len(all_errors) == 0,
            score=round(score, 4),
            total_checks=total,
            passed_checks=passed_count,
            errors=all_errors,
            warnings=all_warnings,
            validator_results=results
        )
