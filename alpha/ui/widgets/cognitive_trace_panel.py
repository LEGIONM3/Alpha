"""Cognitive Trace Panel for Alpha Terminal Cognitive Console (TCC).

The core diagnostic observation instrument exposing Alpha's internal cognition:
- 10-Stage Reasoning Pipeline
- Retrieved Memories
- Loaded Knowledge Domains
- World Model Queries & Active Beliefs
- Tool Calls & Sandboxing Contracts
- Embedding Searches (Cosine Similarities)
- Agent Deliberation Activity
- Governance & Constitution Checks
- Epistemic Truth Checks
- Foundation Model Thinking / Reasoning Stream
- Developer Mode (F12): Raw Prompts, Retrievals, Embeddings, Model Outputs, Agent Messages.
"""

from __future__ import annotations

import json
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.widget import Widget
from textual.widgets import Static, TabbedContent, TabPane
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from alpha.ui.cognitive_bridge import CognitiveTrace, CognitiveTraceStep


class CognitiveTracePanel(Widget):
    """Right panel exposing live cognitive trace and developer introspection."""

    DEFAULT_CSS = """
    CognitiveTracePanel {
        width: 1fr;
        height: 1fr;
        background: #0d1117;
        border: solid #30363d;
        layout: vertical;
    }

    #trace-header {
        dock: top;
        height: 1;
        background: #161b22;
        color: #d2a8ff;
        text-style: bold;
        padding: 0 1;
        border-bottom: solid #21262d;
    }

    #trace-tabs {
        height: 100%;
        background: #0d1117;
    }

    .trace-card {
        margin: 1 1;
        padding: 0 1;
        background: #161b22;
        border-left: solid #d2a8ff;
    }

    .step-passed {
        color: #3fb950;
        text-style: bold;
    }

    .step-warn {
        color: #d29922;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.developer_mode: bool = False
        self.latest_trace: CognitiveTrace | None = None

    def compose(self) -> ComposeResult:
        yield Static(" 🔬 COGNITIVE TRACE & REASONING PIPELINE ", id="trace-header")
        with TabbedContent(id="trace-tabs"):
            with TabPane("Pipeline", id="pane-pipeline"):
                with ScrollableContainer(id="pipeline-scroll"):
                    yield Static(Panel("Awaiting initial cognitive query to trace...", title="PIPELINE STATUS", border_style="dim"))

            with TabPane("Memories & Knowledge", id="pane-memory"):
                with ScrollableContainer(id="memory-scroll"):
                    yield Static(Panel("No memories retrieved yet.", title="EPISODIC MEMORIES", border_style="dim"))

            with TabPane("World Model & Truth", id="pane-world"):
                with ScrollableContainer(id="world-scroll"):
                    yield Static(Panel("No world model queries executed yet.", title="EPISTEMIC GROUNDING", border_style="dim"))

            with TabPane("Thinking Stream", id="pane-thought"):
                with ScrollableContainer(id="thought-scroll"):
                    yield Static(Panel("Internal reasoning tokens from foundation model will stream here.", title="REASONING THOUGHT STREAM", border_style="dim"))

            with TabPane("Raw Debug (F12)", id="pane-debug"):
                with ScrollableContainer(id="debug-scroll"):
                    yield Static(Panel("Developer Mode (F12) inactive.\nPress F12 or type /debug to toggle full raw prompt, embedding, and model inspection.", title="DEVELOPER RAW TELEMETRY", border_style="dim"))

    def toggle_developer_mode(self) -> bool:
        """Toggle developer mode and focus debug pane."""
        self.developer_mode = not self.developer_mode
        header = self.query_one("#trace-header", Static)
        if self.developer_mode:
            header.update(Text(" 🔬 COGNITIVE TRACE [DEVELOPER MODE ACTIVE: F12] ", style="bold black on #d2a8ff"))
            tabs = self.query_one("#trace-tabs", TabbedContent)
            tabs.active = "pane-debug"
        else:
            header.update(Text(" 🔬 COGNITIVE TRACE & REASONING PIPELINE ", style="bold #d2a8ff"))
            tabs = self.query_one("#trace-tabs", TabbedContent)
            tabs.active = "pane-pipeline"

        if self.latest_trace:
            self._render_debug_tab(self.latest_trace)

        return self.developer_mode

    def update_trace(self, trace: CognitiveTrace) -> None:
        """Update all trace tabs with fresh cognitive trace data."""
        self.latest_trace = trace
        self._render_pipeline_tab(trace)
        self._render_memory_tab(trace)
        self._render_world_tab(trace)
        self._render_thought_tab(trace)
        if self.developer_mode:
            self._render_debug_tab(trace)

    def append_reasoning_token(self, token: str) -> None:
        """Update live reasoning tokens in Thinking Stream pane."""
        try:
            scroll = self.query_one("#thought-scroll", ScrollableContainer)
            # Find thought static
            thought_widget = scroll.query_one("Static")
            current = ""
            if self.latest_trace:
                current = self.latest_trace.reasoning_text
            thought_widget.update(Panel(
                Text(current + " ▋", style="italic #d2a8ff"),
                title="🧠 LIVE FOUNDATION MODEL REASONING",
                border_style="#a371f7"
            ))
        except Exception:
            pass

    def update_live_feed(self, feed: dict) -> None:
        """Render Alpha's continuous autonomous live cognitive feed in the Thinking Stream tab."""
        try:
            scroll = self.query_one("#thought-scroll", ScrollableContainer)
            scroll.remove_children()

            table = Table(title=f"⚡ LIVE COGNITIVE FEED (Cycle #{feed.get('cycle_count', 0)})", border_style="#a371f7")
            table.add_column("Cognitive Dimension", style="bold magenta", width=22)
            table.add_column("Current Autonomous State", style="white")

            table.add_row("Current Thought", str(feed.get("current_thought", "")))
            table.add_row("Current Observation", str(feed.get("current_observation", "")))
            table.add_row("Current Reflection", str(feed.get("current_reflection", "")))
            table.add_row("Current Concern", str(feed.get("current_concern", "")))
            table.add_row("Current Goal", str(feed.get("current_goal", "")))
            table.add_row("Current Suggestion", str(feed.get("current_suggestion", "")))
            table.add_row("Current Risk", str(feed.get("current_risk", "")))
            table.add_row("Confidence", f"{float(feed.get('current_confidence', 0.94)):.2f}")
            table.add_row("Current Mission", str(feed.get("current_mission", "")))
            table.add_row("Self Assessment", str(feed.get("current_self_assessment", "")))
            table.add_row("Current Target", str(feed.get("current_target", "alpha/core/identity.py")))
            next_act = feed.get("next_planned_action", {})
            next_str = f"[{next_act.get('action', 'investigate')}] -> {next_act.get('target', '')}" if next_act else "Autonomous continuation loop active"
            table.add_row("Next Action", next_str)

            scroll.mount(Static(table))
        except Exception:
            pass

    def _render_pipeline_tab(self, trace: CognitiveTrace) -> None:
        try:
            scroll = self.query_one("#pipeline-scroll", ScrollableContainer)
            scroll.remove_children()

            table = Table(title=f"Cognitive Execution Pipeline ({trace.total_latency_ms}ms total)", border_style="#30363d")
            table.add_column("Stage", style="bold cyan", width=5)
            table.add_column("Category", style="magenta", width=12)
            table.add_column("Subsystem", style="bold white", width=26)
            table.add_column("Status", style="green", width=11)
            table.add_column("Summary", style="dim white")
            table.add_column("Latency", justify="right", style="yellow", width=8)

            for step in trace.steps:
                status_style = "bold green" if step.status in ("PASSED", "COMPLETED") else "bold yellow"
                table.add_row(
                    str(step.step_id),
                    step.category,
                    step.name,
                    Text(step.status, style=status_style),
                    step.summary,
                    f"{step.duration_ms:.1f}ms"
                )

            scroll.mount(Static(table))

            # Identity Influence Card
            id_text = Text()
            id_text.append("Identity Invariants: ", style="bold cyan")
            id_text.append(trace.identity_influence + "\n\n", style="white")
            id_text.append("Decision Sources: ", style="bold magenta")
            id_text.append(", ".join(trace.decision_sources) or "Direct Reality-Grounding", style="yellow")
            scroll.mount(Static(Panel(id_text, title="IDENTITY & DECISION PROVENANCE", border_style="cyan"), classes="trace-card"))

        except Exception:
            pass

    def _render_memory_tab(self, trace: CognitiveTrace) -> None:
        try:
            scroll = self.query_one("#memory-scroll", ScrollableContainer)
            scroll.remove_children()

            # Memories
            mem_text = Text()
            if trace.retrieved_memories:
                for idx, m in enumerate(trace.retrieved_memories, 1):
                    mem_text.append(f"[{idx}] {m['type'].upper()} (Importance: {m['importance']}):\n", style="bold cyan")
                    mem_text.append(f"    {m['content']}\n", style="white")
                    if m.get("tags"):
                        mem_text.append(f"    Tags: {', '.join(m['tags'])}\n", style="dim")
            else:
                mem_text.append("No episodic memories retrieved for this inquiry.", style="dim")

            scroll.mount(Static(Panel(mem_text, title=f"RETRIEVED MEMORIES ({len(trace.retrieved_memories)})", border_style="magenta")))

            # Knowledge Domains
            k_text = Text()
            for kd in trace.loaded_knowledge:
                k_text.append(f"• {kd}\n", style="bold green")
            scroll.mount(Static(Panel(k_text, title="LOADED KNOWLEDGE DOMAINS (TIER 0 - TIER 3)", border_style="green")))

            # Embedding Searches
            emb_table = Table(title="Dense Embedding Search Results (768-d Nomic)", border_style="#30363d")
            emb_table.add_column("Doc ID", style="bold cyan")
            emb_table.add_column("Cosine Similarity", justify="right", style="bold yellow")
            emb_table.add_column("Content Snippet", style="white")
            for e in trace.embedding_searches:
                emb_table.add_row(e.get("id", ""), f"{e.get('similarity', 0.0):.4f}", e.get("text", "")[:60] + "...")
            scroll.mount(Static(emb_table))

        except Exception:
            pass

    def _render_world_tab(self, trace: CognitiveTrace) -> None:
        try:
            scroll = self.query_one("#world-scroll", ScrollableContainer)
            scroll.remove_children()

            # Beliefs Table
            bel_table = Table(title="World Model Grounded Beliefs", border_style="#30363d")
            bel_table.add_column("Belief ID", style="bold cyan")
            bel_table.add_column("Statement", style="white")
            bel_table.add_column("Confidence", justify="right", style="bold green")
            bel_table.add_column("Domain", style="magenta")

            for b in trace.world_model_queries:
                if "belief_id" in b:
                    bel_table.add_row(
                        b["belief_id"][:12],
                        b["statement"],
                        f"{b['confidence']:.2f}",
                        b.get("domain", "general")
                    )

            scroll.mount(Static(bel_table))

            # Governance Checks
            gov_text = Text()
            for g in trace.governance_checks:
                status_style = "bold green" if g.get("passed") else "bold red"
                gov_text.append(f"• {g.get('check')}: ", style="bold white")
                gov_text.append(f"{'PASSED' if g.get('passed') else 'FAILED'}\n", style=status_style)
                gov_text.append(f"  Reason: {g.get('reason')}\n", style="dim")
            scroll.mount(Static(Panel(gov_text, title="GOVERNANCE CHECKS", border_style="blue")))

            # Truth Layer Checks
            truth_text = Text()
            for t in trace.truth_checks:
                truth_text.append(f"• {t.get('check')}: {t.get('status')} ({t.get('confidence_threshold', '')})\n", style="bold green")
            scroll.mount(Static(Panel(truth_text, title="EPISTEMIC TRUTH VERIFICATION", border_style="yellow")))

        except Exception:
            pass

    def _render_thought_tab(self, trace: CognitiveTrace) -> None:
        try:
            scroll = self.query_one("#thought-scroll", ScrollableContainer)
            scroll.remove_children()
            raw_thought = trace.reasoning_text or "(No internal reasoning tokens returned for this completion)"
            scroll.mount(Static(Panel(
                Text(raw_thought, style="italic #d2a8ff"),
                title="FOUNDATION MODEL REASONING TOKENS",
                border_style="#a371f7"
            )))
        except Exception:
            pass

    def _render_debug_tab(self, trace: CognitiveTrace) -> None:
        try:
            scroll = self.query_one("#debug-scroll", ScrollableContainer)
            scroll.remove_children()

            # Raw Prompts
            p_text = trace.raw_prompt or "(None)"
            scroll.mount(Static(Panel(Syntax(p_text, "markdown", theme="monokai", word_wrap=True), title="RAW PROMPT SENT TO http://localhost:1234/v1", border_style="red")))

            # Raw Model Output
            m_text = trace.raw_model_output or "(None)"
            scroll.mount(Static(Panel(Syntax(m_text, "text", theme="monokai", word_wrap=True), title="RAW MODEL OUTPUT", border_style="yellow")))

            # Raw Retrievals & Embeddings
            r_text = trace.raw_retrievals or "(None)"
            scroll.mount(Static(Panel(Syntax(r_text, "json", theme="monokai", word_wrap=True), title="RAW RETRIEVALS & EMBEDDINGS (JSON)", border_style="cyan")))

        except Exception:
            pass
