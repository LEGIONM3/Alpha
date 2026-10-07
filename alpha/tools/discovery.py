"""Tool Discovery System: Metadata Store, Embeddings, and Capability Graph."""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from alpha.tools.protocol import (
    BaseTool,
    ToolCapability,
    ToolMetadata,
    ToolPermission
)
from alpha.tools.registry import ToolRegistry

class ToolSemanticVector:
    """Lightweight deterministic vector for tool semantic similarity."""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9_\s]", " ", text.lower())
        tokens = [t for t in cleaned.split() if len(t) > 1]
        # Add character bi-grams for robustness against morphological variations
        bigrams = []
        for t in tokens:
            if len(t) >= 4:
                bigrams.extend([t[i:i+3] for i in range(len(t)-2)])
        return tokens + bigrams

    @classmethod
    def compute_embedding(cls, text: str, dim: int = 128) -> List[float]:
        tokens = cls.tokenize(text)
        if not tokens:
            return [0.0] * dim
        vec = [0.0] * dim
        for tok in tokens:
            # Deterministic hash projection
            h = hash(tok)
            idx = abs(h) % dim
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    @classmethod
    def cosine_similarity(cls, vec_a: List[float], vec_b: List[float]) -> float:
        if len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        return max(0.0, min(1.0, dot))

class DiscoveredTool(BaseModel):
    """Ranked tool candidate discovered for an intent."""
    tool_name: str
    relevance_score: float
    description: str
    capabilities: List[str]
    why_use: str
    when_to_use: str
    prerequisites: List[str] = Field(default_factory=list)

class ToolMetadataStore:
    """Stores detailed operational rationale, examples, and when/why guidance for each tool."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def register_metadata(
        self,
        tool_name: str,
        why_it_exists: str,
        when_to_use: str,
        examples: List[str],
        alternatives: Optional[List[str]] = None
    ) -> None:
        self._store[tool_name] = {
            "tool_name": tool_name,
            "why_it_exists": why_it_exists,
            "when_to_use": when_to_use,
            "examples": examples,
            "alternatives": alternatives or []
        }

    def get_info(self, tool_name: str) -> Dict[str, Any]:
        return self._store.get(tool_name, {
            "tool_name": tool_name,
            "why_it_exists": "Provides standardized execution capability for Alpha OS.",
            "when_to_use": "When the task requires this specific operational primitive.",
            "examples": [],
            "alternatives": []
        })

class ToolCapabilityGraph:
    """Graph linking tools, capabilities, and functional relationships."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.metadata_store = ToolMetadataStore()
        self._capability_to_tools: Dict[ToolCapability, Set[str]] = {cap: set() for cap in ToolCapability}
        self._tool_embeddings: Dict[str, List[float]] = {}
        self.refresh()

    def refresh(self) -> None:
        """Re-index capabilities and compute semantic embeddings for registered tools."""
        for cap in ToolCapability:
            self._capability_to_tools[cap] = set()

        for meta in self.registry.list_tools(filter_enabled=False):
            for cap in meta.capabilities:
                self._capability_to_tools[cap].add(meta.name)

            # Rich semantic profile for tool embedding
            info = self.metadata_store.get_info(meta.name)
            cap_names = " ".join([c.value for c in meta.capabilities])
            param_names = " ".join(meta.inputs.keys())
            semantic_text = f"{meta.name} {meta.description} {cap_names} {param_names} {info['when_to_use']} {info['why_it_exists']}"
            self._tool_embeddings[meta.name] = ToolSemanticVector.compute_embedding(semantic_text)

    def get_tools_by_capability(self, capability: ToolCapability) -> List[BaseTool]:
        """Retrieve all active tools providing a specific capability."""
        tool_names = self._capability_to_tools.get(capability, set())
        tools: List[BaseTool] = []
        for name in tool_names:
            try:
                t = self.registry.get_tool(name)
                if t.enabled:
                    tools.append(t)
            except KeyError:
                continue
        return tools

    def discover_tools(self, intent: str, top_k: int = 3) -> List[DiscoveredTool]:
        """Discover and rank the best tools for a high-level intent or plan step."""
        intent_vec = ToolSemanticVector.compute_embedding(intent)
        ranked: List[Tuple[str, float]] = []

        for name, tool_vec in self._tool_embeddings.items():
            if not self.registry.has_tool(name):
                continue
            tool = self.registry.get_tool(name)
            if not tool.enabled:
                continue

            similarity = ToolSemanticVector.cosine_similarity(intent_vec, tool_vec)

            # Boost if intent keywords match capability name or lexical description
            intent_lower = intent.lower()
            for cap in tool.capabilities:
                if cap.value in intent_lower:
                    similarity = min(1.0, similarity + 0.25)

            tool_words = set(re.findall(r'\w+', f"{tool.name} {tool.description}".lower()))
            intent_words = set(re.findall(r'\w+', intent_lower))
            overlap = len(tool_words & intent_words)
            if overlap > 0:
                similarity = max(similarity, min(1.0, 0.3 + 0.1 * overlap))

            ranked.append((name, similarity))

        ranked.sort(key=lambda x: x[1], reverse=True)
        candidates = ranked[:top_k]

        results: List[DiscoveredTool] = []
        for name, score in candidates:
            tool = self.registry.get_tool(name)
            meta = tool.get_metadata()
            info = self.metadata_store.get_info(name)
            results.append(DiscoveredTool(
                tool_name=name,
                relevance_score=round(score, 4),
                description=meta.description,
                capabilities=[c.value for c in meta.capabilities],
                why_use=info["why_it_exists"],
                when_to_use=info["when_to_use"],
                prerequisites=meta.prerequisites
            ))
        return results

    def explain_tool(self, tool_name: str) -> Dict[str, Any]:
        """Explain what a tool does, why it exists, and when to use it."""
        tool = self.registry.get_tool(tool_name)
        meta = tool.get_metadata()
        info = self.metadata_store.get_info(tool_name)

        return {
            "name": tool.name,
            "description": tool.description,
            "capabilities": [c.value for c in tool.capabilities],
            "permissions": [p.value for p in tool.permissions],
            "why_it_exists": info["why_it_exists"],
            "when_to_use": info["when_to_use"],
            "examples": info["examples"],
            "alternatives": info["alternatives"],
            "inputs": {p: p_obj.model_dump() for p, p_obj in meta.inputs.items()},
            "is_reversible": tool.is_reversible
        }
