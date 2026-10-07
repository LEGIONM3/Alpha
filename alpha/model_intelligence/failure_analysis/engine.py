"""Failure Analysis Engine: Unifies failure detectors, audit log, and calibration."""

from typing import List, Dict, Any, Optional
from alpha.model_intelligence.failure_analysis.models import FailureReport, FailureType
from alpha.model_intelligence.failure_analysis.detectors import (
    HallucinationDetector,
    ReasoningFailureDetector,
    ConsistencyChecker,
    LogicFailureDetector,
)
from alpha.model_intelligence.failure_analysis.calibration import ConfidenceCalibrationEngine


class FailureAnalysisEngine:
    """Detects, audits, and explains why, where, and when model failures occur."""

    def __init__(
        self,
        hallucination_detector: Optional[HallucinationDetector] = None,
        reasoning_detector: Optional[ReasoningFailureDetector] = None,
        consistency_checker: Optional[ConsistencyChecker] = None,
        logic_detector: Optional[LogicFailureDetector] = None,
        calibration_engine: Optional[ConfidenceCalibrationEngine] = None
    ):
        self.hallucination_detector = hallucination_detector or HallucinationDetector()
        self.reasoning_detector = reasoning_detector or ReasoningFailureDetector()
        self.consistency_checker = consistency_checker or ConsistencyChecker()
        self.logic_detector = logic_detector or LogicFailureDetector()
        self.calibration_engine = calibration_engine or ConfidenceCalibrationEngine()
        self.audit_log: List[FailureReport] = []

    def analyze(
        self,
        response_text: str,
        grounded_facts: Optional[List[str]] = None,
        known_entities: Optional[List[str]] = None,
        expected_invariants: Optional[List[str]] = None,
        alternative_responses: Optional[List[str]] = None,
        raw_confidence: Optional[float] = None,
        domain_historical_accuracy: float = 0.75,
        location_context: Optional[str] = None
    ) -> Dict[str, Any]:
        detected_failures: List[FailureReport] = []

        # 1. Hallucination detection
        h_fails = self.hallucination_detector.detect(
            response_text,
            grounded_facts or [],
            known_entities
        )
        detected_failures.extend(h_fails)

        # 2. Reasoning gaps
        r_fails = self.reasoning_detector.detect(response_text, expected_invariants)
        detected_failures.extend(r_fails)

        # 3. Logic contradiction
        l_fails = self.logic_detector.detect(response_text)
        detected_failures.extend(l_fails)

        # 4. Consistency across alternatives
        if alternative_responses:
            c_fails = self.consistency_checker.detect([response_text] + alternative_responses)
            detected_failures.extend(c_fails)

        # 5. Confidence calibration
        calibrated_conf = None
        if raw_confidence is not None:
            calibrated_conf = self.calibration_engine.calibrate(
                raw_confidence,
                domain_historical_accuracy
            )
            if raw_confidence > 0.90 and domain_historical_accuracy < 0.60:
                detected_failures.append(FailureReport(
                    failure_type=FailureType.CONFIDENCE_MISCALIBRATION,
                    severity=0.7,
                    description=f"Overconfident claim ({raw_confidence:.2f}) on low-accuracy domain ({domain_historical_accuracy:.2f})",
                    evidence=[f"Raw: {raw_confidence}, Calibrated: {calibrated_conf}"],
                    remediation_strategy="Apply epistemic shrinkage to confidence estimate."
                ))

        # Tag location context and record to audit log
        for f in detected_failures:
            if location_context and not f.location_context:
                f.location_context = location_context
            self.audit_log.append(f)

        has_failure = len(detected_failures) > 0
        overall_severity = max([f.severity for f in detected_failures], default=0.0)

        return {
            "has_failure": has_failure,
            "overall_severity": overall_severity,
            "calibrated_confidence": calibrated_conf or 0.8,
            "failures": [f.model_dump() for f in detected_failures],
            "total_detected": len(detected_failures)
        }
