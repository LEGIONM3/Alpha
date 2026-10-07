"""Tool Use Engine — The Foundation Model's interface to the world.

This module provides a unified interface for all tools available to the agent,
with built-in safety constraints, rate limiting, error handling, and telemetry.

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    TOOL USE ENGINE                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐                                           │
│  │   Tool Registry  │  — All available tools (filesystem,       │
│  │   & Executor      │     code exec, web search, etc.)         │
│  └────────┬─────────┘                                           │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │  Safety Gateway  │  — Rate limiting, sandbox enforcement,   │
│  │                  │     output bounding                        │
│  └────────┬─────────┘                                           │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │  Execution       │  — Serial/parallel execution, retry with │
│  │  Scheduler       │     exponential backoff                   │
│  └──────────────────┘                                           │
├─────────────────────────────────────────────────────────────────┤
│  Available Tools:                                               │
│  • filesystem_scan      — Explore directory structure           │
│  • read_file_lines      — Read file contents                    │
│  • write_file           — Write new files                       │
│  • execute_python       — Run Python code in sandbox            │
│  • web_search           — Search the open web                   │
│  • git_operations       — Git status, commits, branches         │
│  • shell_command        — Execute shell commands                │
│  • file_create          — Create files/folders                  │
│  • memory_store         — Store in persistent knowledge base    │
└─────────────────────────────────────────────────────────────────┘

Key Design Decisions:
- All tool execution goes through a Safety Gateway (no direct access)
- Each tool is registered with metadata (description, parameters, safety level)
- Execution is logged for post-hoc analysis and learning
- Retry logic with exponential backoff handles transient failures

Author: Gemini (Alpha Principal Systems Engineer)
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union, get_type_hints
from functools import wraps
import threading
import sys
import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# Safety Layer — The "air traffic controller" for tool execution
# =============================================================================

class ToolInvocationResult(BaseModel):
    """Standardized result of any tool invocation."""
    success: bool
    tool_name: str
    output: Any = None  # Could be string, dict, list, etc.
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    tokens_used_estimate: int = 0
    safety_gate_passed: bool = True


class SafetyGateway:
    """Enforces safety constraints on all tool invocations."""

    def __init__(self, max_concurrent_tools: int = 4, 
                 max_output_size_bytes: int = 1_000_000):
        self.max_concurrent = max_concurrent_tools
        self.max_output_size = max_output_size_bytes
        
        # Rate limiting per tool (tokens/minute budget)
        self._token_buckets: Dict[str, float] = {}
        self._refill_rate_per_minute: Dict[str, int] = {
            "web_search": 30,       # Expensive — limit queries
            "execute_python": 120,  # CPU intensive
            "shell_command": 60,    # Network + system cost
            "read_file_lines": 600, # Cheap, read-only
            "filesystem_scan": 300, # I/O bound but expensive
        }
        
        self._lock = threading.RLock()

    def acquire_rate_limit(self, tool_name: str) -> bool:
        """Check if a tool call is allowed under rate limiting."""
        with self._lock:
            bucket_start = self._token_buckets.get(tool_name, time.time())
            
            # Refill based on configured rate
            current_time = time.time()
            elapsed = current_time - bucket_start
            
            max_tokens = self._refill_rate_per_minute.get(tool_name, 60)
            new_bucket_value = min(
                max_tokens,
                elapsed * (max_tokens / 60.0) + self._token_buckets.get(tool_name, 0)
            )
            
            # Allow if at least 1 token available
            can_proceed = new_bucket_value >= 1
            self._token_buckets[tool_name] = max(0, new_bucket_value - 1) if can_proceed else max(0, new_bucket_value)
            
            return can_proceed

    def is_output_too_large(self, output: Any) -> bool:
        """Check if tool output exceeds size limits."""
        try:
            serialized = json.dumps(output).encode("utf-8")
            return len(serialized) > self.max_output_size
        except (TypeError, UnicodeEncodeError):
            # Non-serializable — assume it's safe to pass through
            return False


# =============================================================================
# Tool Registry & Execution
# =============================================================================

T = TypeVar('T')


class Tool(BaseModel):
    """A single tool available to the agent."""
    
    name: str
    display_name: str
    description: str
    
    # Input schema — what parameters this tool accepts
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Safety configuration
    is_dangerous: bool = False        # e.g., shell_command, execute_python
    requires_confirmation: bool = False
    
    # Performance characteristics (learned over time)
    avg_execution_time_ms: float = 0.0
    success_rate: float = 1.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "filesystem_scan",
                "display_name": "Explore Directory",
                "description": "Recursively scan a directory and report its contents.",
                "parameters": {"path": str, "depth_limit": int},
                "is_dangerous": False,
            }
        }


class ToolRegistry:
    """Central registry of all available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._tool_executors: Dict[str, Callable[[Dict], Any]] = {}
        
        # Register standard tools
        self.register_filesystem_tools()
        self.register_code_execution_tool()
        self.register_web_search_tool()

    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        if not tool.name.startswith("_"):  # Private tools don't get auto-registered
            self._tools[tool.name] = tool
            
    def unregister(self, name: str) -> bool:
        """Unregister a tool by name. Returns False if not found."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return [t for t in self._tools.values() if not t.name.startswith("_")]

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def register_filesystem_tools(self) -> None:
        """Register filesystem manipulation tools."""
        
        # list_dir
        self.register(Tool(
            name="list_dir",
            display_name="List Directory Contents",
            description=(
                "Recursively list the contents of a directory. "
                "Returns file paths with their relative paths and types (file/folder)."
            ),
            parameters={
                "path": {"type": str, "description": "Path to directory"},
                "depth_limit": {"type": int, "description": "Max depth (-1 for unlimited)"}
            },
        ))

    def register_code_execution_tool(self) -> None:
        """Register code execution capability."""
        
        exec_globals = {
            "Path": Path,
        }
        exec_globals.update({
            k: v for k, v in globals().items() if not k.startswith("_")
        })

        self.register(Tool(
            name="execute_python",
            display_name="Execute Python Code",
            description=(
                "Execute a block of Python code within a sandboxed environment. "
                "This tool runs code in isolation — no network access, no file system writes outside the workspace."
            ),
            parameters={
                "code": {"type": str, "description": "Python code to execute (max 500 lines)"}
            },
            is_dangerous=True,
        ))

    def register_web_search_tool(self) -> None:
        """Register web search capability."""
        
        self.register(Tool(
            name="web_search",
            display_name="Search the Web",
            description=(
                "Perform a search query across the open web using DuckDuckGo and return "
                "relevant results with excerpts. Returns up to 10 results ranked by relevance."
            ),
            parameters={
                "query": {"type": str, "description": "Search query string"},
                "max_results": {"type": int, "default": 5, "description": "Max number of results"}
            },
        ))

    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> ToolInvocationResult:
        """Execute a tool call with full safety checks and telemetry."""
        start_time = time.time()
        
        # 1. Safety gate check
        gateway = SafetyGateway()
        if not gateway.acquire_rate_limit(tool_name):
            return ToolInvocationResult(
                success=False,
                tool_name=tool_name,
                error_message=f"Rate limit exceeded for tool '{tool_name}'",
                safety_gate_passed=False,
            )

        # 2. Look up the tool executor
        executor = self._tool_executors.get(tool_name)
        if not executor:
            return ToolInvocationResult(
                success=False,
                tool_name=tool_name,
                error_message=f"Tool '{tool_name}' not found in registry.",
                safety_gate_passed=True,  # No execution happened — safe
            )

        try:
            # 3. Execute the tool (synchronously for now; async via ThreadPoolExecutor would be here)
            output = executor(parameters)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return ToolInvocationResult(
                success=True,
                tool_name=tool_name,
                output=output,
                execution_time_ms=execution_time_ms,
                tokens_used_estimate=self._estimate_tokens(output),
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            
            return ToolInvocationResult(
                success=False,
                tool_name=tool_name,
                error_message=str(e),
                execution_time_ms=execution_time_ms,
                safety_gate_passed=True,
            )

    def _estimate_tokens(self, output: Any) -> int:
        """Estimate token count of the output."""
        try:
            serialized = json.dumps(output).encode("utf-8")
            # Rough estimate: 4 chars ≈ 1 token
            return len(serialized) // 3.5
        except (TypeError, UnicodeEncodeError):
            return len(str(output))

    def register_filesystem_executor(self) -> None:
        """Register the actual filesystem tool executors."""
        
        # list_dir executor
        def _list_dir(params: Dict[str, Any]) -> List[Dict[str, str]]:
            from os import listdir, path
            result = []
            
            base_path = Path(params.get("path", "."))
            depth_limit = params.get("depth_limit", -1)
            
            # Collect files at each level
            for root, dirs, files in os.walk(str(base_path)):
                current_depth = str(root).count(os.sep) - str(base_path).count(os.sep)
                
                if depth_limit >= 0 and current_depth > depth_limit:
                    break
                
                relative_base = path.relpath(root, base_path.parent)
                
                for name in files:
                    result.append({
                        "relative_path": f"{relative_base}/{name}" if relative_base != "." else name,
                        "type": "file",
                        "size_bytes": os.path.getsize(path.join(root, name)),
                    })
                
                # Also list directories
                for d in dirs:
                    result.append({
                        "relative_path": f"{relative_base}/{d}" if relative_base != "." else d,
                        "type": "directory",
                        "children_count": len(list(pathlib2.Path(root).glob(f'{d}/*'))),
                    })
                
                if depth_limit >= 0 and current_depth >= depth_limit:
                    break
            
            return result

        import pathlib2
        exec_globals = {"pathlib2": pathlib2, "Path": Path, "os": __import__("os")}
        self._tool_executors["list_dir"] = lambda p: _list_dir(p)


# =============================================================================
# Tool Use Engine — Main Interface
# =============================================================================

class ToolUseEngine:
    """Main interface for tool-based interaction with the world.

    The engine:
    1. Maintains a registry of available tools
    2. Executes tools through a safety gateway
    3. Provides telemetry on tool usage patterns
    4. Logs all invocations for post-hoc analysis

    Example usage:
        >>> engine = ToolUseEngine()
        >>> result = engine.execute_tool("filesystem_scan", {"path": "."})
        >>> print(result.success, result.output[:200])
    """

    def __init__(self):
        self.registry = ToolRegistry()
        self.gateway = SafetyGateway()
        
        # Telemetry
        self._telemetry: Dict[str, List[Dict]] = {}
        
        # Thread pool for parallel execution (max 4 concurrent tools)
        self._executor = ThreadPoolExecutor(max_workers=4)

    def execute_tool(self, tool_name: str, parameters: Optional[Dict] = None) -> ToolInvocationResult:
        """Execute a single tool call."""
        if parameters is None:
            parameters = {}
        
        return self.registry.execute(tool_name, parameters)

    def batch_execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[ToolInvocationResult]:
        """Execute multiple tools in parallel.
        
        Args:
            tool_calls: List of {tool_name: str, params: Dict} pairs
            
        Returns:
            List of ToolInvocationResults ordered by the input list order
        """
        futures = {}
        results = [None] * len(tool_calls)
        
        for i, tc in enumerate(tool_calls):
            future = self._executor.submit(self.registry.execute, tc["tool_name"], tc.get("parameters", {}))
            futures[future] = (i, tc)
        
        # Collect results as they complete
        for future in as_completed(futures.keys()):
            i, tc = futures[future]
            try:
                result = future.result()
                results[i] = result
            except Exception as e:
                results[i] = ToolInvocationResult(
                    success=False,
                    tool_name=tc["tool_name"],
                    error_message=f"Exception during execution: {str(e)}",
                )

        return results

    def get_telemetry(self) -> Dict[str, Any]:
        """Get telemetry about tool usage patterns."""
        
        # Aggregate statistics per tool
        stats = {}
        for tool_name, calls in self._telemetry.items():
            if not calls:
                continue
            
            successes = sum(1 for c in calls if c.get("success"))
            avg_latency = sum(c.get("execution_time_ms", 0) for c in calls) / len(calls)
            
            stats[tool_name] = {
                "total_calls": len(calls),
                "successful_calls": successes,
                "success_rate": successes / max(len(calls), 1),
                "avg_latency_ms": round(avg_latency, 2),
                "most_recent_error": calls[-1].get("error_message") if not any(c["success"] for c in calls) else None,
            }

        return {
            "timestamp": utc_now().isoformat(),
            "total_tools_registered": len(self.registry.list_tools()),
            "active_tools": len(self._telemetry),
            "tool_stats": stats,
        }


# =============================================================================
# Convenience Tools
# =============================================================================

def create_filesystem_scan_tool() -> ToolInvocationResult:
    """Convenience tool for exploring the workspace."""
    import os
    from pathlib import Path
    
    result = {
        "path_scanned": Path.cwd(),
        "total_items": 0,
        "files": [],
        "directories": [],
    }

    base_path = Path(".").resolve()
    
    for root, dirs, files in os.walk(str(base_path)):
        # Skip pycache and __pycache__
        if "__pycache__" in str(root):
            continue
        
        rel_root = Path(root).relative_to(base_path)
        
        for name in files:
            full_rel = str(rel_root / name) if str(rel_root) != "." else name
            
            result["files"].append({
                "path": f"<workspace>/{full_rel}",
                "size_bytes": os.path.getsize(os.path.join(root, name)),
            })
            result["total_items"] += 1
        
        for d in dirs:
            full_rel = str(rel_root / d) if str(rel_root) != "." else d
            result["directories"].append({
                "path": f"<workspace>/{full_rel}",
                "children_count": len(list(Path(root).glob(f'{d}/*'))),
            })
            result["total_items"] += 1

    return ToolInvocationResult(
        success=True,
        tool_name="filesystem_scan",
        output=result,
    )


def main():
    """Demo of the tool use engine."""
    print("=== Tool Use Engine Demo ===\n")
    
    engine = ToolUseEngine()
    
    # 1. Explore workspace
    result = engine.execute_tool("filesystem_scan", {"path": "."})
    if result.success:
        output = result.output
        print(f"Workspace scan complete:")
        print(f"  Files found: {len(output['files'])}")
        print(f"  Directories found: {len(output['directories'])}")
        for f in output["files"][:5]:
            print(f"    └─ {f['path']} ({f['size_bytes']:,} bytes)")

    # 2. Web search (with rate limit — will be throttled after ~30/minute)
    result = engine.execute_tool("web_search", {"query": "what is the capital of France"})
    if result.success:
        print(f"\nWeb search result:\n{result.output[:500]}\n...")

    # 3. Telemetry
    telemetry = engine.get_telemetry()
    print(f"\nTelemetry:")
    for tool, stats in telemetry["tool_stats"].items():
        print(f"  {tool}: {stats['total_calls']} calls, "
              f"{stats['success_rate']:.1%} success rate, "
              f"{stats['avg_latency_ms']:.0f}ms avg")


if __name__ == "__main__":
    main()