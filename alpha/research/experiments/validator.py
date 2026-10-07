"""Experiment Validator: Audits experimental designs before execution."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.research.entities import Experiment


class ValidationCheckResult(BaseModel):
    check_name: str
    passed: bool
    details: str


class ExperimentValidationReport(BaseModel):
    experiment_id: str
    is_valid: bool
    checks: List[ValidationCheckResult] = Field(default_factory=list)
    methodological_score: float = Field(default=0.9, ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)


class ExperimentValidator:
    """Rigorous methodological gatekeeper auditing experimental designs."""

    def __init__(self, min_sample_size: int = 20, max_acceptable_risk: float = 0.5):
        self.min_sample_size = min_sample_size
        self.max_acceptable_risk = max_acceptable_risk

    def validate(self, experiment: Experiment) -> ExperimentValidationReport:
        checks: List[ValidationCheckResult] = []
        recommendations: List[str] = []

        # 1. Variables partition check
        has_vars = bool(experiment.independent_variables and experiment.dependent_variables)
        checks.append(ValidationCheckResult(
            check_name="variable_isolation",
            passed=has_vars,
            details=f"Independent: {len(experiment.independent_variables)}, Dependent: {len(experiment.dependent_variables)}"
        ))
        if not has_vars:
            recommendations.append("Explicitly specify at least one independent and dependent variable.")

        # 2. Control condition check
        has_control = bool(experiment.control_conditions)
        checks.append(ValidationCheckResult(
            check_name="control_conditions_present",
            passed=has_control,
            details="Control conditions defined in protocol" if has_control else "Missing baseline control"
        ))
        if not has_control:
            recommendations.append("Add explicit negative/untreated control conditions to isolate treatment effects.")

        # 3. Sample size / power check
        has_power = experiment.sample_size >= self.min_sample_size
        checks.append(ValidationCheckResult(
            check_name="statistical_power",
            passed=has_power,
            details=f"Sample size {experiment.sample_size} >= minimum {self.min_sample_size}"
        ))
        if not has_power:
            recommendations.append(f"Increase sample size to at least {self.min_sample_size} for statistical power.")

        # 4. Risk safety limit
        safe_risk = experiment.estimated_risk <= self.max_acceptable_risk
        checks.append(ValidationCheckResult(
            check_name="risk_containment",
            passed=safe_risk,
            details=f"Estimated risk {experiment.estimated_risk} <= threshold {self.max_acceptable_risk}"
        ))
        if not safe_risk:
            recommendations.append("Mitigate protocol risks before proceeding to trial execution.")

        # Overall validity
        all_passed = all(c.passed for c in checks)
        score = sum(1.0 for c in checks if c.passed) / len(checks)

        if all_passed:
            experiment.status = "VALIDATED"

        return ExperimentValidationReport(
            experiment_id=experiment.experiment_id,
            is_valid=all_passed,
            checks=checks,
            methodological_score=round(score, 3),
            recommendations=recommendations
        )
