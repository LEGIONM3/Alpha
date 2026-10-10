"""Laya: Computer-Use Interface (Eyes & Hands).

Laya is NOT a brain.
Laya is:
- Eyes (Read, Observe, Inspect, Browse, Desktop Inspection)
- Hands (Navigate, Execute with permission approval, Computer Tasks)

Qwen remains: Mind.

Directly bridges Project Alpha to the production Computer-Use execution
infrastructure via the `COMPUTER_USE_ROOT` environment variable or an adjacent
`Computer-Use` workspace directory.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import psutil
from pydantic import BaseModel, Field

from alpha.computer_use.permissions import ComputerActionType, PermissionGate, ApprovalToken

logger = logging.getLogger("alpha.computer_use.laya")

# Default relative location of adjacent Computer-Use subsystem
DEFAULT_COMPUTER_USE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "Computer-Use"


def _resolve_computer_use_dir() -> Optional[Path]:
    """Resolves authentic Computer-Use package root."""
    env_path = os.environ.get("COMPUTER_USE_ROOT")
    if env_path and Path(env_path).exists():
        return Path(env_path).resolve()
    if DEFAULT_COMPUTER_USE_DIR.exists():
        return DEFAULT_COMPUTER_USE_DIR.resolve()
    return None


class LayaObservationResult(BaseModel):
    action: str
    target: str
    success: bool
    data: Any
    latency_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LayaComputerInterface:
    """The sensory and motor interface to the host operating system."""

    def __init__(self, workspace_root: Optional[Path] = None, computer_use_dir: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.permission_gate = PermissionGate()
        self.computer_use_dir = computer_use_dir or _resolve_computer_use_dir()

        # Connect Computer-Use runtime if present
        self._runtime_module = None
        self._browser_runtime_cls = None
        self._windows_runtime_cls = None
        self._orchestrator_cls = None
        self._laya_policy_cls = None
        self._init_computer_use_bridge()

    def _init_computer_use_bridge(self) -> None:
        """Dynamically imports the production Computer-Use package."""
        if not self.computer_use_dir or not self.computer_use_dir.exists():
            logger.info("Computer-Use package not detected at default location.")
            return

        cu_path_str = str(self.computer_use_dir)
        if cu_path_str not in sys.path:
            sys.path.insert(0, cu_path_str)

        try:
            import runtime
            self._runtime_module = runtime
            from runtime.browser.playwright_runtime import BrowserRuntime
            self._browser_runtime_cls = BrowserRuntime
            from runtime.desktop.windows_runtime import WindowsRuntime
            self._windows_runtime_cls = WindowsRuntime
            from runtime.orchestrator import AlphaOrchestrator
            self._orchestrator_cls = AlphaOrchestrator
            from runtime.policy import LayaPolicy
            self._laya_policy_cls = LayaPolicy
            logger.info(f"Connected Computer-Use runtime from {self.computer_use_dir}")
        except Exception as e:
            logger.warning(f"Could not load Computer-Use runtime modules: {e}")

    # =========================================================================
    # EYES (Read, Observe, Inspect, Browse, Desktop)
    # =========================================================================

    def read_file(self, file_path: str, max_bytes: int = 50_000) -> LayaObservationResult:
        """Reads file contents within safety bounds."""
        t0 = time.perf_counter()
        target = self.workspace_root / file_path
        if not target.exists():
            return LayaObservationResult(
                action="READ",
                target=file_path,
                success=False,
                data={"error": f"File {file_path} not found."},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        try:
            content = target.read_text(encoding="utf-8", errors="replace")[:max_bytes]
            return LayaObservationResult(
                action="READ",
                target=file_path,
                success=True,
                data={"content": content, "length_chars": len(content)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="READ",
                target=file_path,
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

    def observe_system_state(self) -> LayaObservationResult:
        """Observes active processes, memory, and host details."""
        t0 = time.perf_counter()
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        procs = len(psutil.pids())
        return LayaObservationResult(
            action="OBSERVE",
            target="system_state",
            success=True,
            data={
                "cpu_percent": cpu_pct,
                "memory_used_mb": round(mem.used / (1024 * 1024), 1),
                "memory_percent": mem.percent,
                "process_count": procs,
                "pid": os.getpid()
            },
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )

    def inspect_ast(self, python_file_path: str) -> LayaObservationResult:
        """Inspects Python AST symbols: classes, functions, docstrings."""
        t0 = time.perf_counter()
        target = self.workspace_root / python_file_path
        if not target.exists():
            return LayaObservationResult(
                action="INSPECT",
                target=python_file_path,
                success=False,
                data={"error": "File does not exist"},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        try:
            tree = ast.parse(target.read_text(encoding="utf-8", errors="replace"))
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            return LayaObservationResult(
                action="INSPECT",
                target=python_file_path,
                success=True,
                data={
                    "classes": classes,
                    "functions": funcs,
                    "total_classes": len(classes),
                    "total_functions": len(funcs)
                },
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="INSPECT",
                target=python_file_path,
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

    def get_runtime_capabilities(self) -> Dict[str, Any]:
        """Queries actual capabilities from the Computer-Use runtime."""
        if self._runtime_module and hasattr(self._runtime_module, "capabilities"):
            try:
                return self._runtime_module.capabilities()
            except Exception as e:
                return {"error": str(e), "available": False}
        return {"available": False, "reason": "Computer-Use package not loaded"}

    def observe_browser(self, url: str = "http://localhost:1234/v1/models", headless: bool = True) -> LayaObservationResult:
        """Observes browser DOM, accessibility tree, and candidate actions via Playwright."""
        t0 = time.perf_counter()
        if not self._browser_runtime_cls:
            return LayaObservationResult(
                action="BROWSE",
                target=url,
                success=False,
                data={"error": "BrowserRuntime not available from Computer-Use package"},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        rt = None
        try:
            rt = self._browser_runtime_cls(goal=f"Observe {url}", headless=headless)
            if url:
                rt.navigate(url)
            state = rt.observe_state()
            return LayaObservationResult(
                action="BROWSE",
                target=url,
                success=True,
                data={
                    "url": state.get("url", url),
                    "title": state.get("title", ""),
                    "n_elements": state.get("n_elements", 0),
                    "candidate_actions": state.get("candidate_actions", [])[:10],
                    "fingerprint": state.get("fingerprint", "")
                },
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="BROWSE",
                target=url,
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        finally:
            if rt:
                try:
                    rt.close()
                except Exception:
                    pass

    def observe_desktop(self, window_title: str = "") -> LayaObservationResult:
        """Observes Windows desktop top-level windows and UIA control trees."""
        t0 = time.perf_counter()
        if not self._windows_runtime_cls:
            return LayaObservationResult(
                action="DESKTOP_INSPECT",
                target=window_title,
                success=False,
                data={"error": "WindowsRuntime not available from Computer-Use package"},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        rt = None
        try:
            rt = self._windows_runtime_cls(goal="Observe desktop UI elements", window_title=window_title)
            wins = rt.list_windows()
            return LayaObservationResult(
                action="DESKTOP_INSPECT",
                target=window_title,
                success=True,
                data={
                    "total_windows": len(wins),
                    "windows": wins[:15]
                },
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="DESKTOP_INSPECT",
                target=window_title,
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        finally:
            if rt:
                try:
                    rt.close()
                except Exception:
                    pass

    def inspect_git_diff(self) -> LayaObservationResult:
        """Inspects uncommitted changes and repository status in workspace."""
        t0 = time.perf_counter()
        try:
            proc_status = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=5.0
            )
            proc_diff = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=5.0
            )
            return LayaObservationResult(
                action="INSPECT",
                target="git_diff",
                success=True,
                data={
                    "status_output": proc_status.stdout.strip(),
                    "diff_summary": proc_diff.stdout.strip()
                },
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="INSPECT",
                target="git_diff",
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

    def inspect_network_port(self, port: int, host: str = "127.0.0.1") -> LayaObservationResult:
        """Checks whether a local TCP port is reachable and listening."""
        t0 = time.perf_counter()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        try:
            res = sock.connect_ex((host, port))
            is_open = (res == 0)
            return LayaObservationResult(
                action="OBSERVE",
                target=f"{host}:{port}",
                success=True,
                data={"host": host, "port": port, "is_listening": is_open},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="OBSERVE",
                target=f"{host}:{port}",
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        finally:
            sock.close()

    def inspect_process_tree(self) -> LayaObservationResult:
        """Inspects child process tree and memory consumption of Alpha."""
        t0 = time.perf_counter()
        try:
            current_proc = psutil.Process(os.getpid())
            children = current_proc.children(recursive=True)
            child_info = []
            for c in children[:20]:
                try:
                    child_info.append({
                        "pid": c.pid,
                        "name": c.name(),
                        "status": c.status(),
                        "memory_mb": round(c.memory_info().rss / (1024 * 1024), 2)
                    })
                except Exception:
                    continue

            return LayaObservationResult(
                action="OBSERVE",
                target="process_tree",
                success=True,
                data={
                    "parent_pid": current_proc.pid,
                    "children_count": len(children),
                    "children": child_info
                },
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="OBSERVE",
                target="process_tree",
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

    # =========================================================================
    # HANDS (Navigate, Execute, Write, Computer Tasks)
    # =========================================================================

    def navigate_directory(self, dir_path: str) -> LayaObservationResult:
        """Navigates filesystem hierarchy safely."""
        t0 = time.perf_counter()
        target = (self.workspace_root / dir_path).resolve()
        if not target.exists() or not target.is_dir():
            return LayaObservationResult(
                action="NAVIGATE",
                target=dir_path,
                success=False,
                data={"error": f"Directory {dir_path} not found"},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        entries = [{"name": e.name, "is_dir": e.is_dir(), "size": e.stat().st_size if e.is_file() else 0}
                   for e in target.iterdir()][:50]
        return LayaObservationResult(
            action="NAVIGATE",
            target=dir_path,
            success=True,
            data={"entries": entries, "count": len(entries)},
            latency_ms=(time.perf_counter() - t0) * 1000.0
        )

    def execute_command(
        self,
        command: str,
        approval_token: Optional[ApprovalToken] = None,
        timeout: float = 10.0
    ) -> LayaObservationResult:
        """Executes a terminal command ONLY IF approved by PermissionGate."""
        t0 = time.perf_counter()
        permitted, reason = self.permission_gate.check_permission(
            ComputerActionType.EXECUTE,
            target=command,
            token=approval_token
        )
        if not permitted:
            return LayaObservationResult(
                action="EXECUTE",
                target=command,
                success=False,
                data={"error": "PERMISSION_DENIED", "reason": reason},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return LayaObservationResult(
                action="EXECUTE",
                target=command,
                success=(proc.returncode == 0),
                data={
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout.strip()[:500],
                    "stderr": proc.stderr.strip()[:500]
                },
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="EXECUTE",
                target=command,
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

    def write_file(
        self,
        file_path: str,
        content: str,
        approval_token: Optional[ApprovalToken] = None
    ) -> LayaObservationResult:
        """Writes to a file ONLY IF approved by PermissionGate."""
        t0 = time.perf_counter()
        permitted, reason = self.permission_gate.check_permission(
            ComputerActionType.WRITE,
            target=file_path,
            token=approval_token
        )
        if not permitted:
            return LayaObservationResult(
                action="WRITE",
                target=file_path,
                success=False,
                data={"error": "PERMISSION_DENIED", "reason": reason},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        try:
            target = self.workspace_root / file_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return LayaObservationResult(
                action="WRITE",
                target=file_path,
                success=True,
                data={"bytes_written": len(content.encode("utf-8"))},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="WRITE",
                target=file_path,
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

    def execute_computer_task(
        self,
        goal: str,
        start_url: str = "",
        max_steps: int = 5,
        approval_token: Optional[ApprovalToken] = None
    ) -> LayaObservationResult:
        """Executes a closed-loop computer-use subtask via AlphaOrchestrator ONLY IF approved."""
        t0 = time.perf_counter()
        permitted, reason = self.permission_gate.check_permission(
            ComputerActionType.COMPUTER_TASK,
            target=goal,
            token=approval_token
        )
        if not permitted:
            return LayaObservationResult(
                action="COMPUTER_TASK",
                target=goal,
                success=False,
                data={"error": "PERMISSION_DENIED", "reason": reason},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        if not self._orchestrator_cls or not self._browser_runtime_cls:
            return LayaObservationResult(
                action="COMPUTER_TASK",
                target=goal,
                success=False,
                data={"error": "AlphaOrchestrator or BrowserRuntime unavailable"},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )

        try:
            orchestrator = self._orchestrator_cls(
                runtime_factory=lambda g: self._browser_runtime_cls(g, headless=True),
                max_steps=max_steps
            )
            run_result = orchestrator.run(goal, start_url=start_url, max_steps=max_steps)
            return LayaObservationResult(
                action="COMPUTER_TASK",
                target=goal,
                success=run_result.success,
                data={
                    "outcome": run_result.outcome,
                    "steps": run_result.loop.steps if hasattr(run_result, "loop") else 0,
                    "plan": run_result.plan.to_dict() if hasattr(run_result, "plan") else {}
                },
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
        except Exception as e:
            return LayaObservationResult(
                action="COMPUTER_TASK",
                target=goal,
                success=False,
                data={"error": str(e)},
                latency_ms=(time.perf_counter() - t0) * 1000.0
            )
