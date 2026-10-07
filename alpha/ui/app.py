"""Main Textual Application for Alpha Terminal Cognitive Console (TCC).

Multi-pane layout:
--------------------------------------------------
TOP BAR (Alpha Status | Model | Memory | World | Gov | Emb | Res | Agt | CPU | RAM | GPU | Uptime)
--------------------------------------------------
LEFT PANEL (Conversation)       | RIGHT PANEL (Cognitive Trace)
User messages                   | Reasoning Pipeline
Alpha responses                 | Retrieved Memories
Streaming support               | World Model Queries
Markdown & Syntax highlight     | Developer Mode (F12)
--------------------------------------------------
BOTTOM PANEL (Live Logs: Errors, Model, Emb, Mem, World, Research, Agents)
--------------------------------------------------
"""

from __future__ import annotations

import asyncio
import logging
import queue
import threading
import time
from typing import Optional, Callable, Any
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input

from alpha.ui.cognitive_bridge import CognitiveBridge, LogEntry, CognitiveTrace
from alpha.ui.widgets.top_bar import TopBarWidget
from alpha.ui.widgets.conversation_panel import ConversationPanel
from alpha.ui.widgets.cognitive_trace_panel import CognitiveTracePanel
from alpha.ui.widgets.live_log_panel import LiveLogPanel
from alpha.ui.screens.inspection_modal import SubsystemInspectionScreen

logger = logging.getLogger("alpha.ui.app")


class AlphaConsoleApp(App):
    """Alpha Terminal Cognitive Console (TCC) Textual Application."""

    TITLE = "Alpha Terminal Cognitive Console"
    SUB_TITLE = "Development & Epistemic Verification Interface"

    CSS = """
    Screen {
        background: #090d13;
        layout: vertical;
    }

    #main-split {
        height: 1fr;
        layout: horizontal;
    }
    """

    BINDINGS = [
        Binding("f12", "toggle_developer_mode", "Developer Mode", priority=True),
        Binding("ctrl+c", "quit_app", "Quit Console", priority=True),
        Binding("ctrl+l", "clear_conversation", "Clear Screen")
    ]

    def __init__(
        self,
        bridge: Optional[CognitiveBridge] = None,
        identity_path: str = "alpha_identity.md",
        model_url: str = "http://localhost:1234/v1",
        default_model: str = "gemma-4-e4b-it-ultra-uncensored-heretic",
        initial_developer_mode: bool = False,
        start_autonomous: bool = False,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.bridge = bridge or CognitiveBridge(
            identity_path=identity_path,
            model_url=model_url,
            default_model=default_model
        )
        self.initial_developer_mode = initial_developer_mode
        self.start_autonomous = start_autonomous
        self.is_processing_query = False
        self.inbound_ui_queue: queue.Queue = queue.Queue()

    def compose(self) -> ComposeResult:
        yield TopBarWidget(id="top-bar")
        with Horizontal(id="main-split"):
            yield ConversationPanel(id="conversation-panel")
            yield CognitiveTracePanel(id="trace-panel")
        yield LiveLogPanel(id="live-log-panel")

    def safe_post_ui(self, callback: Callable, *args: Any, **kwargs: Any) -> None:
        """Execute a UI callback safely across thread and asyncio loop boundaries."""
        cur_id = threading.get_ident()
        app_id = getattr(self, "_thread_id", None)
        if app_id is not None and cur_id == app_id:
            try:
                callback(*args, **kwargs)
            except Exception as exc:
                logger.error(f"UI update failed on main thread: {exc}")
        else:
            try:
                self.call_from_thread(callback, *args, **kwargs)
            except RuntimeError as r_err:
                if "must run in a different thread" in str(r_err):
                    try:
                        callback(*args, **kwargs)
                    except Exception:
                        pass
                else:
                    logger.error(f"UI dispatch runtime error: {r_err}")
            except Exception as exc:
                logger.error(f"UI dispatch failed from worker thread: {exc}")

    def on_mount(self) -> None:
        """Initialize telemetry timers and attach bridge listeners."""
        # 1. Attach log listener to bridge
        log_panel = self.query_one("#live-log-panel", LiveLogPanel)
        self.bridge.add_log_listener(lambda entry: self.safe_post_ui(log_panel.add_log_entry, entry))

        # 2. Boot Bridge if not operational
        if self.bridge.alpha_status != "OPERATIONAL":
            try:
                self.bridge.boot()
            except Exception as ex:
                self.notify(f"Boot Invariant Error: {str(ex)}", severity="error", timeout=10)

        # 3. Attach inbound UI queue to background cognitive runtime
        if getattr(self.bridge, "runtime", None):
            self.bridge.runtime.attach_ui_queue(self.inbound_ui_queue)

        # 4. Setup periodic hardware and telemetry refresh (every 1.0s)
        self.set_interval(1.0, self._periodic_telemetry_update)
        self._periodic_telemetry_update()

        # 5. Setup decoupled event queue drainer and live cognitive feed (every 0.2s and 1.5s)
        self.set_interval(0.2, self._drain_inbound_ui_events)
        self.set_interval(1.5, self._periodic_live_feed_update)

        # 6. Initialize developer mode if specified
        if self.initial_developer_mode:
            self.action_toggle_developer_mode()

        # 7. Start autonomous mode if requested
        if self.start_autonomous:
            convo = self.query_one("#conversation-panel", ConversationPanel)
            convo.add_system_card(
                "AUTONOMOUS COGNITION ONLINE",
                "Alpha's persistent CognitiveRuntime is operating continuously in the background.\n"
                "Streaming thoughts, observations, reflections, and workspace mutations live.",
                "green"
            )

        # Focus input box
        try:
            inp = self.query_one("#user-input", Input)
            inp.focus()
        except Exception:
            pass

    def _periodic_telemetry_update(self) -> None:
        """Polls telemetry from bridge and updates TopBar."""
        try:
            topbar = self.query_one("#top-bar", TopBarWidget)
            telemetry = self.bridge.get_top_bar_telemetry()
            topbar.update_telemetry(telemetry)
        except Exception:
            pass

    def _drain_inbound_ui_events(self) -> None:
        """Processes events queued by background CognitiveRuntime without thread boundary issues."""
        while not self.inbound_ui_queue.empty():
            try:
                event = self.inbound_ui_queue.get_nowait()
                log_panel = self.query_one("#live-log-panel", LiveLogPanel)
                entry = LogEntry(
                    timestamp=event.timestamp,
                    category=event.event_type.value,
                    level="INFO" if event.significance < 0.7 else "WARN",
                    message=event.title,
                    details=event.data
                )
                log_panel.add_log_entry(entry)
            except queue.Empty:
                break
            except Exception:
                pass

    def _periodic_live_feed_update(self) -> None:
        """Fetch live cognitive feed snapshot from runtime and render in trace panel."""
        try:
            feed = self.bridge.get_live_cognitive_feed()
            if feed:
                trace_panel = self.query_one("#trace-panel", CognitiveTracePanel)
                if hasattr(trace_panel, "update_live_feed"):
                    trace_panel.update_live_feed(feed)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Actions & Keybindings
    # -------------------------------------------------------------------------

    def action_toggle_developer_mode(self) -> None:
        """Toggle F12 Developer Mode."""
        trace_panel = self.query_one("#trace-panel", CognitiveTracePanel)
        active = trace_panel.toggle_developer_mode()
        convo = self.query_one("#conversation-panel", ConversationPanel)
        mode_str = "ENABLED" if active else "DISABLED"
        convo.add_system_card("DEVELOPER MODE", f"Full Developer Mode (F12): **{mode_str}**.\nInspect raw prompts, retrievals, embeddings, and model output.", "magenta")

    def action_quit_app(self) -> None:
        self.exit()

    def action_clear_conversation(self) -> None:
        self.notify("Screen cleared", timeout=2)

    # -------------------------------------------------------------------------
    # Input & Command Handling
    # -------------------------------------------------------------------------

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return

        input_widget = event.input
        input_widget.value = ""

        convo = self.query_one("#conversation-panel", ConversationPanel)

        # Handle Commands starting with '/'
        if user_text.startswith("/"):
            await self._handle_command(user_text)
            return

        # Normal Cognitive Query
        if self.is_processing_query:
            self.notify("Alpha is currently reasoning. Please wait...", severity="warning")
            return

        convo.add_user_message(user_text)
        self.run_worker(self._process_cognitive_query_worker(user_text), group="query", exclusive=False)

    async def _handle_command(self, cmd_text: str) -> None:
        parts = cmd_text.split()
        cmd = parts[0].lower()
        convo = self.query_one("#conversation-panel", ConversationPanel)

        if cmd in ("/exit", "/quit"):
            self.exit()
            return

        elif cmd == "/debug":
            self.action_toggle_developer_mode()
            return

        elif cmd == "/reload":
            self.bridge.reload()
            convo.add_system_card("SYSTEM RELOAD", "Identity and Tiered Knowledge hot-reloaded successfully.", "green")
            return

        elif cmd == "/status":
            top = self.bridge.get_top_bar_telemetry()
            hw = self.bridge.get_hardware_metrics()
            status_md = (
                f"### System Operational Status\n"
                f"- **Alpha Status:** {top['alpha_status']}\n"
                f"- **Foundation Model:** {top['model_status']}\n"
                f"- **Memory System:** {top['memory_status']}\n"
                f"- **World Model:** {top['world_model_status']}\n"
                f"- **Governance:** {top['governance_status']}\n"
                f"- **Embedding System:** {top['embedding_status']}\n"
                f"- **Research Engine:** {top['research_status']}\n"
                f"- **Agent System:** {top['agent_status']}\n"
                f"- **CPU:** {hw['cpu_percent']}% | **RAM:** {hw['ram_percent']}% ({hw['ram_used_gb']}GB) | **GPU:** {hw['gpu_info']}\n"
                f"- **Console Uptime:** {hw['uptime_str']}"
            )
            convo.add_system_card("SYSTEM STATUS", status_md, "cyan")
            return

        elif cmd == "/autonomous":
            convo.add_system_card("AUTONOMOUS RESEARCH", "Initiating Autonomous Scientific Discovery Loop...", "yellow")
            self.run_worker(self._handle_autonomous_command(), group="autonomous", exclusive=True)
            return

        # Subsystem Inspection Modals
        modal_tab_map = {
            "/help": "tab-help",
            "/model": "tab-model",
            "/world": "tab-world",
            "/beliefs": "tab-beliefs",
            "/goals": "tab-beliefs",
            "/memory": "tab-memory",
            "/embeddings": "tab-embeddings",
            "/knowledge": "tab-knowledge",
            "/research": "tab-research",
            "/agents": "tab-agents",
            "/tools": "tab-tools",
            "/governance": "tab-governance",
            "/truth": "tab-truth",
            "/identity": "tab-identity"
        }

        tab_id = modal_tab_map.get(cmd)
        if tab_id:
            modal = SubsystemInspectionScreen(self.bridge, initial_tab=tab_id)
            self.push_screen(modal)
        else:
            convo.add_system_card("UNKNOWN COMMAND", f"Command `{cmd}` not recognized. Type `/help` for list of commands.", "red")

    async def _handle_autonomous_command(self) -> None:
        convo = self.query_one("#conversation-panel", ConversationPanel)
        convo.add_system_card("AUTONOMOUS MODE", "Requesting atomic thought & discovery cycle execution from background CognitiveRuntime...", "yellow")
        try:
            loop = asyncio.get_running_loop()
            def _run():
                if getattr(self.bridge, "runtime", None):
                    return self.bridge.runtime.thought_engine.run_single_cycle()
                return {}
            record = await loop.run_in_executor(None, _run)
            result_md = (
                f"### Autonomous Cognitive Cycle Completed!\n"
                f"- **Cycle:** #{record.get('cycle_number')}\n"
                f"- **Observation:** {record.get('observation')}\n"
                f"- **Insight:** {record.get('insight')}\n"
                f"- **Improvement Suggestion:** {record.get('suggestion')}\n"
                f"- **Duration:** {record.get('duration_s')}s"
            )
            convo.add_system_card("DISCOVERY RESULT", result_md, "green")
        except Exception as ex:
            convo.add_system_card("AUTONOMOUS ERROR", f"Autonomous cycle failed: {str(ex)}", "red")

    # -------------------------------------------------------------------------
    # Cognitive Query Execution Worker
    # -------------------------------------------------------------------------

    async def _process_cognitive_query_worker(self, user_query: str) -> None:
        self.is_processing_query = True
        convo = self.query_one("#conversation-panel", ConversationPanel)
        trace_panel = self.query_one("#trace-panel", CognitiveTracePanel)

        convo.start_streaming_response()

        def on_token(token: str, is_reasoning: bool) -> None:
            if is_reasoning:
                self.safe_post_ui(trace_panel.append_reasoning_token, token)
            else:
                self.safe_post_ui(convo.append_stream_token, token, is_reasoning)

        def on_trace_update(trace: CognitiveTrace) -> None:
            self.safe_post_ui(trace_panel.update_trace, trace)

        try:
            trace = await self.bridge.execute_cognitive_query(
                user_query=user_query,
                token_stream_callback=on_token,
                trace_update_callback=on_trace_update
            )
            convo.finish_streaming_response(trace.final_response)
        except Exception as exc:
            convo.finish_streaming_response(f"**Error in Cognitive Execution:** {str(exc)}")
            self.bridge.emit_log("ERROR", "ERROR", f"Cognitive Pipeline Exception: {str(exc)}")
        finally:
            self.is_processing_query = False
            try:
                inp = self.query_one("#user-input", Input)
                inp.focus()
            except Exception:
                pass
