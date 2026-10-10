"""Laya Capability Provider Contracts for Project Alpha Phase Next.

In accordance with Phase Next Architectural Directives:
DO NOT fully integrate Laya yet.
Create formal capability contracts and interfaces.

Laya functions exclusively as:
1. Observation Tool (Sensory provider: screen capture, window tree, UI elements)
2. Research Tool (Browser navigation, DOM inspection, document retrieval)
3. Execution Tool (UI motor actions, desktop actions, terminal executions)

Sovereignty Invariant:
Alpha cognition remains sovereign and primary.
Laya remains strictly a capability provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid
from pydantic import BaseModel, Field

from alpha.observation_engine.observation import Observation
from alpha.computer_use.permissions import ApprovalToken, ComputerActionType

if TYPE_CHECKING:
    from alpha.research_engine.engine import ResearchFinding

logger = logging.getLogger("alpha.computer_use.contracts")


class LayaCapabilityType(str, Enum):
    OBSERVATION = "OBSERVATION"
    RESEARCH = "RESEARCH"
    EXECUTION = "EXECUTION"


class LayaManifest(BaseModel):
    provider_name: str = "Laya"
    version: str = "2.0.0"
    capability_type: LayaCapabilityType = LayaCapabilityType.OBSERVATION
    supported_actions: List[str] = Field(default_factory=list)
    requires_approval_token: bool = False
    cognitive_sovereignty_preserved: bool = True
    observation_capabilities: List[str] = Field(default_factory=lambda: ["SCREEN_GEOMETRY", "WINDOW_HIERARCHY", "DISPLAY_METRICS"])
    research_capabilities: List[str] = Field(default_factory=lambda: ["AST_INSPECTION", "DOM_SNAPSHOT", "WEB_NAVIGATION"])
    execution_capabilities: List[str] = Field(default_factory=lambda: ["FILE_EDIT", "COMMAND_EXECUTION", "UI_ACTION"])
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# 1. Observation Tool Contract
# =============================================================================
class ILayaObservationTool(ABC):
    """Sensory contract: Laya as an empirical observation provider."""

    @abstractmethod
    def capture_screen_observation(self, metadata: Optional[Dict[str, Any]] = None) -> Observation:
        """Captures host desktop display state and converts it into a verifiable Observation."""
        pass

    @abstractmethod
    def inspect_window_hierarchy(self) -> List[Observation]:
        """Inspects native desktop window handles and returns empirical observations."""
        pass

    def observe_display_geometry(self) -> Dict[str, Any]:
        """Observes host screen resolution and geometry."""
        return {"width": 1920, "height": 1080, "scale_factor": 1.0}

    @abstractmethod
    def get_observation_manifest(self) -> LayaManifest:
        """Returns provider declaration and sensory capabilities."""
        pass


class DefaultLayaObservationTool(ILayaObservationTool):
    """Default local provider for Laya observation contract."""

    def capture_screen_observation(self, metadata: Optional[Dict[str, Any]] = None) -> Observation:
        from alpha.observation_engine.laya_observer import LayaObservationObserver
        return LayaObservationObserver().observe()[0]

    def inspect_window_hierarchy(self) -> List[Observation]:
        from alpha.observation_engine.laya_observer import LayaObservationObserver
        return LayaObservationObserver().observe()

    def observe_display_geometry(self) -> Dict[str, Any]:
        from alpha.observation_engine.laya_observer import LayaObservationObserver
        obs = LayaObservationObserver().observe()
        if obs and isinstance(obs[0].evidence, dict):
            return obs[0].evidence.get("screen", {"width": 1920, "height": 1080})
        return {"width": 1920, "height": 1080}

    def get_observation_manifest(self) -> LayaManifest:
        return LayaManifest(capability_type=LayaCapabilityType.OBSERVATION)


# =============================================================================
# 2. Research Tool Contract
# =============================================================================
class ILayaResearchTool(ABC):
    """Research contract: Laya as an external web/document investigation tool."""

    @abstractmethod
    def execute_browser_research(
        self,
        query: str,
        target_urls: Optional[List[str]] = None,
        max_pages: int = 3
    ) -> ResearchFinding:
        """Navigates web/documentation sources and returns a citation-backed ResearchFinding."""
        pass

    @abstractmethod
    def extract_dom_snapshot(self, target_url: str) -> Dict[str, Any]:
        """Extracts structural DOM/accessibility snapshot for inspection."""
        pass

    @abstractmethod
    def get_research_manifest(self) -> LayaManifest:
        """Returns provider declaration and research capabilities."""
        pass


# =============================================================================
# 3. Execution Tool Contract
# =============================================================================
class ILayaExecutionTool(ABC):
    """Execution contract: Laya as a motor execution tool governed by PermissionGate."""

    @abstractmethod
    def execute_ui_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        approval_token: ApprovalToken
    ) -> Dict[str, Any]:
        """Executes a native UI motor action (click, type, drag) strictly requiring approval."""
        pass

    @abstractmethod
    def execute_terminal_action(
        self,
        command: str,
        approval_token: ApprovalToken,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Executes a host system command strictly requiring approval."""
        pass

    @abstractmethod
    def get_execution_manifest(self) -> LayaManifest:
        """Returns provider declaration and execution capabilities."""
        pass


# =============================================================================
# Laya Contract Registry & Validator
# =============================================================================
class LayaContractRegistry:
    """Coordinates and validates Laya capability contracts against Alpha cognition."""

    def __init__(self):
        self._default_obs = DefaultLayaObservationTool()
        self._observation_providers: Dict[str, ILayaObservationTool] = {"default": self._default_obs}
        self._research_providers: Dict[str, ILayaResearchTool] = {}
        self._execution_providers: Dict[str, ILayaExecutionTool] = {}

    def get_manifest(self) -> LayaManifest:
        """Returns standard Laya manifest declaration."""
        return LayaManifest(
            provider_name="Laya",
            version="2.0.0",
            capability_type=LayaCapabilityType.OBSERVATION,
            supported_actions=["SCREEN_GEOMETRY", "WINDOW_HIERARCHY", "AST_INSPECTION", "FILE_EDIT"]
        )

    def get_observation_tool(self, name: str = "default") -> ILayaObservationTool:
        """Returns registered or default observation provider."""
        return self._observation_providers.get(name, self._default_obs)

    def register_observation_tool(self, name: str, tool: ILayaObservationTool) -> None:
        if not isinstance(tool, ILayaObservationTool):
            raise TypeError(f"Provider {name} does not conform to ILayaObservationTool contract.")
        self._observation_providers[name] = tool
        logger.info(f"Registered Laya Observation Provider: {name}")

    def register_research_tool(self, name: str, tool: ILayaResearchTool) -> None:
        if not isinstance(tool, ILayaResearchTool):
            raise TypeError(f"Provider {name} does not conform to ILayaResearchTool contract.")
        self._research_providers[name] = tool
        logger.info(f"Registered Laya Research Provider: {name}")

    def register_execution_tool(self, name: str, tool: ILayaExecutionTool) -> None:
        if not isinstance(tool, ILayaExecutionTool):
            raise TypeError(f"Provider {name} does not conform to ILayaExecutionTool contract.")
        self._execution_providers[name] = tool
        logger.info(f"Registered Laya Execution Provider: {name}")

    def validate_provider_compliance(self, provider: Any, expected_capability: LayaCapabilityType) -> bool:
        """Validates formal interface compliance for a capability provider."""
        if expected_capability == LayaCapabilityType.OBSERVATION:
            return isinstance(provider, ILayaObservationTool) and hasattr(provider, "capture_screen_observation")
        elif expected_capability == LayaCapabilityType.RESEARCH:
            return isinstance(provider, ILayaResearchTool) and hasattr(provider, "execute_browser_research")
        elif expected_capability == LayaCapabilityType.EXECUTION:
            return isinstance(provider, ILayaExecutionTool) and hasattr(provider, "execute_ui_action")
        return False

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "observation_providers": list(self._observation_providers.keys()),
            "research_providers": list(self._research_providers.keys()),
            "execution_providers": list(self._execution_providers.keys())
        }


# Singleton contract registry
laya_contract_registry = LayaContractRegistry()
