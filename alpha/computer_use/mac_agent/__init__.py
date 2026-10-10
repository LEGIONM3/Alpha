"""Apple Silicon macOS Computer-Use Agent Package for Project Alpha.

Separates:
- Platform & TCC Permission Probe (platform_probe.py)
- Versioned API & Action Schemas (schemas.py)
- Deny-by-Default Policy, Budgets, Redaction & Untrusted Content Guard (policy.py)
- Isolated Playwright Chromium Browser Executor (browser_executor.py)
- Native macOS Accessibility & Quartz Actuator (native_executor.py)
- Independent Outcome Verifier (verifier.py)
- Private Authenticated HTTP Service (server.py)
- Legion-to-Mac Client & Laya Contract Adapter (client.py)
"""

from alpha.computer_use.mac_agent.platform_probe import (
    MacPermissionStatus,
    MacPlatformProbe,
    MacPlatformReport,
)
from alpha.computer_use.mac_agent.schemas import (
    API_VERSION,
    CancelTaskRequest,
    CapabilitiesResponse,
    EmergencyStopRequest,
    ExecuteActionRequest,
    ExecuteActionResponse,
    HealthResponse,
    LocatorStrategy,
    MacActionType,
    MacModality,
    MacObservationPayload,
    ObservedUIElement,
    ObserveRequest,
    ObserveResponse,
    OutcomeVerificationDetail,
    SemanticLocator,
    TaskStatusResponse,
    VerificationStatus,
    VerifyOutcomeRequest,
    VerifyOutcomeResponse,
)
from alpha.computer_use.mac_agent.policy import (
    DEFAULT_APPROVED_APPLICATIONS,
    DEFAULT_APPROVED_URL_PREFIXES,
    FORBIDDEN_APPLICATIONS,
    MacAgentPolicy,
    TaskBudgetState,
    is_private_bind_address,
    redact_sensitive_data,
    redact_sensitive_text,
    wrap_untrusted_environment_content,
)
from alpha.computer_use.mac_agent.browser_executor import MacBrowserExecutor
from alpha.computer_use.mac_agent.native_executor import MacNativeExecutor
from alpha.computer_use.mac_agent.verifier import MacOutcomeVerifier
from alpha.computer_use.mac_agent.server import (
    MacAgentHTTPServer,
    MacAgentServiceCore,
)
from alpha.computer_use.mac_agent.client import (
    MacAgentClientError,
    MacComputerUseClient,
)

__all__ = [
    "API_VERSION",
    "MacPermissionStatus",
    "MacPlatformProbe",
    "MacPlatformReport",
    "CancelTaskRequest",
    "CapabilitiesResponse",
    "EmergencyStopRequest",
    "ExecuteActionRequest",
    "ExecuteActionResponse",
    "HealthResponse",
    "LocatorStrategy",
    "MacActionType",
    "MacModality",
    "MacObservationPayload",
    "ObservedUIElement",
    "ObserveRequest",
    "ObserveResponse",
    "OutcomeVerificationDetail",
    "SemanticLocator",
    "TaskStatusResponse",
    "VerificationStatus",
    "VerifyOutcomeRequest",
    "VerifyOutcomeResponse",
    "DEFAULT_APPROVED_APPLICATIONS",
    "DEFAULT_APPROVED_URL_PREFIXES",
    "FORBIDDEN_APPLICATIONS",
    "MacAgentPolicy",
    "TaskBudgetState",
    "is_private_bind_address",
    "redact_sensitive_data",
    "redact_sensitive_text",
    "wrap_untrusted_environment_content",
    "MacBrowserExecutor",
    "MacNativeExecutor",
    "MacOutcomeVerifier",
    "MacAgentHTTPServer",
    "MacAgentServiceCore",
    "MacAgentClientError",
    "MacComputerUseClient",
]
