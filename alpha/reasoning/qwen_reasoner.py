"""Qwen Strategic Reasoning Engine for Project Alpha.

The Foundation Model (Qwen 3.8 9B Heretic) is the sole strategic reasoning engine.
Zero heuristics. Zero scoring formulas. Zero hardcoded priorities.

Answers:
1. What appears unusual?
2. What is missing?
3. What contradicts expectations?
4. What should be investigated next?
5. Which investigation has highest epistemic value?

Also drives hypothesis generation and belief revision grounding.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import time
import urllib.request
import urllib.error
import uuid
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from alpha.observation_engine.observation import Observation

logger = logging.getLogger("alpha.reasoning.qwen_reasoner")


class EvidenceBundle(BaseModel):
    """A structured collection of verifiable empirical observations gathered during a cycle."""
    bundle_id: str = Field(default_factory=lambda: f"bundle_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    observations: List[Observation] = Field(default_factory=list)
    summary: str = ""

    def format_for_prompt(self, max_items: int = 15) -> str:
        """Formats observations into a clean, concise text representation for Qwen."""
        items = self.observations[:max_items]
        lines = []
        for idx, obs in enumerate(items, start=1):
            lines.append(f"{idx}. [{obs.source}] (Conf: {obs.confidence:.2f}): {obs.evidence}")
        return "\n".join(lines)


class StrategicInvestigation(BaseModel):
    """An inquiry selected by the foundation model for empirical investigation."""
    topic: str
    target: str = ""
    question: str
    epistemic_value: Any = "HIGH"
    epistemic_rationale: str = ""


class StrategicReasoningResult(BaseModel):
    """The 5-part strategic reasoning output produced by Qwen."""
    unusual: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    next_investigations: List[StrategicInvestigation] = Field(default_factory=list)
    highest_epistemic_investigation: Optional[StrategicInvestigation] = None
    hypothesis: Optional[Dict[str, Any]] = None
    raw_response: str = ""


class QwenStrategicReasoner:
    """Interfaces with Qwen at http://localhost:1234/v1 as Alpha's sole strategic reasoner."""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:1234/v1",
        preferred_model: str = "qwen3.8-9b-heretic-uncensored@q6_k",
        timeout: float = 60.0
    ):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.preferred_model = preferred_model
        self.timeout = timeout
        self.active_model: Optional[str] = None
        self._ensure_model_discovered()

    def _ensure_model_discovered(self) -> str:
        """Discovers or confirms loaded model at LM Studio endpoint."""
        if self.active_model:
            return self.active_model

        try:
            req = urllib.request.Request(f"{self.endpoint_url}/models")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                if self.preferred_model in models:
                    self.active_model = self.preferred_model
                elif models:
                    self.active_model = models[0]
                else:
                    self.active_model = self.preferred_model
        except Exception as e:
            logger.warning(f"Could not connect to {self.endpoint_url}/models: {e}. Defaulting to {self.preferred_model}")
            self.active_model = self.preferred_model

        return self.active_model

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 1200) -> str:
        """Executes a chat completion call to Qwen and extracts output text."""
        model = self._ensure_model_discovered()
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens
        }

        req = urllib.request.Request(
            f"{self.endpoint_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode("utf-8")
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""
                reasoning = msg.get("reasoning_content") or ""
                return content.strip() if content.strip() else reasoning.strip()
        except Exception as exc:
            logger.error(f"Error calling Qwen at {self.endpoint_url}: {exc}")
            raise

    def _extract_json(self, raw_text: str) -> Any:
        """Cleans code fences, strips thinking processes, and parses JSON robustly with progressive stack repair."""
        text = raw_text.strip()
        # 1. Strip <think> tags
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        # 2. Clean markdown code fences anywhere in string
        cleaned = text.replace("```json", "").replace("```", "").strip()

        # 3. Direct parse
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # 4. Find starting bracket or brace
        start_brace = cleaned.find("{")
        start_bracket = cleaned.find("[")

        start_idx = -1
        if start_brace != -1 and start_bracket != -1:
            start_idx = min(start_brace, start_bracket)
        elif start_brace != -1:
            start_idx = start_brace
        elif start_bracket != -1:
            start_idx = start_bracket
        else:
            raise ValueError(f"No JSON start delimiter found in LLM output: {raw_text[:200]}...")

        cleaned = cleaned[start_idx:]

        # 5. Try standard end delimiters first
        end_brace = cleaned.rfind("}")
        end_bracket = cleaned.rfind("]")
        end_idx = max(end_brace, end_bracket)
        if end_idx != -1:
            candidate = cleaned[:end_idx + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # 6. Progressive truncation repair (backwards scan from end)
        for cut in range(len(cleaned), max(0, len(cleaned) - 400), -1):
            sub = cleaned[:cut].rstrip()
            # Ensure odd quotes are closed
            quote_count = sub.count('"') - sub.count(r'\"')
            if quote_count % 2 != 0:
                sub += '"'

            # Trim dangling trailing punctuation
            sub = sub.rstrip()
            if sub.endswith(':'):
                sub += ' ""'
            if sub.endswith(','):
                sub = sub[:-1].rstrip()

            # Stack repair for unmatched braces/brackets
            in_str = False
            escape = False
            stack = []
            for ch in sub:
                if escape:
                    escape = False
                    continue
                if ch == '\\':
                    escape = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if not in_str:
                    if ch in ('{', '['):
                        stack.append('}' if ch == '{' else ']')
                    elif ch in ('}', ']') and stack:
                        if stack[-1] == ch:
                            stack.pop()

            repaired = sub + "".join(reversed(stack))
            try:
                return json.loads(repaired)
            except Exception:
                continue

        raise ValueError(f"Could not parse valid JSON from LLM output: {raw_text[:200]}...")

    def reason_over_evidence(self, bundle: EvidenceBundle) -> StrategicReasoningResult:
        """Sends EvidenceBundle to Qwen to answer the 5 mandatory strategic questions:

        1. What appears unusual?
        2. What is missing?
        3. What contradicts expectations?
        4. What should be investigated next?
        5. Which investigation has highest epistemic value?
        """
        system_prompt = (
            "You are the sole Strategic Reasoning Engine of Project Alpha. "
            "You reason strictly from verifiable empirical evidence. "
            "Do not simulate knowledge. Do not use hardcoded heuristics. "
            "Keep reasoning brief, direct, and concise. "
            "Output ONLY a valid JSON object matching the requested schema."
        )

        formatted_evidence = bundle.format_for_prompt(max_items=10)
        user_prompt = f"""EVIDENCE BUNDLE ({len(bundle.observations)} empirical observations):
{formatted_evidence}

Answer the following 5 strategic questions strictly from the evidence (keep each concise, max 1-2 items):
1. What appears unusual? (key: "unusual", list of strings)
2. What is missing? (key: "missing", list of strings)
3. What contradicts expectations? (key: "contradictions", list of strings)
4. What should be investigated next? (key: "next_investigations", list of objects with fields "topic", "target", "question", "epistemic_value")
5. Which investigation has highest epistemic value? (key: "highest_epistemic_investigation", object with fields "topic", "target", "question", "epistemic_rationale")

Respond ONLY with valid JSON."""

        raw_output = self._call_llm(system_prompt, user_prompt, max_tokens=1500)
        parsed = self._extract_json(raw_output)

        unusual = parsed.get("unusual", [])
        missing = parsed.get("missing", [])
        contradictions = parsed.get("contradictions", [])

        next_investigations: List[StrategicInvestigation] = []
        for inv in parsed.get("next_investigations", []):
            if isinstance(inv, dict):
                next_investigations.append(
                    StrategicInvestigation(
                        topic=inv.get("topic", "Repository Investigation"),
                        target=inv.get("target", ""),
                        question=inv.get("question", "Investigate empirical status"),
                        epistemic_value=inv.get("epistemic_value", "HIGH")
                    )
                )

        highest_inv_data = parsed.get("highest_epistemic_investigation")
        highest_inv: Optional[StrategicInvestigation] = None
        if isinstance(highest_inv_data, dict):
            highest_inv = StrategicInvestigation(
                topic=highest_inv_data.get("topic", "Primary Investigation"),
                target=highest_inv_data.get("target", ""),
                question=highest_inv_data.get("question", "Verify primary epistemic gap"),
                epistemic_value="HIGHEST",
                epistemic_rationale=highest_inv_data.get("epistemic_rationale", "")
            )
        elif next_investigations:
            highest_inv = next_investigations[0]
            highest_inv.epistemic_value = "HIGHEST"

        return StrategicReasoningResult(
            unusual=unusual if isinstance(unusual, list) else [str(unusual)],
            missing=missing if isinstance(missing, list) else [str(missing)],
            contradictions=contradictions if isinstance(contradictions, list) else [str(contradictions)],
            next_investigations=next_investigations,
            highest_epistemic_investigation=highest_inv,
            raw_response=raw_output
        )

    def generate_hypotheses_from_evidence(
        self,
        bundle: EvidenceBundle,
        findings: List[Any],
        reasoning: Optional[StrategicReasoningResult] = None
    ) -> List[Dict[str, Any]]:
        """Qwen generates falsifiable hypotheses with:

        - hypothesis statement
        - mechanism
        - confidence
        - evidence references
        - falsification conditions
        """
        system_prompt = (
            "You are the Strategic Hypothesis Generator of Project Alpha. "
            "You synthesize empirical observations and research findings into rigorous, "
            "falsifiable hypotheses. Keep reasoning brief, direct, and concise. "
            "Output ONLY a valid JSON array of hypothesis objects."
        )

        obs_text = bundle.format_for_prompt(max_items=6)
        findings_text = ""
        for idx, f in enumerate(findings[:4], start=1):
            f_summary = getattr(f, "finding_summary", str(f))
            f_cites = getattr(f, "citations", [])
            findings_text += f"\nFinding {idx}: {f_summary} (Citations: {', '.join(f_cites[:3])})"

        strategic_context = ""
        if reasoning and reasoning.highest_epistemic_investigation:
            inv = reasoning.highest_epistemic_investigation
            strategic_context = f"\nFocus Investigation: {inv.topic} -> {inv.question}"

        user_prompt = f"""EMPIRICAL EVIDENCE:
{obs_text}
{findings_text}
{strategic_context}

Generate 1 to 2 concise falsifiable hypotheses grounded in this evidence.
Each hypothesis must have:
- statement: clear propositional claim about repository structure, behavior, or architecture
- mechanism: underlying causal or software engineering mechanism
- confidence: prior probability from 0.05 to 0.95 assessed by your reasoning
- evidence_references: list of exact observation sources or citation references
- falsification_conditions: list of concrete empirical observations or test outputs that would disprove it
- verification_plan: specific actionable verification steps

Respond ONLY with a JSON array of hypothesis objects."""

        raw_output = self._call_llm(system_prompt, user_prompt, max_tokens=1500)
        parsed = self._extract_json(raw_output)

        if isinstance(parsed, dict) and "hypotheses" in parsed:
            parsed = parsed["hypotheses"]
        elif not isinstance(parsed, list):
            parsed = [parsed]

        return parsed

    def evaluate_belief_revision(
        self,
        beliefs: List[Any],
        findings: List[Any],
        observations: List[Observation]
    ) -> Dict[str, Any]:
        """Qwen analyzes active beliefs against empirical findings and observations.

        Determines:
        - which beliefs are contradicted and should be weakened
        - which beliefs are supported and should be strengthened
        - which findings represent novel verified knowledge to form new beliefs
        """
        system_prompt = (
            "You are the Epistemic Gatekeeper of Project Alpha. "
            "Evaluate active beliefs against new empirical evidence. "
            "No belief may exist or be formed without evidence. "
            "Keep reasoning brief, direct, and concise. "
            "Output ONLY a valid JSON object."
        )

        beliefs_text = "\n".join(
            f"- [{b.belief_id[:8]}] (Conf: {b.confidence:.2f}): {b.statement}"
            for b in beliefs[:6]
        )
        findings_text = "\n".join(
            f"- Finding: {f.finding_summary} (Citations: {', '.join(getattr(f, 'citations', [])[:2])})"
            for f in findings[:4]
        )
        obs_text = "\n".join(
            f"- Obs [{o.source}]: {o.evidence[:120]}"
            for o in observations[:4]
        )

        user_prompt = f"""ACTIVE BELIEFS:
{beliefs_text or "No active beliefs currently."}

NEW EMPIRICAL RESEARCH FINDINGS:
{findings_text or "No research findings in this cycle."}

NEW OBSERVATIONS:
{obs_text or "No raw observations."}

Determine (keep lists concise, max 1-2 items each):
1. contradicted_beliefs: list of objects {{"belief_id": str, "reason": str, "penalty": float between 0.1 and 0.5}}
2. supported_beliefs: list of objects {{"belief_id": str, "reason": str, "delta": float between 0.05 and 0.3}}
3. new_beliefs: list of objects {{"statement": str, "confidence": float, "source_evidence": list of strings}} (ONLY for verified empirical findings with real evidence!)

Respond ONLY with valid JSON."""

        try:
            raw_output = self._call_llm(system_prompt, user_prompt, max_tokens=1500)
            parsed = self._extract_json(raw_output)
            if isinstance(parsed, dict):
                return parsed
        except Exception as e:
            logger.warning(f"Belief revision Qwen evaluation exception: {e}")

        return {"contradicted_beliefs": [], "supported_beliefs": [], "new_beliefs": []}


# Singleton instance
qwen_reasoner = QwenStrategicReasoner()
