"""Computer Use package: Laya Integration, Permissions, Tool Routing, and Contracts."""

from alpha.computer_use.permissions import (
    ComputerActionType,
    ApprovalToken,
    PermissionGate,
)
from alpha.computer_use.laya import (
    LayaComputerInterface,
    LayaObservationResult,
)
from alpha.computer_use.router import (
    CognitiveActionIntent,
    LayaToolRouter,
)
from alpha.computer_use.contracts import (
    LayaCapabilityType,
    LayaManifest,
    ILayaObservationTool,
    ILayaResearchTool,
    ILayaExecutionTool,
    LayaContractRegistry,
    laya_contract_registry,
)
from alpha.computer_use.computer_use_tool import (
    ComputerUseTool,
    computer_use_tool,
    ComputerUseResult,
)

from alpha.computer_use.closed_loop import (
    LayaClosedLoopRuntime,
    ComputerUseTask,
    ComputerUseTrajectory,
    ModelActionProposal,
    PostActionVerification,
    TrajectoryStepRecord,
)

__all__ = [
    "ComputerActionType",
    "ApprovalToken",
    "PermissionGate",
    "LayaComputerInterface",
    "LayaObservationResult",
    "CognitiveActionIntent",
    "LayaToolRouter",
    "LayaCapabilityType",
    "LayaManifest",
    "ILayaObservationTool",
    "ILayaResearchTool",
    "ILayaExecutionTool",
    "LayaContractRegistry",
    "laya_contract_registry",
    "ComputerUseTool",
    "computer_use_tool",
    "ComputerUseResult",
    "LayaClosedLoopRuntime",
    "ComputerUseTask",
    "ComputerUseTrajectory",
    "ModelActionProposal",
    "PostActionVerification",
    "TrajectoryStepRecord",
]
