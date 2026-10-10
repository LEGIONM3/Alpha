"""Qwen Strategic Reasoning Engine for Project Alpha Phase 9E.

The Foundation Model (Qwen 3.8 9B Heretic) is Alpha's sole strategic cognitive engine.
Zero heuristics. Zero static goal templates. Zero rule-based curiosity triggers.

Qwen owns:
- Curiosity
- Goal Formation
- Question Generation
- Hypothesis Formation
- Research Prioritization
- Strategic Evaluation
- Interpretation & Reflection on evidence
- Decision between competing explanations

Output strictly adheres to Phase 9 schema:
{
  "salient_observations": [],
  "unknowns": [],
  "contradictions": [],
  "opportunities": [],
  "candidate_questions": [],
  "candidate_hypotheses": [],
  "candidate_goals": [],
  "highest_value_goal": {},
  "reasoning_confidence": 0.0,
  "requested_evidence": []
}

Temperature policy:
- 1.0 for exploration/curiosity calls
- 0.1 - 0.2 for verification, schema repair, code execution planning, and belief adjudication.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import os
import re
import socket
import time
import urllib.request
import urllib.error
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, model_validator

from alpha.observation_engine.observation import Observation

logger = logging.getLogger("alpha.reasoning.qwen_reasoner")


class ModelInferenceError(RuntimeError):
    """Raised when the Foundation Model inference fails after all retries."""
    pass


class InferenceAuditRecord(BaseModel):
    """Runtime audit record for an authentic Foundation Model inference."""
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:10]}")
    response_id: str = Field(default_factory=lambda: f"resp_{uuid.uuid4().hex[:10]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_id: str
    endpoint: str
    temperature: float = 0.7
    max_tokens: int = 1000
    latency_ms: float = 0.0
    status: str = "SUCCESS"  # "SUCCESS", "FAILURE", "TIMEOUT"
    structured_validation_status: str = "RAW_TEXT"  # "VALID_JSON", "REPAIRED_JSON", "SCHEMA_VALIDATED", "PARSE_FAILED", "RAW_TEXT"
    decision_type: str = "GENERAL_REASONING"  # "STRATEGIC_COGNITION", "GOAL_SELECTION", "HYPOTHESIS_FORMULATION", "PRIORITIZATION", "NEXT_OBJECTIVE"
    decision_summary: str = ""
    rejection_or_retry_count: int = 0
    error: Optional[str] = None
    system_prompt_preview: str = ""
    user_prompt_preview: str = ""


class EvidenceBundle(BaseModel):
    """Collection of verifiable empirical observations."""
    bundle_id: str = Field(default_factory=lambda: f"bundle_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    observations: List[Any] = Field(default_factory=list)
    summary: str = ""

    def format_for_prompt(self, max_items: int = 15) -> str:
        items = self.observations[:max_items]
        lines = []
        for idx, obs in enumerate(items, start=1):
            src = getattr(obs, "source_uri", None) or getattr(obs, "source", "system")
            stype = getattr(obs, "source_type", "observation")
            conf = getattr(obs, "confidence", 1.0)
            ev = getattr(obs, "evidence", None)
            if ev is None:
                ev = getattr(obs, "raw_evidence", None) or getattr(obs, "normalized_summary", "")
            lines.append(f"{idx}. [{stype}|{src}] (Conf: {conf:.2f}): {ev}")
        return "\n".join(lines)


class StrategicInvestigation(BaseModel):
    topic: str = "Repository Investigation"
    target: str = ""
    question: str = "Investigate empirical status"
    epistemic_value: Any = "HIGH"
    epistemic_rationale: str = ""


class StrategicCognitionOutput(BaseModel):
    """The authoritative Phase 9 output produced by Qwen Strategic Reasoner."""
    salient_observations: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    candidate_questions: List[str] = Field(default_factory=list)
    candidate_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    candidate_goals: List[Dict[str, Any]] = Field(default_factory=list)
    highest_value_goal: Dict[str, Any] = Field(default_factory=dict)
    reasoning_confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    requested_evidence: List[str] = Field(default_factory=list)
    raw_response: str = ""

    # Compatibility properties for legacy callers
    @property
    def unusual(self) -> List[str]:
        return self.salient_observations

    @property
    def missing(self) -> List[str]:
        return self.unknowns

    @property
    def highest_epistemic_investigation(self) -> Optional[StrategicInvestigation]:
        if self.highest_value_goal:
            return StrategicInvestigation(
                topic=self.highest_value_goal.get("goal_statement", "Primary Goal"),
                target=self.highest_value_goal.get("target", ""),
                question=self.highest_value_goal.get("knowledge_gap", "Epistemic Inquiry"),
                epistemic_value="HIGHEST",
                epistemic_rationale=self.highest_value_goal.get("reason_for_selection", "")
            )
        elif self.candidate_questions:
            return StrategicInvestigation(
                topic="Epistemic Inquiry",
                target="",
                question=self.candidate_questions[0],
                epistemic_value="HIGHEST"
            )
        return None

    @property
    def next_investigations(self) -> List[StrategicInvestigation]:
        results = []
        for g in self.candidate_goals:
            results.append(
                StrategicInvestigation(
                    topic=g.get("goal_statement", "Goal"),
                    target=g.get("target", ""),
                    question=g.get("knowledge_gap", "Inquiry"),
                    epistemic_value="HIGH"
                )
            )
        return results


# Compatibility alias
StrategicReasoningResult = StrategicCognitionOutput


def resolve_default_model_endpoint() -> str:
    """Dynamically resolves OpenAI-compatible endpoint from environment or active local port (1234 / 1235)."""
    env_url = os.environ.get("ALPHA_MODEL_URL") or os.environ.get("LM_STUDIO_URL")
    if env_url:
        return env_url.rstrip("/")
    for port in (1234, 1235):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return f"http://127.0.0.1:{port}/v1"
        except Exception:
            pass
    return "http://127.0.0.1:1234/v1"


class QwenStrategicReasoner:
    """Authoritative strategic reasoning engine for Project Alpha."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        preferred_model: str = "qwen3.8-9b-heretic-uncensored",
        timeout: float = 90.0
    ):
        if endpoint_url is None:
            self.endpoint_url = resolve_default_model_endpoint()
        else:
            self.endpoint_url = endpoint_url.rstrip("/")
        self.preferred_model = preferred_model
        self.timeout = timeout
        self.active_model: Optional[str] = None
        self.audit_log: List[InferenceAuditRecord] = []
        self.audit_log_path = Path("data/model_inference_audit.jsonl")
        self._ensure_model_discovered()

    def record_inference_audit(self, record: InferenceAuditRecord) -> None:
        """Appends inference audit record to memory and persist to JSONL."""
        self.audit_log.append(record)
        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(record.model_dump_json() + "\n")
        except Exception as e:
            logger.warning(f"Could not persist inference audit record: {e}")

    def _ensure_model_discovered(self) -> str:
        if self.active_model:
            return self.active_model

        try:
            req = urllib.request.Request(f"{self.endpoint_url}/models")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                for m in models:
                    if "qwen" in m.lower():
                        self.active_model = m
                        return self.active_model
                if models:
                    self.active_model = models[0]
                    return self.active_model
                else:
                    self.active_model = self.preferred_model
        except Exception as e:
            # If default port 1234 failed with connection error, try alternate active port (1235)
            if ":1234" in self.endpoint_url:
                alt_url = self.endpoint_url.replace(":1234", ":1235")
                try:
                    req_alt = urllib.request.Request(f"{alt_url}/models")
                    with urllib.request.urlopen(req_alt, timeout=3.0) as resp_alt:
                        data = json.loads(resp_alt.read().decode("utf-8"))
                        self.endpoint_url = alt_url
                        models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                        for m in models:
                            if "qwen" in m.lower():
                                self.active_model = m
                                return self.active_model
                        if models:
                            self.active_model = models[0]
                            return self.active_model
                except Exception:
                    pass
            logger.warning(f"Could not connect to {self.endpoint_url}/models: {e}. Defaulting to {self.preferred_model}")
            self.active_model = self.preferred_model

        return self.active_model

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        decision_type: str = "GENERAL_REASONING"
    ) -> str:
        """Executes a chat completion call to Qwen with bounded exponential backoff retries and audit logging."""
        max_retries = 3
        backoff_base = 1.0
        last_exc: Optional[Exception] = None
        t0 = time.perf_counter()
        req_id = f"req_{uuid.uuid4().hex[:10]}"

        for attempt in range(1, max_retries + 1):
            model = self._ensure_model_discovered()
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
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
                    result = content.strip() if content.strip() else reasoning.strip()
                    if not result:
                        raise ValueError(f"Empty response received from Qwen at {self.endpoint_url}")

                    dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    audit_rec = InferenceAuditRecord(
                        request_id=req_id,
                        response_id=data.get("id") or f"resp_{uuid.uuid4().hex[:10]}",
                        model_id=model,
                        endpoint=self.endpoint_url,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        latency_ms=dt_ms,
                        status="SUCCESS",
                        structured_validation_status="RAW_TEXT",
                        decision_type=decision_type,
                        decision_summary=result[:120],
                        rejection_or_retry_count=attempt - 1,
                        system_prompt_preview=system_prompt[:120],
                        user_prompt_preview=user_prompt[:120]
                    )
                    self.record_inference_audit(audit_rec)
                    return result
            except Exception as exc:
                self.active_model = None
                last_exc = exc
                if attempt < max_retries:
                    wait_s = backoff_base * (2 ** (attempt - 1))
                    logger.warning(
                        f"Qwen inference attempt {attempt}/{max_retries} failed ({exc}); "
                        f"backing off for {wait_s:.1f}s before retry..."
                    )
                    time.sleep(wait_s)
                else:
                    dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    audit_rec = InferenceAuditRecord(
                        request_id=req_id,
                        response_id=f"resp_failed_{uuid.uuid4().hex[:8]}",
                        model_id=model if 'model' in locals() else self.preferred_model,
                        endpoint=self.endpoint_url,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        latency_ms=dt_ms,
                        status="FAILURE",
                        structured_validation_status="PARSE_FAILED",
                        decision_type=decision_type,
                        decision_summary="Inference failed after all retries",
                        rejection_or_retry_count=max_retries,
                        error=str(last_exc),
                        system_prompt_preview=system_prompt[:120],
                        user_prompt_preview=user_prompt[:120]
                    )
                    self.record_inference_audit(audit_rec)
                    logger.error(f"All {max_retries} attempts failed calling Qwen at {self.endpoint_url}: {exc}")
                    raise ModelInferenceError(
                        f"Qwen model inference failed at {self.endpoint_url} after {max_retries} attempts: {last_exc}"
                    ) from last_exc

    def generate_reasoning(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """General strategic reasoning interface calling Qwen directly."""
        sys_p = system_prompt or "You are the strategic cognition engine for Project Alpha (Qwen3.8-9B-Heretic)."
        return self._call_llm(system_prompt=sys_p, user_prompt=prompt, temperature=0.7)

    def _extract_json(self, raw_text: str) -> Any:
        """Robustly extracts and parses JSON with thinking tag removal and stack repair."""
        text = raw_text.strip()
        # 1. Strip <think> tags
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        # 2. Clean markdown fences
        cleaned = text.replace("```json", "").replace("```", "").strip()

        # 3. Direct parse
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # 4. Find starting delimiter
        start_brace = cleaned.find("{")
        start_bracket = cleaned.find("[")
        if start_brace != -1 and start_bracket != -1:
            start_idx = min(start_brace, start_bracket)
        elif start_brace != -1:
            start_idx = start_brace
        elif start_bracket != -1:
            start_idx = start_bracket
        else:
            raise ValueError(f"No JSON start delimiter found: {raw_text[:200]}")

        cleaned = cleaned[start_idx:]
        end_brace = cleaned.rfind("}")
        end_bracket = cleaned.rfind("]")
        end_idx = max(end_brace, end_bracket)
        if end_idx != -1:
            candidate = cleaned[:end_idx + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # 5. Backward progressive stack repair
        for cut in range(len(cleaned), 0, -1):
            sub = cleaned[:cut].rstrip()
            quote_count = sub.count('"') - sub.count(r'\"')
            if quote_count % 2 != 0:
                sub += '"'
            sub = sub.rstrip()
            if sub.endswith(':'):
                sub += ' ""'
            if sub.endswith(','):
                sub = sub[:-1].rstrip()

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
                return json.loads(repaired, strict=False)
            except Exception:
                continue

        raise ValueError(f"Failed to parse valid JSON from LLM: {raw_text[:200]}")

    def reason_over_evidence(
        self,
        bundle: Union[EvidenceBundle, List[Observation]],
        beliefs: Optional[List[Any]] = None,
        contradictions: Optional[List[str]] = None,
        knowledge_gaps: Optional[List[Any]] = None,
        world_state: Optional[Any] = None,
        active_goals: Optional[List[Any]] = None,
        tool_capabilities: Optional[List[str]] = None,
        temperature: float = 1.0
    ) -> StrategicCognitionOutput:
        """Primary Phase 9 Strategic Reasoning interface."""
        obs_list = bundle.observations if isinstance(bundle, EvidenceBundle) else bundle
        obs_formatted = "\n".join(
            f"{i+1}. [{o.source_type}|{o.source_uri}]: {o.normalized_summary or o.evidence}"
            for i, o in enumerate(obs_list[:12])
        ) or "No recent observations."

        beliefs_formatted = "\n".join(
            f"- [{getattr(b, 'belief_id', 'b')[:8]}] (Conf: {getattr(b, 'confidence', 0.5):.2f}): {getattr(b, 'statement', str(b))}"
            for b in (beliefs or [])[:6]
        ) or "No active beliefs in working memory."

        contra_formatted = "\n".join(f"! {c}" for c in (contradictions or [])[:4]) or "No active contradictions."
        gaps_formatted = "\n".join(f"? {getattr(g, 'topic', str(g))}" for g in (knowledge_gaps or [])[:4]) or "No explicit gaps cataloged."
        goals_formatted = "\n".join(f"* {getattr(g, 'goal_statement', str(g))}" for g in (active_goals or [])[:3]) or "No active goal set."

        system_prompt = (
            "You are the sole Strategic Cognitive Engine of Project Alpha. "
            "You reason strictly from verifiable reality. You possess genuine curiosity. "
            "Zero heuristics. You decide what deserves attention and inquiry. "
            "Respond ONLY with a valid JSON object matching the exact schema."
        )

        user_prompt = f"""EMPIRICAL OBSERVATIONS FROM REALITY:
{obs_formatted}

ACTIVE WORLD-MODEL BELIEFS:
{beliefs_formatted}

KNOWN CONTRADICTIONS:
{contra_formatted}

KNOWLEDGE GAPS & OPEN INQUIRIES:
{gaps_formatted}

ACTIVE GOALS:
{goals_formatted}

Evaluate reality and provide strategic cognition in this exact JSON schema:
{{
  "salient_observations": ["list of strings: what actually stands out in reality"],
  "unknowns": ["list of strings: what is missing or unexplained"],
  "contradictions": ["list of strings: what conflicts with expectations or prior beliefs"],
  "opportunities": ["list of strings: unexpected potential avenues for discovery"],
  "candidate_questions": ["list of strings: precise research questions"],
  "candidate_hypotheses": [
    {{
      "statement": "propositional claim",
      "mechanism": "underlying software or causal mechanism",
      "confidence": 0.5,
      "falsification_conditions": ["concrete disproof condition"],
      "verification_plan": "actionable test or tool step"
    }}
  ],
  "candidate_goals": [
    {{
      "goal_id": "goal_1",
      "goal_statement": "actionable research goal",
      "originating_observations": ["source uris"],
      "knowledge_gap": "what gap this resolves",
      "expected_information_gain": "high/medium/low",
      "reason_for_selection": "why this matters",
      "success_condition": "how success is verified",
      "termination_condition": "when to stop",
      "required_tools": ["search_code", "run_tests", "git_history"],
      "estimated_cost": 3,
      "confidence": 0.8
    }}
  ],
  "highest_value_goal": {{
    "goal_id": "goal_primary",
    "goal_statement": "the single highest-epistemic-value goal selected from candidates",
    "originating_observations": ["source uris"],
    "knowledge_gap": "gap statement",
    "expected_information_gain": "HIGH",
    "reason_for_selection": "epistemic rationale",
    "success_condition": "verification condition",
    "termination_condition": "termination condition",
    "required_tools": ["search_code", "run_tests"],
    "estimated_cost": 3,
    "confidence": 0.85
  }},
  "reasoning_confidence": 0.85,
  "requested_evidence": ["list of specific tool calls or sources needed next"]
}}

Respond ONLY with valid JSON."""

        raw_output = self._call_llm(
            system_prompt,
            user_prompt,
            temperature=temperature,
            max_tokens=1800,
            decision_type="STRATEGIC_COGNITION"
        )
        parsed = self._extract_json(raw_output)

        if not isinstance(parsed, dict):
            parsed = {}

        if self.audit_log:
            self.audit_log[-1].structured_validation_status = "SCHEMA_VALIDATED" if parsed else "PARSE_FAILED"
            h_goal = parsed.get("highest_value_goal", {})
            g_stmt = h_goal.get("goal_statement", "") if isinstance(h_goal, dict) else ""
            if g_stmt:
                self.audit_log[-1].decision_summary = f"Selected Goal: {g_stmt[:80]}"

        highest_goal = parsed.get("highest_value_goal") or {}
        candidate_goals = parsed.get("candidate_goals") or []
        if not highest_goal and candidate_goals:
            highest_goal = candidate_goals[0]

        return StrategicCognitionOutput(
            salient_observations=parsed.get("salient_observations", []),
            unknowns=parsed.get("unknowns", []),
            contradictions=parsed.get("contradictions", []),
            opportunities=parsed.get("opportunities", []),
            candidate_questions=parsed.get("candidate_questions", []),
            candidate_hypotheses=parsed.get("candidate_hypotheses", []),
            candidate_goals=candidate_goals,
            highest_value_goal=highest_goal,
            reasoning_confidence=float(parsed.get("reasoning_confidence", 0.85)),
            requested_evidence=parsed.get("requested_evidence", []),
            raw_response=raw_output
        )

    def plan_research_execution(
        self,
        goal: Dict[str, Any],
        available_tools: List[str],
        temperature: float = 0.2
    ) -> List[Dict[str, Any]]:
        """Qwen constructs an actionable sequence of tool invocations to investigate a goal.

        Lower temperature for planning precision.
        """
        system_prompt = (
            "You are the Research Planner for Project Alpha. "
            "Generate an executable sequence of tool invocations to acquire empirical evidence for the goal. "
            "Output ONLY a valid JSON array of tool execution steps."
        )

        user_prompt = f"""GOAL TO INVESTIGATE:
Statement: {goal.get('goal_statement', 'Investigate repository')}
Knowledge Gap: {goal.get('knowledge_gap', '')}
Success Condition: {goal.get('success_condition', '')}

AVAILABLE TOOLS:
{json.dumps(available_tools)}

Plan 2 to 4 concrete tool execution steps in order.
Each step must be a JSON object:
{{
  "step": 1,
  "tool": "name_of_tool",
  "arguments": {{"param": "value"}},
  "purpose": "why this tool call is necessary"
}}

Respond ONLY with valid JSON array."""

        try:
            raw_output = self._call_llm(system_prompt, user_prompt, temperature=temperature, max_tokens=2200)
            parsed = self._extract_json(raw_output)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "steps" in parsed:
                return parsed["steps"]
        except Exception as e:
            logger.warning(f"Research planning exception: {e}")

        return []

    def evaluate_belief_revision(
        self,
        beliefs: List[Any],
        findings: List[Any],
        observations: List[Observation],
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Qwen adjudicates evidence against active beliefs. Lower temperature for rigorous evaluation."""
        system_prompt = (
            "You are the Epistemic Adjudicator of Project Alpha. "
            "Evaluate active beliefs against new empirical evidence. "
            "Zero belief without evidence. "
            "Output ONLY a valid JSON object."
        )

        beliefs_text = "\n".join(
            f"- [{b.belief_id[:8]}] (Conf: {b.confidence:.2f}): {b.statement}"
            for b in beliefs[:6]
        ) or "No active beliefs."

        findings_text = "\n".join(
            f"- Finding: {getattr(f, 'finding_summary', str(f))} (Citations: {', '.join(getattr(f, 'citations', [])[:2])})"
            for f in findings[:5]
        ) or "No research findings."

        obs_text = "\n".join(
            f"- Obs [{o.source_type}|{o.source_uri}]: {o.normalized_summary or o.evidence}"
            for o in observations[:4]
        ) or "No raw observations."

        user_prompt = f"""ACTIVE BELIEFS:
{beliefs_text}

NEW EMPIRICAL RESEARCH FINDINGS:
{findings_text}

NEW OBSERVATIONS:
{obs_text}

Adjudicate evidence against beliefs:
1. contradicted_beliefs: list of {{"belief_id": str, "reason": str, "severity": float between 0.1 and 0.5}}
2. supported_beliefs: list of {{"belief_id": str, "reason": str, "strength": float between 0.05 and 0.3}}
3. new_beliefs: list of {{"statement": str, "confidence": float, "source_evidence": list of strings}} (ONLY for verified findings!)

Respond ONLY with valid JSON."""

        try:
            raw_output = self._call_llm(system_prompt, user_prompt, temperature=temperature, max_tokens=700)
            parsed = self._extract_json(raw_output)
            if isinstance(parsed, dict):
                return parsed
        except Exception as e:
            logger.warning(f"Belief revision Qwen evaluation exception: {e}")

        return {"contradicted_beliefs": [], "supported_beliefs": [], "new_beliefs": []}


# Singleton instance
qwen_reasoner = QwenStrategicReasoner()
