"""Model Registry: Model discovery, metadata, context limits, and configuration management.

Part 1: Model Connector
Tracks:
- Discovered models
- Context limits
- Tokenizer limits
- Model versions
- Model configurations
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator


class ModelConfiguration(BaseModel):
    temperature: float = 0.2
    top_p: float = 0.95
    max_tokens: int = 2048
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    stop_sequences: List[str] = Field(default_factory=list)


class ModelMetadata(BaseModel):
    model_id: str = ""
    family: str = "generic"  # gemma, llama, qwen, deepseek, gpt_oss, etc.
    context_window_tokens: int = 8192
    max_output_tokens: int = 2048
    tokenizer_type: str = "bpe"
    supports_tools: bool = True
    supports_json_schema: bool = True
    supports_embeddings: bool = False
    parameter_size: str = "medium"  # small, medium, large
    parameters_b: Optional[float] = 7.0
    capabilities: List[str] = Field(default_factory=list)
    quantization: str = "none"
    version: str = "1.0.0"
    is_active: bool = True
    discovered_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "name" in data and not data.get("model_id"):
                data["model_id"] = data["name"]
            if "context_window" in data and not data.get("context_window_tokens"):
                data["context_window_tokens"] = data["context_window"]
        return data

    @property
    def name(self) -> str:
        return self.model_id

    @property
    def context_window(self) -> int:
        return self.context_window_tokens


class ModelRegistry:
    """Manages available foundation models and their operational boundaries."""

    def __init__(self, endpoint_url: str = "http://localhost:1234/v1"):
        normalized_url = endpoint_url.rstrip("/")
        if "://localhost" in normalized_url:
            normalized_url = normalized_url.replace("://localhost", "://127.0.0.1")
        self.endpoint_url = normalized_url
        self._models: Dict[str, ModelMetadata] = {}
        self._default_configs: Dict[str, ModelConfiguration] = {}
        self._register_known_defaults()

    def _register_known_defaults(self) -> None:
        """Register built-in profiles for prominent open-source families."""
        defaults = [
            ModelMetadata(
                model_id="gemma-4-e4b-it-ultra-uncensored-heretic",
                family="gemma",
                context_window_tokens=8192,
                max_output_tokens=2048,
                supports_tools=True,
                supports_json_schema=True,
                parameter_size="small"
            ),
            ModelMetadata(
                model_id="text-embedding-nomic-embed-text-v1.5",
                family="nomic",
                context_window_tokens=2048,
                max_output_tokens=0,
                supports_embeddings=True,
                parameter_size="small"
            ),
            ModelMetadata(
                model_id="llama-3.3-70b-instruct",
                family="llama",
                context_window_tokens=131072,
                max_output_tokens=4096,
                supports_tools=True,
                supports_json_schema=True,
                parameter_size="large"
            ),
            ModelMetadata(
                model_id="qwen-2.5-coder-32b-instruct",
                family="qwen",
                context_window_tokens=32768,
                max_output_tokens=4096,
                supports_tools=True,
                supports_json_schema=True,
                parameter_size="medium"
            ),
            ModelMetadata(
                model_id="deepseek-r1-distill-qwen-14b",
                family="deepseek",
                context_window_tokens=65536,
                max_output_tokens=8192,
                supports_tools=True,
                supports_json_schema=True,
                parameter_size="medium"
            ),
            ModelMetadata(
                model_id="mock-weak-model",
                family="mock",
                context_window_tokens=4096,
                max_output_tokens=1024,
                supports_tools=True,
                supports_json_schema=True,
                parameter_size="tiny"
            )
        ]
        for m in defaults:
            self.register_model(m)

    def register_model(self, meta: ModelMetadata, config: Optional[ModelConfiguration] = None) -> ModelMetadata:
        self._models[meta.model_id] = meta
        self._default_configs[meta.model_id] = config or ModelConfiguration()
        return meta

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        return self._models.get(model_id)

    def list_models(self) -> List[ModelMetadata]:
        return list(self._models.values())

    def get_config(self, model_id: str) -> ModelConfiguration:
        return self._default_configs.get(model_id, ModelConfiguration())

    def discover_live_models(self) -> List[str]:
        """Query local/remote endpoint `/v1/models` and register any newly found models."""
        discovered_ids = []
        try:
            req = urllib.request.Request(f"{self.endpoint_url}/models", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("data", []):
                    mid = item.get("id")
                    if mid:
                        discovered_ids.append(mid)
                        if mid not in self._models:
                            # Infer family from model_id
                            fam = "generic"
                            mid_lower = mid.lower()
                            if "gemma" in mid_lower: fam = "gemma"
                            elif "llama" in mid_lower: fam = "llama"
                            elif "qwen" in mid_lower: fam = "qwen"
                            elif "deepseek" in mid_lower: fam = "deepseek"
                            elif "embed" in mid_lower: fam = "embedding"

                            is_embed = "embed" in mid_lower
                            self.register_model(ModelMetadata(
                                model_id=mid,
                                family=fam,
                                supports_embeddings=is_embed,
                                context_window_tokens=8192 if not is_embed else 2048
                            ))
        except Exception:
            pass
        return discovered_ids
