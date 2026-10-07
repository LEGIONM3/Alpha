"""Universal Tool Interface protocol definitions and data structures for Alpha Phase 2."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
from pydantic import BaseModel, Field

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ToolPermission(str, Enum):
    """Fine-grained permission tiers for tool execution."""
    READ_FS = "read_fs"
    WRITE_FS = "write_fs"
    EXEC_CODE = "exec_code"
    NETWORK = "network"
    SYSTEM = "system"
    GIT = "git"
    API = "api"
    DATABASE = "database"
    ANALYTICS = "analytics"

class ToolCapability(str, Enum):
    """Categorical capabilities provided by tools."""
    SEARCH = "search"
    CODE_EXECUTION = "code_execution"
    FILESYSTEM = "filesystem"
    GIT = "git"
    BROWSER = "browser"
    API = "api"
    DATABASE = "database"
    VERIFICATION = "verification"
    ANALYTICS = "analytics"
    SYSTEM = "system"

class ToolParameter(BaseModel):
    """Schema descriptor for a single tool input argument."""
    name: str
    type: str  # "string", "integer", "float", "boolean", "dict", "list"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum_values: Optional[List[Any]] = None

class ValidationRule(BaseModel):
    """Declarative validation rule applied to tool inputs or outputs."""
    rule_type: str  # e.g., "regex", "range", "non_empty", "file_exists", "schema"
    target_field: str
    rule_parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: str

class ToolResult(BaseModel):
    """Standardized output structure for all tool invocations."""
    call_id: str
    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    cost_units: float = 0.0
    artifacts_produced: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=utc_now)

    def summary(self, max_length: int = 150) -> str:
        if not self.success:
            return f"Error: {self.error}"
        text = str(self.output)
        return (text[:max_length] + "...") if len(text) > max_length else text

class ToolMetadata(BaseModel):
    """Metadata describing tool capabilities, requirements, and profile."""
    name: str
    description: str
    capabilities: List[ToolCapability]
    permissions_required: List[ToolPermission]
    inputs: Dict[str, ToolParameter] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    validation_rules: List[ValidationRule] = Field(default_factory=list)
    version: str = "1.0.0"
    author: str = "Alpha System"
    estimated_latency_ms: float = 50.0
    estimated_cost_units: float = 0.1
    prerequisites: List[str] = Field(default_factory=list)
    is_reversible: bool = False

class BaseTool(ABC):
    """Universal Base Tool Interface.
    
    Every external interaction mechanism in Alpha must inherit from BaseTool
    and implement execute().
    """

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[ToolCapability],
        permissions: List[ToolPermission],
        parameters: Optional[Dict[str, ToolParameter]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[List[ValidationRule]] = None,
        is_reversible: bool = False
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.permissions = permissions
        self.parameters = parameters or {}
        self.output_schema = output_schema or {}
        self.validation_rules = validation_rules or []
        self.is_reversible = is_reversible
        self.enabled: bool = True
        self.disable_reason: Optional[str] = None

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Core tool implementation to be executed by the sandbox."""
        raise NotImplementedError

    def get_metadata(self) -> ToolMetadata:
        """Return standardized metadata descriptor."""
        return ToolMetadata(
            name=self.name,
            description=self.description,
            capabilities=self.capabilities,
            permissions_required=self.permissions,
            inputs=self.parameters,
            output_schema=self.output_schema,
            validation_rules=self.validation_rules,
            is_reversible=self.is_reversible
        )

    def validate_inputs(self, arguments: Dict[str, Any]) -> List[str]:
        """Validate input arguments against schema and declarative rules."""
        errors: List[str] = []
        for param_name, param_schema in self.parameters.items():
            if param_schema.required and param_name not in arguments:
                errors.append(f"Missing required parameter '{param_name}'")
            elif param_name in arguments:
                val = arguments[param_name]
                if param_schema.enum_values and val not in param_schema.enum_values:
                    errors.append(f"Parameter '{param_name}' value '{val}' not in allowed enum values: {param_schema.enum_values}")

        for rule in self.validation_rules:
            if rule.rule_type == "non_empty":
                val = arguments.get(rule.target_field)
                if val is None or (isinstance(val, (str, list, dict)) and len(val) == 0):
                    errors.append(rule.error_message)
        return errors

    def validate_output(self, result: ToolResult) -> List[str]:
        """Validate result output against declared validation rules."""
        errors: List[str] = []
        if not result.success:
            return errors
        for rule in self.validation_rules:
            if rule.rule_type == "output_non_empty":
                if result.output is None or (isinstance(result.output, (str, list, dict)) and len(result.output) == 0):
                    errors.append(rule.error_message)
        return errors
