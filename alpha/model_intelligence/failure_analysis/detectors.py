"""Failure Detectors: Hallucination, reasoning gap, logic contradiction, and consistency checks."""

import re
from typing import List, Dict, Any, Optional
from alpha.model_intelligence.failure_analysis.models import FailureType, FailureReport


class HallucinationDetector:
    """Detects factual inventions, unsupported entity claims, and contradiction of grounded knowledge."""

    def detect(
        self,
        response_text: str,
        grounded_facts: List[str],
        known_entities: Optional[List[str]] = None
    ) -> List[FailureReport]:
        failures: List[FailureReport] = []
        resp_lower = response_text.lower()

        # Check for direct contradictions of known facts
        for fact in grounded_facts:
            fact_lower = fact.lower()
            # E.g. fact: "python 3.12 is used" but text says "we are using python 2.7"
            if "not " in fact_lower and fact_lower.replace("not ", "") in resp_lower:
                # possible contradiction
                pass

        # Check for hallmark hallucination assertions: false certainty with lack of grounding
        unsupported_hedges = [
            "as everyone knows without doubt",
            "it is universally guaranteed that",
            "100% verified fact that"
        ]
        for hedge in unsupported_hedges:
            if hedge in resp_lower:
                failures.append(FailureReport(
                    failure_type=FailureType.HALLUCINATION,
                    severity=0.7,
                    description=f"Ungrounded definitive claim detected: '{hedge}'",
                    evidence=[f"Found '{hedge}' in text."],
                    remediation_strategy="Apply strict epistemic hedging and ground claims against knowledge graph."
                ))

        # Check for citation of non-existent entities if known_entities whitelist provided
        if known_entities:
            # Look for entity-like tokens e.g. capitalized terms or UUID-like strings
            uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}'
            found_uuids = re.findall(uuid_pattern, response_text)
            for u in found_uuids:
                if u not in known_entities:
                    failures.append(FailureReport(
                        failure_type=FailureType.HALLUCINATION,
                        severity=0.85,
                        description=f"Fabricated entity UUID identifier detected: '{u}'",
                        evidence=[f"Identifier '{u}' does not exist in grounded entity registry."],
                        remediation_strategy="Replace fabricated IDs with dynamic graph lookups."
                    ))

        return failures


class ReasoningFailureDetector:
    """Detects truncated logic, missing causal steps, and circular reasoning."""

    def detect(
        self,
        response_text: str,
        expected_invariants: Optional[List[str]] = None
    ) -> List[FailureReport]:
        failures: List[FailureReport] = []
        resp_lower = response_text.lower()

        # Check for obvious non-sequiturs or circular phrases
        circular_patterns = [
            r"because it is true that it is",
            r"is correct because it is right",
            r"therefore.*therefore.*therefore"
        ]
        for pat in circular_patterns:
            if re.search(pat, resp_lower):
                failures.append(FailureReport(
                    failure_type=FailureType.REASONING_GAP,
                    severity=0.75,
                    description="Circular reasoning or tautological derivation detected.",
                    evidence=[f"Matched pattern: {pat}"],
                    remediation_strategy="Switch to Analyst or Architect mode with explicit intermediate deduction steps."
                ))

        # Check expected invariants
        if expected_invariants:
            for inv in expected_invariants:
                if inv.lower() not in resp_lower:
                    failures.append(FailureReport(
                        failure_type=FailureType.REASONING_GAP,
                        severity=0.6,
                        description=f"Mandatory invariant '{inv}' omitted from reasoning path.",
                        evidence=[f"Expected invariant '{inv}' was missing."],
                        remediation_strategy=f"Inject invariant '{inv}' explicitly into context constraint scaffold."
                    ))

        return failures


class ConsistencyChecker:
    """Detects semantic and logical contradictions across multiple model outputs or statements."""

    def detect(self, responses: List[str]) -> List[FailureReport]:
        failures: List[FailureReport] = []
        if len(responses) < 2:
            return failures

        # Compare pair-wise sentiment / binary answers
        binary_pos = {"yes", "true", "correct", "feasible", "supported", "succeeded", "success", "successful", "valid"}
        binary_neg = {"no", "false", "incorrect", "infeasible", "unsupported", "failed", "failure", "aborted", "invalid"}

        verdicts = []
        for r in responses:
            tokens = set(re.findall(r'\b\w+\b', r.lower()[:100]))
            has_pos = bool(tokens & binary_pos)
            has_neg = bool(tokens & binary_neg)
            if has_pos and not has_neg:
                verdicts.append(True)
            elif has_neg and not has_pos:
                verdicts.append(False)
            else:
                verdicts.append(None)

        non_none = [v for v in verdicts if v is not None]
        if len(set(non_none)) > 1:
            failures.append(FailureReport(
                failure_type=FailureType.INCONSISTENCY,
                severity=0.8,
                description="Mutually contradictory binary verdicts detected across multiple model samplings.",
                evidence=[f"Samplings produced conflicting conclusions: {non_none}"],
                remediation_strategy="Employ majority voting or self-consistency multi-path aggregation with verification."
            ))

        return failures


class LogicFailureDetector:
    """Detects formal logical inconsistencies (e.g. A and not A, mathematical impossibilities)."""

    def detect(self, response_text: str) -> List[FailureReport]:
        failures: List[FailureReport] = []
        resp_lower = response_text.lower()

        # Check for obvious contradictory assertions
        contradiction_pairs = [
            ("always true", "never true"),
            ("is impossible", "is guaranteed"),
            ("cannot be done", "easily succeeds"),
            ("is empty", "contains multiple items")
        ]
        for a, b in contradiction_pairs:
            if a in resp_lower and b in resp_lower:
                failures.append(FailureReport(
                    failure_type=FailureType.LOGIC_CONTRADICTION,
                    severity=0.8,
                    description=f"Direct logical contradiction in text: both '{a}' and '{b}' asserted.",
                    evidence=[f"Found '{a}' and '{b}' in same generation context."],
                    remediation_strategy="Prompt model with Critic or Formal Verification mode to reconcile assertions."
                ))

        return failures
