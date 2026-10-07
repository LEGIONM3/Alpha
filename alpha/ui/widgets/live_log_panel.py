"""Live Logs & Telemetry Stream Widget for Alpha Terminal Cognitive Console (TCC).

Bottom panel displaying real-time cognitive activity:
- Errors & Warnings
- Research Activity & Discoveries
- Foundation Model Invocations
- Embedding Invocations
- Memory Ingestion & Queries
- World Model & State Mutations
- Governance Checks
"""

from __future__ import annotations

from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Static, RichLog, Button
from rich.text import Text

from alpha.ui.cognitive_bridge import LogEntry


class LiveLogPanel(Widget):
    """Bottom panel showing real-time formatted log and telemetry events."""

    DEFAULT_CSS = """
    LiveLogPanel {
        dock: bottom;
        height: 10;
        background: #090d13;
        border-top: solid #30363d;
        layout: vertical;
    }

    #log-header-bar {
        height: 1;
        background: #161b22;
        color: #79c0ff;
        padding: 0 1;
        border-bottom: solid #21262d;
    }

    #log-filters-bar {
        height: 2;
        background: #0d1117;
        padding: 0 1;
        align: left middle;
    }

    .log-filter-btn {
        margin: 0 1;
        height: 1;
        min-width: 7;
        background: #21262d;
        color: #c9d1d9;
        border: none;
    }

    .log-filter-btn:hover {
        background: #30363d;
    }

    .log-filter-active {
        background: #1f6feb;
        color: #ffffff;
        text-style: bold;
    }

    #log-stream {
        width: 100%;
        height: 1fr;
        background: #090d13;
        color: #c9d1d9;
        padding: 0 1;
    }
    """

    CATEGORIES = [
        ("ALL", "All Logs"),
        ("MODEL", "Model"),
        ("EMBEDDING", "Embeddings"),
        ("MEMORY", "Memory"),
        ("WORLD_MODEL", "World Model"),
        ("RESEARCH", "Research"),
        ("AGENT", "Agents"),
        ("GOVERNANCE", "Governance"),
        ("TRUTH", "Truth Layer"),
        ("ERROR", "Errors")
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.active_filter: str = "ALL"
        self._raw_entries: List[LogEntry] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="log-header-bar"):
            yield Static(" 📜 LIVE COGNITIVE TELEMETRY & AUDIT STREAM ")

        with Horizontal(id="log-filters-bar"):
            for cat_id, cat_label in self.CATEGORIES:
                btn_class = "log-filter-btn log-filter-active" if cat_id == "ALL" else "log-filter-btn"
                yield Button(cat_label, id=f"filter-{cat_id}", classes=btn_class)

        yield RichLog(id="log-stream", highlight=True, markup=True, wrap=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("filter-"):
            new_filter = btn_id.replace("filter-", "")
            self.set_filter(new_filter)

    def set_filter(self, category: str) -> None:
        self.active_filter = category
        # Update button classes
        for cat_id, _ in self.CATEGORIES:
            try:
                b = self.query_one(f"#filter-{cat_id}", Button)
                if cat_id == category:
                    b.set_classes("log-filter-btn log-filter-active")
                else:
                    b.set_classes("log-filter-btn")
            except Exception:
                pass

        # Re-render log stream
        try:
            stream = self.query_one("#log-stream", RichLog)
            stream.clear()
            for entry in self._raw_entries:
                if self._matches_filter(entry):
                    self._write_entry(stream, entry)
        except Exception:
            pass

    def add_log_entry(self, entry: LogEntry) -> None:
        """Receive and conditionally render a new log entry."""
        self._raw_entries.append(entry)
        if len(self._raw_entries) > 2000:
            self._raw_entries.pop(0)

        if self._matches_filter(entry):
            try:
                stream = self.query_one("#log-stream", RichLog)
                self._write_entry(stream, entry)
            except Exception:
                pass

    def _matches_filter(self, entry: LogEntry) -> bool:
        if self.active_filter == "ALL":
            return True
        if self.active_filter == "ERROR":
            return entry.level in ("ERROR", "WARN")
        return entry.category == self.active_filter

    def _write_entry(self, stream: RichLog, entry: LogEntry) -> None:
        line = Text()
        line.append(f"[{entry.formatted_time}] ", style="dim")

        # Category Badge
        cat_styles = {
            "MODEL": "bold black on #58a6ff",
            "EMBEDDING": "bold black on #39c5bb",
            "MEMORY": "bold black on #bc8cff",
            "WORLD_MODEL": "bold black on #f0883e",
            "RESEARCH": "bold black on #e3b341",
            "AGENT": "bold black on #d2a8ff",
            "GOVERNANCE": "bold black on #388bfd",
            "TRUTH": "bold black on #7ee787",
            "TOOL": "bold black on #56d364",
            "ERROR": "bold white on #f85149",
            "SYSTEM": "bold black on #8b949e"
        }
        badge_style = cat_styles.get(entry.category, "bold black on #8b949e")
        line.append(f" {entry.category} ", style=badge_style)
        line.append(" ")

        # Level
        level_styles = {
            "INFO": "green",
            "WARN": "bold yellow",
            "ERROR": "bold red",
            "DEBUG": "dim cyan"
        }
        line.append(f"[{entry.level}] ", style=level_styles.get(entry.level, "white"))

        # Message
        line.append(entry.message, style="white")

        stream.write(line)
