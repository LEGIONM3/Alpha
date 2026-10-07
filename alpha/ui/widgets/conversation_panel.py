"""Conversation & Interaction Panel for Alpha Terminal Cognitive Console (TCC).

Provides:
- User Message rendering
- Alpha Response rendering with full Rich Markdown and Syntax Highlighting
- Live Token Streaming support
- Command line input with history navigation
- Inline diagnostic blocks for /commands
"""

from __future__ import annotations

import time
from typing import List
from textual.app import ComposeResult
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widget import Widget
from textual.widgets import Input, Static, Markdown
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax


class ConversationPanel(Widget):
    """Left panel handling multi-turn conversation and developer command input."""

    DEFAULT_CSS = """
    ConversationPanel {
        width: 1fr;
        height: 1fr;
        background: #0d1117;
        border: solid #30363d;
        layout: vertical;
    }

    #convo-header {
        dock: top;
        height: 1;
        background: #161b22;
        color: #58a6ff;
        text-style: bold;
        padding: 0 1;
        border-bottom: solid #21262d;
    }

    #messages-scroll {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        padding: 1 1;
    }

    #input-container {
        dock: bottom;
        height: 3;
        background: #161b22;
        border-top: solid #30363d;
        padding: 0 1;
    }

    #user-input {
        width: 100%;
        background: #0d1117;
        color: #f0f6fc;
        border: solid #388bfd;
    }

    .user-msg-box {
        margin: 1 0 0 0;
        padding: 0 1;
        background: #1c2128;
        border-left: solid #58a6ff;
    }

    .alpha-msg-box {
        margin: 1 0 1 0;
        padding: 0 1;
        background: #0d1117;
        border-left: solid #2ea043;
    }

    .system-msg-box {
        margin: 1 0 1 0;
        padding: 0 1;
        background: #161b22;
        border-left: solid #d29922;
    }

    .streaming-cursor {
        color: #2ea043;
        text-style: blink;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.command_history: List[str] = []
        self.history_index: int = -1
        self.current_stream_widget: Static | None = None
        self.stream_buffer: str = ""

    def compose(self) -> ComposeResult:
        yield Static(" 💬 COGNITIVE CONVERSATION & COMMAND CONSOLE ", id="convo-header")
        with ScrollableContainer(id="messages-scroll"):
            # Initial Welcome Greeting
            welcome_text = (
                "**Project Alpha Cognitive Operating System v5.0.0-COGNITIVE**\n\n"
                "Connected to local foundation model at `http://localhost:1234/v1`.\n"
                "Type queries to observe real-time cognitive trace and reasoning.\n\n"
                "*Available developer commands:*\n"
                "`/help` `/status` `/model` `/identity` `/world` `/beliefs` `/goals` `/memory`\n"
                "`/research` `/agents` `/tools` `/governance` `/truth` `/embeddings` `/autonomous` `/reload` `/debug` `/exit`\n\n"
                "*Hotkeys:* `F12` Toggle Developer Mode | `Esc` Close Modals"
            )
            yield Static(Panel(welcome_text, title="ALPHA INITIALIZED", border_style="cyan"), classes="system-msg-box")

        with Container(id="input-container"):
            yield Input(
                placeholder="Enter prompt or command (e.g., 'Who are you?', /world, /autonomous)...",
                id="user-input"
            )

    def add_user_message(self, text: str) -> None:
        """Add user message card to scrollable conversation."""
        scroll = self.query_one("#messages-scroll", ScrollableContainer)
        t = time.strftime("%H:%M:%S")
        card = Static(
            Panel(
                Text(text, style="bold #f0f6fc"),
                title=f"👤 DEVELOPER [{t}]",
                border_style="#58a6ff"
            ),
            classes="user-msg-box"
        )
        scroll.mount(card)
        card.scroll_visible()

    def start_streaming_response(self) -> None:
        """Initialize a new streaming card for Alpha's response."""
        scroll = self.query_one("#messages-scroll", ScrollableContainer)
        t = time.strftime("%H:%M:%S")
        self.stream_buffer = ""
        self.current_stream_widget = Static(
            Panel(
                Text("Thinking...", style="italic dim green"),
                title=f"🧠 ALPHA [{t}] (STREAMING)",
                border_style="#2ea043"
            ),
            classes="alpha-msg-box"
        )
        scroll.mount(self.current_stream_widget)
        self.current_stream_widget.scroll_visible()

    def append_stream_token(self, token: str, is_reasoning: bool = False) -> None:
        """Append streamed token delta."""
        if not self.current_stream_widget:
            self.start_streaming_response()

        self.stream_buffer += token
        t = time.strftime("%H:%M:%S")

        # Format with rich markdown or text
        rendered_panel = Panel(
            Text(self.stream_buffer + " ▋", style="#c9d1d9"),
            title=f"🧠 ALPHA [{t}] (STREAMING)",
            border_style="#2ea043"
        )
        self.current_stream_widget.update(rendered_panel)
        self.current_stream_widget.scroll_visible()

    def finish_streaming_response(self, final_markdown: str) -> None:
        """Finalize streamed response with complete markdown formatting."""
        if self.current_stream_widget:
            t = time.strftime("%H:%M:%S")
            # Replace streaming panel with formatted Markdown widget
            scroll = self.query_one("#messages-scroll", ScrollableContainer)
            self.current_stream_widget.remove()
            self.current_stream_widget = None

            md_card = Static(
                Panel(
                    final_markdown,
                    title=f"🧠 ALPHA [{t}]",
                    border_style="#2ea043"
                ),
                classes="alpha-msg-box"
            )
            scroll.mount(md_card)
            md_card.scroll_visible()

    def add_system_card(self, title: str, content: str, style: str = "yellow") -> None:
        """Display a diagnostic card inside the conversation history."""
        scroll = self.query_one("#messages-scroll", ScrollableContainer)
        card = Static(
            Panel(content, title=title, border_style=style),
            classes="system-msg-box"
        )
        scroll.mount(card)
        card.scroll_visible()
