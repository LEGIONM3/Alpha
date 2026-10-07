"""Project Alpha: Continuous Perception Layer (Phase 7C).

Ingests events across the entire cognitive operating system:
- Filesystem Changes
- Agent Messages
- Memory Updates
- World Model Updates
- Embedding Events
- Tool Outputs
- Runtime Errors
- Task Completions
- User Messages
- System Metrics
"""

from __future__ import annotations

import enum
import os
import queue
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class PerceptionEventType(str, enum.Enum):
    FILESYSTEM_CHANGE = "FILESYSTEM_CHANGE"
    AGENT_MESSAGE = "AGENT_MESSAGE"
    MEMORY_UPDATE = "MEMORY_UPDATE"
    WORLD_MODEL_UPDATE = "WORLD_MODEL_UPDATE"
    EMBEDDING_EVENT = "EMBEDDING_EVENT"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TASK_COMPLETION = "TASK_COMPLETION"
    USER_MESSAGE = "USER_MESSAGE"
    SYSTEM_METRIC = "SYSTEM_METRIC"
    COGNITIVE_THOUGHT = "COGNITIVE_THOUGHT"
    AWARENESS_UPDATE = "AWARENESS_UPDATE"


class PerceptionEvent(BaseModel):
    """An atomic perceptual observation event ingested by Alpha."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    event_type: PerceptionEventType
    source: str
    title: str
    data: Dict[str, Any] = Field(default_factory=dict)
    significance: float = 0.5  # 0.0 (trivial) to 1.0 (critical paradigm shift)

    @property
    def formatted_time(self) -> str:
        t = time.localtime(self.timestamp)
        millis = int((self.timestamp % 1) * 1000)
        return f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}.{millis:03d}"


class PerceptionBus:
    """Thread-safe event routing hub connecting all cognitive inputs to awareness."""

    def __init__(self, max_history: int = 1000, workspace_root: Optional[Path] = None):
        self._lock = threading.RLock()
        self._subscribers: Dict[Callable[[PerceptionEvent], None], Optional[Set[PerceptionEventType]]] = {}
        self._history: List[PerceptionEvent] = []
        self._max_history = max_history
        self._event_queue: queue.Queue[PerceptionEvent] = queue.Queue(maxsize=5000)
        self._workspace_root = workspace_root or Path.cwd()
        self._is_running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._fs_watch_thread: Optional[threading.Thread] = None
        self._last_fs_snapshot: Dict[str, float] = {}

    def start(self) -> None:
        """Start the background dispatch worker and filesystem monitor."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._worker_thread = threading.Thread(
                target=self._dispatch_loop,
                name="AlphaPerceptionBus-Dispatcher",
                daemon=True
            )
            self._worker_thread.start()

            self._fs_watch_thread = threading.Thread(
                target=self._filesystem_monitor_loop,
                name="AlphaPerceptionBus-FSWatcher",
                daemon=True
            )
            self._fs_watch_thread.start()

    def stop(self) -> None:
        """Stop background perception threads cleanly."""
        with self._lock:
            self._is_running = False

    def subscribe(
        self,
        handler: Callable[[PerceptionEvent], None],
        event_types: Optional[List[PerceptionEventType]] = None
    ) -> None:
        """Subscribe a callable to receive perception events."""
        with self._lock:
            allowed = set(event_types) if event_types else None
            self._subscribers[handler] = allowed

    def unsubscribe(self, handler: Callable[[PerceptionEvent], None]) -> None:
        """Remove a subscriber."""
        with self._lock:
            if handler in self._subscribers:
                del self._subscribers[handler]

    def publish(
        self,
        event_type: PerceptionEventType,
        source: str,
        title: str,
        data: Optional[Dict[str, Any]] = None,
        significance: float = 0.5
    ) -> PerceptionEvent:
        """Create and queue a perception event for non-blocking asynchronous dispatch."""
        event = PerceptionEvent(
            event_type=event_type,
            source=source,
            title=title,
            data=data or {},
            significance=significance
        )
        try:
            self._event_queue.put_nowait(event)
        except queue.Full:
            pass  # Drop if overwhelmed to prevent backpressure
        return event

    def _dispatch_loop(self) -> None:
        """Continuously pulls events from queue and distributes to subscribers."""
        while self._is_running:
            try:
                event = self._event_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            with self._lock:
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]
                subscribers_copy = list(self._subscribers.items())

            for handler, allowed_types in subscribers_copy:
                if allowed_types is None or event.event_type in allowed_types:
                    try:
                        handler(event)
                    except Exception:
                        pass

    def _filesystem_monitor_loop(self) -> None:
        """Polls key project directories for real-time filesystem events."""
        # Initial scan
        self._scan_filesystem(initial=True)
        while self._is_running:
            time.sleep(2.0)
            if not self._is_running:
                break
            self._scan_filesystem(initial=False)

    def _scan_filesystem(self, initial: bool = False) -> None:
        """Scans workspace files and emits events on modifications."""
        monitored_exts = {".py", ".md", ".json", ".jsonl"}
        ignore_dirs = {".git", ".pytest_cache", "__pycache__", ".vscode", "tmp"}
        try:
            current_snapshot: Dict[str, float] = {}
            for root, dirs, files in os.walk(self._workspace_root):
                # Filter dirs in-place
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    ext = os.path.splitext(file)[1]
                    if ext in monitored_exts:
                        p = os.path.join(root, file)
                        try:
                            mtime = os.path.getmtime(p)
                            rel_p = os.path.relpath(p, self._workspace_root)
                            current_snapshot[rel_p] = mtime
                        except OSError:
                            pass

            if not initial:
                # Detect modified or created files
                for rel_p, mtime in current_snapshot.items():
                    if rel_p not in self._last_fs_snapshot:
                        self.publish(
                            event_type=PerceptionEventType.FILESYSTEM_CHANGE,
                            source="filesystem_watcher",
                            title=f"File created: {rel_p}",
                            data={"path": rel_p, "action": "created"},
                            significance=0.6
                        )
                    elif mtime > self._last_fs_snapshot[rel_p]:
                        # Only publish if not internal temp or log file to avoid loops
                        if not rel_p.endswith(("_log.jsonl", "ACTIVE_COGNITIVE_STATE.json")):
                            self.publish(
                                event_type=PerceptionEventType.FILESYSTEM_CHANGE,
                                source="filesystem_watcher",
                                title=f"File modified: {rel_p}",
                                data={"path": rel_p, "action": "modified"},
                                significance=0.4
                            )

            self._last_fs_snapshot = current_snapshot
        except Exception:
            pass

    def get_recent_events(
        self,
        limit: int = 50,
        min_significance: float = 0.0,
        event_types: Optional[List[PerceptionEventType]] = None
    ) -> List[PerceptionEvent]:
        """Query recent perceptual history with filtering."""
        with self._lock:
            allowed = set(event_types) if event_types else None
            filtered = [
                e for e in self._history
                if e.significance >= min_significance and (allowed is None or e.event_type in allowed)
            ]
            return filtered[-limit:]
