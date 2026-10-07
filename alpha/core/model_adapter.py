"""Model Adapter: Interfaces with low-reasoning foundation models with strict prompting and output sanitization."""

import json
import re
import time
from typing import Callable, Optional, Dict, Any
from alpha.core.types import ExecutionResult

class BaseLanguageModel:
    """Interface for foundation models."""
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class LocalEndpointModel(BaseLanguageModel):
    """OpenAI-compatible model connector for local foundation models (e.g. LM Studio, vLLM, Ollama)."""

    def __init__(
        self,
        endpoint_url: str = "http://localhost:1234/v1",
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
        fallback_to_mock: bool = True
    ):
        import urllib.parse
        self.endpoint_url = endpoint_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.fallback_to_mock = fallback_to_mock
        self._mock_fallback = MockWeakModel() if fallback_to_mock else None

        # Auto-discover loaded model if not specified
        if not self.model_name:
            self.model_name = self._discover_model() or "default"

    def _discover_model(self) -> Optional[str]:
        import urllib.request
        try:
            req = urllib.request.Request(f"{self.endpoint_url}/models")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("data", [])
                if models:
                    return models[0].get("id")
        except Exception:
            pass
        return None

    def generate(self, prompt: str) -> str:
        import urllib.request
        try:
            req_data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1024
            }
            req = urllib.request.Request(
                f"{self.endpoint_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(req_data).encode("utf-8")
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                reasoning = msg.get("reasoning_content") or ""
                return content if content.strip() else reasoning
        except Exception as exc:
            if self.fallback_to_mock and self._mock_fallback:
                return self._mock_fallback.generate(prompt)
            raise RuntimeError(f"LocalEndpointModel error connecting to {self.endpoint_url}: {str(exc)}")

OpenAICompatibleModel = LocalEndpointModel

class MockWeakModel(BaseLanguageModel):
    """Simulates a low-reasoning language model (SLM) for testing and demonstration.
    
    Can exhibit typical small-model behaviors:
    - Adds conversational filler ('Sure, here is...')
    - Fails complex multi-step reasoning without scaffolding
    - Corrects errors when given explicit corrective feedback
    """
    def __init__(self, failure_on_first_try: bool = False):
        self.failure_on_first_try = failure_on_first_try
        self.call_count: Dict[str, int] = {}

    def generate(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        key = prompt[:50]
        count = self.call_count.get(key, 0)
        self.call_count[key] = count + 1

        # Focus matching on immediate task instruction and corrective feedback
        instruction_part = prompt
        if "### IMMEDIATE TASK INSTRUCTION" in prompt:
            instruction_part = prompt.split("### IMMEDIATE TASK INSTRUCTION")[-1]
        instruction_lower = instruction_part.lower()

        # If reflection corrective prompt was injected, the weak model corrects itself!
        if "previous attempt failed" in prompt_lower or "critical: comply strictly" in prompt_lower:
            if "validation" in instruction_lower or "validate constraints" in instruction_lower:
                return "status: success\nresult: constraints fully verified"
            elif "extract parameters" in instruction_lower or "json" in instruction_lower:
                return '{"status": "success", "extracted_parameters": {"scope": "phase1", "target": "scaffolding"}}'
            return "status: success\nresult: task completed cleanly according to corrected constraints"

        # Simulate first attempt failure if enabled
        if self.failure_on_first_try and count == 0:
            if "json" in instruction_lower or "extract parameters" in instruction_lower:
                return "Sure! Here is the JSON you asked for: { status: 'incomplete', missing_quotes }"
            return "Here is my answer. I might have missed some constraints."

        # Standard responses for atomic steps based on the immediate instruction
        if "validate constraints" in instruction_lower or "validation_report" in instruction_lower or "validation" in instruction_lower:
            return "status: success\nresult: constraints fully verified"
        elif "extract parameters" in instruction_lower or "json_summary" in instruction_lower:
            return '{"status": "success", "extracted_parameters": {"target": "production", "budget_tokens": 1000}}'
        elif "generate core artifact" in instruction_lower or "core artifact" in instruction_lower:
            return "Artifact payload generated with complete specifications."
        else:
            return f"Processed atomic task successfully with direct result."


class ModelAdapter:
    """Enforces prompt scaffolding, context bounding, and output sanitization around any model."""

    def __init__(self, model: BaseLanguageModel):
        self.model = model

    def build_scaffolded_prompt(
        self,
        instruction: str,
        memory_context: Optional[str] = None,
        knowledge_context: Optional[str] = None,
        corrective_feedback: Optional[str] = None,
        expected_format: str = "text"
    ) -> str:
        """Assembles a tightly bounded prompt engineered for weak reasoning models."""
        parts = [
            "### ROLE & OBJECTIVE",
            "You are an atomic task executor. Focus strictly on the single immediate task below.",
            "Do NOT add greetings, conversational preambles, or speculative commentary."
        ]

        if knowledge_context and knowledge_context.strip():
            parts.append("\n### RELEVANT KNOWLEDGE")
            parts.append(knowledge_context.strip())

        if memory_context and memory_context.strip():
            parts.append("\n### WORKING MEMORY & LESSONS")
            parts.append(memory_context.strip())

        if corrective_feedback and corrective_feedback.strip():
            parts.append("\n### CORRECTION FROM PREVIOUS ATTEMPT")
            parts.append(corrective_feedback.strip())

        parts.append("\n### IMMEDIATE TASK INSTRUCTION")
        parts.append(instruction.strip())

        parts.append("\n### OUTPUT CONTRACT")
        if "json" in expected_format.lower():
            parts.append("Return ONLY a valid JSON object. No explanation, no markdown backticks.")
        else:
            parts.append("Return ONLY the direct result satisfying the instruction.")

        return "\n".join(parts)

    def execute_atomic_step(
        self,
        task_id: str,
        instruction: str,
        memory_context: Optional[str] = None,
        knowledge_context: Optional[str] = None,
        corrective_feedback: Optional[str] = None,
        expected_format: str = "text"
    ) -> ExecutionResult:
        """Executes a single atomic step through the model with latency and token estimation."""
        prompt = self.build_scaffolded_prompt(
            instruction=instruction,
            memory_context=memory_context,
            knowledge_context=knowledge_context,
            corrective_feedback=corrective_feedback,
            expected_format=expected_format
        )

        start_time = time.perf_counter()
        raw_output = self.model.generate(prompt)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Output sanitization & JSON extraction heuristics
        sanitized, parsed_data = self._sanitize_output(raw_output, expected_format)
        tokens_est = (len(prompt) + len(raw_output)) // 4

        return ExecutionResult(
            task_id=task_id,
            success=True,
            raw_output=sanitized,
            parsed_output=parsed_data,
            latency_ms=elapsed_ms,
            tokens_used_est=tokens_est
        )

    def _sanitize_output(self, raw: str, expected_format: str) -> tuple[str, Optional[Any]]:
        """Clean markdown fences, conversational headers, and extract structured JSON if needed."""
        text = raw.strip()

        # Remove markdown code fences if wrapped
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        parsed: Optional[Any] = None
        if "json" in expected_format.lower():
            # Try direct parse
            try:
                parsed = json.loads(text)
            except Exception:
                # Heuristic: search for JSON object {...}
                match = re.search(r"(\{.*\})", text, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group(1))
                        text = match.group(1)
                    except Exception:
                        pass

        return text, parsed
