"""Model Gateway: Unified managed resource entry point for foundation models."""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from alpha.model_intelligence.connector.client import (
    OpenAICompatibleClient,
    ChatCompletionResponse,
    EmbeddingResponse,
    ModelMessage,
)
from alpha.model_intelligence.connector.registry import (
    ModelRegistry,
    ModelMetadata,
    ModelConfiguration,
)


class GatewayTelemetry(BaseModel):
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        return round(self.total_latency_ms / max(1, self.total_calls), 2)


class ModelGateway:
    """Managed cognitive resource entry point for model interactions."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        default_model: Optional[str] = None,
        enable_mock_fallback: bool = True,
        client: Optional[OpenAICompatibleClient] = None,
        registry: Optional[ModelRegistry] = None
    ):
        self.registry = registry or ModelRegistry(endpoint_url=base_url)
        # Attempt live discovery
        discovered = self.registry.discover_live_models()
        chosen_model = default_model or (discovered[0] if discovered else "gemma-4-e4b-it-ultra-uncensored-heretic")

        self.client = client or OpenAICompatibleClient(
            base_url=base_url,
            default_model=chosen_model,
            enable_mock_fallback=enable_mock_fallback
        )
        self.active_model = chosen_model
        self.telemetry = GatewayTelemetry()

    def discover_and_register_active_models(self) -> List[ModelMetadata]:
        """Discovers active models via registry and returns all registered models."""
        self.registry.discover_live_models()
        return self.registry.list_models()

    def set_active_model(self, model_id: str) -> None:
        """Switch active foundation model."""
        self.active_model = model_id
        self.client.default_model = model_id

    def execute_chat(
        self,
        messages: List[Union[Dict[str, Any], ModelMessage]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> ChatCompletionResponse:
        """Execute chat completion with telemetry logging."""
        target_model = model or self.active_model
        config = self.registry.get_config(target_model)

        t_temp = temperature if temperature is not None else config.temperature
        t_max = max_tokens if max_tokens is not None else config.max_tokens

        self.telemetry.total_calls += 1
        t0 = time.perf_counter()
        try:
            resp = self.client.chat_completion(
                messages=messages,
                model=target_model,
                temperature=t_temp,
                max_tokens=t_max,
                tools=tools,
                response_format=response_format
            )
            self.telemetry.successful_calls += 1
            self.telemetry.total_prompt_tokens += resp.tokens_prompt
            self.telemetry.total_completion_tokens += resp.tokens_completion
            self.telemetry.total_latency_ms += resp.latency_ms
            return resp
        except Exception:
            self.telemetry.failed_calls += 1
            raise

    def chat_completion(
        self,
        messages: List[Union[Dict[str, Any], ModelMessage]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience method returning standard dict structure for cognitive engines."""
        resp = self.execute_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format
        )
        return {
            "choices": [{"message": {"content": resp.content, "tool_calls": resp.tool_calls}, "finish_reason": resp.finish_reason}],
            "model": resp.model,
            "latency_ms": resp.latency_ms
        }

    def execute_embeddings(self, texts: List[str], model: Optional[str] = None) -> EmbeddingResponse:
        return self.client.embeddings(texts=texts, model=model)

    def get_telemetry_summary(self) -> Dict[str, Any]:
        return {
            "active_model": self.active_model,
            "total_calls": self.telemetry.total_calls,
            "successful_calls": self.telemetry.successful_calls,
            "failed_calls": self.telemetry.failed_calls,
            "avg_latency_ms": self.telemetry.avg_latency_ms,
            "total_tokens": self.telemetry.total_prompt_tokens + self.telemetry.total_completion_tokens
        }
