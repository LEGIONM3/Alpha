"""Shared Context Layer: Blackboard pattern, versioned state, and event notifications."""

import threading
import time
from typing import Any, Dict, List, Optional, Callable

class SharedContextLayer:
    """Thread-safe blackboard state shared across cognitive agents."""

    def __init__(self, context_id: str = "global"):
        self.context_id = context_id
        self._state: Dict[str, Any] = {}
        self._versions: Dict[str, int] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._listeners: Dict[str, List[Callable[[str, Any, int], None]]] = {}
        self._lock = threading.RLock()

    def set(self, key: str, value: Any, author_id: str = "system") -> int:
        """Store a value with version increment and notify listeners."""
        with self._lock:
            version = self._versions.get(key, 0) + 1
            self._state[key] = value
            self._versions[key] = version
            
            entry = {
                "key": key,
                "value": value,
                "version": version,
                "author_id": author_id,
                "timestamp": time.time()
            }
            if key not in self._history:
                self._history[key] = []
            self._history[key].append(entry)

            # Notify listeners for this specific key and wildcard '*'
            callbacks = list(self._listeners.get(key, [])) + list(self._listeners.get("*", []))
            for cb in callbacks:
                try:
                    cb(key, value, version)
                except Exception:
                    pass

            return version

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve latest value for a key."""
        with self._lock:
            return self._state.get(key, default)

    def get_version(self, key: str) -> int:
        """Retrieve current revision number for a key."""
        with self._lock:
            return self._versions.get(key, 0)

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow copy of the entire shared state dictionary."""
        with self._lock:
            return dict(self._state)

    def subscribe(self, key: str, callback: Callable[[str, Any, int], None]) -> None:
        """Subscribe a callback to changes for key or '*'."""
        with self._lock:
            if key not in self._listeners:
                self._listeners[key] = []
            self._listeners[key].append(callback)

    def get_history(self, key: str) -> List[Dict[str, Any]]:
        """Retrieve audit log of revisions for key."""
        with self._lock:
            return list(self._history.get(key, []))

    def create_child_context(self, sub_context_id: str) -> "SharedContextLayer":
        """Fork child context pre-populated with parent snapshot."""
        child = SharedContextLayer(context_id=f"{self.context_id}:{sub_context_id}")
        with self._lock:
            for k, v in self._state.items():
                child.set(k, v, author_id="inherited")
        return child
