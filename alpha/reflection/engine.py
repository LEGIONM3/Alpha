"""Reflection Engine: Analyzes execution outputs, formulates critiques, and distills lessons."""

import json
from typing import Optional, List
from alpha.core.types import ValidationType, ExecutionResult
from alpha.planner.schemas import ExecutionStep, ValidationContract
from alpha.reflection.schemas import ReflectionReport, RubricScore, FailurePattern, LessonLearned
from alpha.memory.manager import MemoryManager

class ReflectionEngine:
    """Evaluates task outputs against constraints, failure modes, and rubrics."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None, quality_threshold: float = 0.75):
        self.memory_manager = memory_manager
        self.quality_threshold = quality_threshold

    def reflect_on_step(
        self,
        step: ExecutionStep,
        result: ExecutionResult,
        raw_output: str
    ) -> ReflectionReport:
        """Analyze an execution output answering: What worked? What failed? What can improve?"""
        rubric_scores: List[RubricScore] = []
        failures: List[FailurePattern] = []
        what_worked: List[str] = []
        what_failed: List[str] = []
        what_can_improve: List[str] = []
        lessons: List[LessonLearned] = []

        # 1. Evaluate deterministic validation contracts
        contract_failures = self._check_contracts(step.validation_contracts, raw_output)

        # 2. Score Rubrics
        # Rubric 1: Format & Non-emptiness
        if not raw_output or not raw_output.strip():
            rubric_scores.append(RubricScore(criterion="non_emptiness", score=0.0, feedback="Output is empty"))
            failures.append(FailurePattern(
                category="empty_output",
                symptom="Zero non-whitespace characters produced",
                suspected_cause="Model hallucinated empty response or hit timeout"
            ))
            what_failed.append("Output was empty")
        else:
            rubric_scores.append(RubricScore(criterion="non_emptiness", score=1.0, feedback="Output populated"))
            what_worked.append("Model produced non-empty text")

        # Rubric 2: Contract Adherence
        if contract_failures:
            contract_score = max(0.0, 1.0 - (len(contract_failures) * 0.4))
            rubric_scores.append(RubricScore(
                criterion="contract_adherence",
                score=contract_score,
                feedback="; ".join(contract_failures)
            ))
            for cf in contract_failures:
                failures.append(FailurePattern(
                    category="contract_violation",
                    symptom=cf,
                    suspected_cause="Small model ignored formatting instruction or hallucinated structure"
                ))
                what_failed.append(cf)
        else:
            rubric_scores.append(RubricScore(criterion="contract_adherence", score=1.0, feedback="All contracts met"))
            what_worked.append("Satisfied all validation contracts")

        # Rubric 3: Conciseness & Noise Reduction (SLMs often add chatty preambles)
        chatter_prefixes = ["here is the", "sure,", "certainly!", "as an ai", "below is"]
        has_chatter = any(raw_output.strip().lower().startswith(p) for p in chatter_prefixes)
        if has_chatter:
            rubric_scores.append(RubricScore(criterion="conciseness", score=0.7, feedback="Contains conversational conversational boilerplate"))
            what_can_improve.append("Omit conversational preambles like 'Here is the...'")
        else:
            rubric_scores.append(RubricScore(criterion="conciseness", score=1.0, feedback="Clean direct output"))
            what_worked.append("Direct answer without conversational preamble")

        # Calculate overall score
        overall_score = sum(r.score for r in rubric_scores) / max(1, len(rubric_scores))
        passed = (overall_score >= self.quality_threshold) and (len(contract_failures) == 0)

        # Formulate corrective advice if failed
        corrective_prompt: Optional[str] = None
        if not passed:
            corrective_lines = ["PREVIOUS ATTEMPT FAILED THE FOLLOWING CHECKS:"]
            for f in what_failed:
                corrective_lines.append(f"- {f}")
            corrective_lines.append("CRITICAL: Comply strictly with the requirements above. Do not include markdown chatter.")
            corrective_prompt = "\n".join(corrective_lines)

            # Distill lesson
            lesson = LessonLearned(
                rule=f"Strictly format output for '{step.name}' avoiding: {', '.join(what_failed)}",
                trigger=f"task_type={step.name}",
                rationale="Small models fail when output formatting contracts are violated"
            )
            lessons.append(lesson)
            what_can_improve.append(f"Enforce strict template adherence: {lesson.rule}")
        else:
            what_can_improve.append("Maintain concise atomic execution format")

        report = ReflectionReport(
            task_id=step.task_id,
            step_number=step.step_number,
            overall_score=overall_score,
            passed=passed,
            what_worked=what_worked,
            what_failed=what_failed,
            what_can_improve=what_can_improve,
            rubric_scores=rubric_scores,
            failures=failures,
            lessons=lessons,
            corrective_prompt_injection=corrective_prompt
        )

        # Persist lessons to memory if memory_manager is wired
        if self.memory_manager:
            for l in lessons:
                self.memory_manager.store_lesson_learned(
                    rule=l.rule,
                    context_trigger=l.trigger,
                    rationale=l.rationale
                )
            if not passed:
                self.memory_manager.store_failure(
                    task_id=step.task_id,
                    description=step.name,
                    error_message="; ".join(what_failed),
                    root_cause=failures[0].suspected_cause if failures else None
                )

        return report

    def _check_contracts(self, contracts: List[ValidationContract], output: str) -> List[str]:
        """Validate output against specified validation contracts."""
        failures: List[str] = []
        for contract in contracts:
            if contract.validation_type == ValidationType.DETERMINISTIC_ASSERTION:
                if "len(output.strip()) > 0" in contract.rule and not output.strip():
                    failures.append(f"Failed assertion: {contract.description}")
            elif contract.validation_type == ValidationType.SCHEMA_MATCH:
                if "valid_json" in contract.rule:
                    try:
                        # Attempt to extract json if enclosed in code fences
                        clean_text = output.strip()
                        if clean_text.startswith("```"):
                            lines = clean_text.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].startswith("```"):
                                lines = lines[:-1]
                            clean_text = "\n".join(lines).strip()
                        json.loads(clean_text)
                    except Exception as e:
                        failures.append(f"JSON validation failed: {str(e)}")
            elif contract.validation_type == ValidationType.KEYWORD_PRESENCE:
                required_words = [w.strip() for w in contract.rule.split(",")]
                missing = [w for w in required_words if w.lower() not in output.lower()]
                if missing:
                    failures.append(f"Missing required keywords: {', '.join(missing)}")
        return failures
