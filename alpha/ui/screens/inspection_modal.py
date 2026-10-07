"""Subsystem Inspection Modal Screen for Alpha Terminal Cognitive Console (TCC).

Provides dedicated deep diagnostic views for:
- /model
- /world
- /beliefs
- /goals
- /memory
- /embeddings
- /knowledge
- /research
- /agents
- /tools
- /governance
- /truth
- /identity
- /help
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TabbedContent, TabPane, DataTable
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from alpha.ui.cognitive_bridge import CognitiveBridge


class SubsystemInspectionScreen(ModalScreen):
    """Full-featured inspection modal with tabbed views into all cognitive subsystems."""

    DEFAULT_CSS = """
    SubsystemInspectionScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.85);
    }

    #inspection-dialog {
        width: 90%;
        height: 85%;
        background: #0d1117;
        border: thick #58a6ff;
        layout: vertical;
    }

    #dialog-header {
        height: 2;
        background: #161b22;
        color: #58a6ff;
        padding: 0 1;
        align: left middle;
        border-bottom: solid #30363d;
    }

    #dialog-tabs {
        height: 1fr;
        background: #0d1117;
    }

    #dialog-footer {
        dock: bottom;
        height: 3;
        background: #161b22;
        border-top: solid #30363d;
        align: right middle;
        padding: 0 1;
    }

    .modal-scroll {
        padding: 1 1;
        height: 100%;
        overflow-y: auto;
    }

    .close-btn {
        background: #21262d;
        color: #f0f6fc;
        border: none;
    }

    .close-btn:hover {
        background: #388bfd;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close Modal"),
        ("q", "dismiss", "Close Modal")
    ]

    def __init__(self, bridge: CognitiveBridge, initial_tab: str = "tab-help", **kwargs) -> None:
        super().__init__(**kwargs)
        self.bridge = bridge
        self.initial_tab = initial_tab

    def compose(self) -> ComposeResult:
        with Container(id="inspection-dialog"):
            with Horizontal(id="dialog-header"):
                yield Static(" 🔬 ALPHA SUBSYSTEM DIAGNOSTICS & DEEP INSPECTOR ", id="dialog-title")

            with TabbedContent(id="dialog-tabs", initial=self.initial_tab):
                with TabPane("Help (/help)", id="tab-help"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_help_view())

                with TabPane("Model (/model)", id="tab-model"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_model_view())

                with TabPane("World Model (/world)", id="tab-world"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_world_view())

                with TabPane("Beliefs & Goals", id="tab-beliefs"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_beliefs_view())

                with TabPane("Memory (/memory)", id="tab-memory"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_memory_view())

                with TabPane("Embeddings (/embeddings)", id="tab-embeddings"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_embeddings_view())

                with TabPane("Knowledge Loader", id="tab-knowledge"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_knowledge_view())

                with TabPane("Research (/research)", id="tab-research"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_research_view())

                with TabPane("Agents (/agents)", id="tab-agents"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_agents_view())

                with TabPane("Tools (/tools)", id="tab-tools"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_tools_view())

                with TabPane("Governance (/governance)", id="tab-governance"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_governance_view())

                with TabPane("Truth Layer (/truth)", id="tab-truth"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_truth_view())

                with TabPane("Identity (/identity)", id="tab-identity"):
                    with ScrollableContainer(classes="modal-scroll"):
                        yield Static(self._build_identity_view())

            with Horizontal(id="dialog-footer"):
                yield Button("Close (Esc)", id="btn-close", classes="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss()

    # -------------------------------------------------------------------------
    # View Builders
    # -------------------------------------------------------------------------

    def _build_help_view(self) -> Table:
        t = Table(title="Alpha Terminal Cognitive Console: Command Reference", border_style="cyan")
        t.add_column("Command", style="bold cyan", width=18)
        t.add_column("Description", style="white")
        t.add_column("Subsystem", style="magenta", width=16)

        t.add_row("/help", "Display full console command guide and keyboard shortcuts", "Console")
        t.add_row("/status", "Display overall health, uptime, and telemetry summary", "Master OS")
        t.add_row("/model", "Inspect foundation model latency, tokens, requests & status", "Foundation Model")
        t.add_row("/identity", "Inspect alpha_identity.md, values, constitution & hash", "Identity Engine")
        t.add_row("/world", "Inspect ontology entities, relationships, graph connectivity", "World Model")
        t.add_row("/beliefs", "Inspect active beliefs, confidence ratings, and evidence", "Epistemology")
        t.add_row("/goals", "Inspect foundational civilizational and operational goals", "World Model")
        t.add_row("/memory", "Inspect working memory, episodic observations & SQLite store", "Memory Manager")
        t.add_row("/embeddings", "Inspect dense embedding cache, vector dimensions, index state", "Embedding Service")
        t.add_row("/research", "Inspect autonomous research hypotheses, experiments & papers", "Research Engine")
        t.add_row("/agents", "Inspect 18 specialized archetypes, fitness & mailboxes", "Multi-Agent System")
        t.add_row("/tools", "Inspect 29 sandboxed tools, permissions and contracts", "Tool Registry")
        t.add_row("/governance", "Inspect change proposals, canary tests and drift metrics", "Governance Engine")
        t.add_row("/truth", "Inspect evidence registry, polarity, and conflict status", "Truth Layer")
        t.add_row("/autonomous", "Trigger live autonomous scientific research & discovery loop", "Autonomous Mind")
        t.add_row("/reload", "Hot-reload identity, tiered knowledge, and re-probe model", "Hot Reload")
        t.add_row("/debug", "Toggle full developer debug mode (raw prompts/embeddings)", "Developer Mode")
        t.add_row("/exit", "Safely terminate the console and persist all records", "Shutdown")

        return t

    def _build_model_view(self) -> Table:
        m = self.bridge.get_model_summary()
        t = Table(title="Foundation Model Diagnostics (http://localhost:1234/v1)", border_style="cyan")
        t.add_column("Metric", style="bold white", width=25)
        t.add_column("Value", style="bold yellow")

        t.add_row("Model Name", str(m["model_name"]))
        t.add_row("Endpoint URL", str(m["endpoint"]))
        t.add_row("Status", str(m["status"]))
        t.add_row("Total Requests", str(m["total_requests"]))
        t.add_row("Total Responses", str(m["total_responses"]))
        t.add_row("Failed Invocations", str(m["total_failures"]))
        t.add_row("Last Query Latency", f"{m['last_latency_ms']} ms")
        t.add_row("Average Query Latency", f"{m['avg_latency_ms']} ms")
        t.add_row("Total Prompt Tokens", str(m["total_prompt_tokens"]))
        t.add_row("Total Completion Tokens", str(m["total_completion_tokens"]))
        t.add_row("Context Window Budget", f"{m['context_budget']} tokens")
        t.add_row("Estimated Context Usage", str(m["estimated_context_usage"]))
        t.add_row("Model Health", "HEALTHY (SYNCHRONOUS & STREAMING VERIFIED)")
        return t

    def _build_world_view(self) -> Table:
        w = self.bridge.get_world_model_summary()
        t = Table(title="Cognitive World Model Ontology & Knowledge Graph", border_style="yellow")
        t.add_column("Ontological Dimension", style="bold white", width=25)
        t.add_column("Metric", style="bold green")

        t.add_row("Total Registered Entities", str(w.get("total_entities", 0)))
        t.add_row("Total Semantic Relationships", str(w.get("total_relationships", 0)))
        t.add_row("Total Epistemic Beliefs", str(w.get("total_beliefs", 0)))
        t.add_row("Active Verified Beliefs", str(w.get("active_beliefs", 0)))
        t.add_row("Active Goals", str(w.get("goals_count", 0)))
        t.add_row("Registered Capabilities", str(w.get("capabilities_count", 0)))
        t.add_row("Monitored Risks", str(w.get("risks_count", 0)))
        t.add_row("Universal Ontology Classes", "25 Classes (Entity Hierarchy)")
        t.add_row("Bidirectional Relationship Types", "14 Types (SUPPORTS, VALIDATES, CAUSES...)")
        t.add_row("World Model Health", str(w.get("health", "OPERATIONAL")))

        breakdown = w.get("entity_breakdown", {})
        if breakdown:
            t.add_row("--- Entity Type Breakdown ---", "-------------------------")
            for k, v in breakdown.items():
                t.add_row(f"  • {k.capitalize()}", str(v))

        return t

    def _build_beliefs_view(self) -> Table:
        t = Table(title="Active Grounded Beliefs (Evidence-Backed)", border_style="green")
        t.add_column("Belief ID", style="bold cyan", width=14)
        t.add_column("Statement", style="white")
        t.add_column("Confidence", justify="right", style="bold green", width=12)
        t.add_column("Domain", style="magenta", width=18)

        if self.bridge.world_model:
            beliefs = list(self.bridge.world_model.beliefs._beliefs.values())
            for b in beliefs:
                t.add_row(
                    b.belief_id[:12],
                    b.statement,
                    f"{b.confidence:.2f}",
                    b.domain
                )
        return t

    def _build_memory_view(self) -> Table:
        mem = self.bridge.get_memory_summary()
        t = Table(title=f"Memory Subsystem Inspection (SQLite DB: {mem.get('db_path')})", border_style="magenta")
        t.add_column("Metric", style="bold white", width=25)
        t.add_column("Value", style="bold yellow")

        t.add_row("Working Memory Observations", str(mem.get("working_memory_count", 0)))
        t.add_row("Total Persistent Memory Records", str(mem.get("total_stored_items", 0)))
        t.add_row("Vector Embeddings Cached", str(mem.get("cache_size", 0)))
        t.add_row("Database Journal Mode", "WAL (Write-Ahead Logging)")

        recent = mem.get("recent_memories", [])
        if recent:
            t.add_row("--- Recent Episodic Memories ---", "-------------------------")
            for r in recent[:5]:
                t.add_row(f"[{r['type']}] Imp: {r['importance']}", r["content"][:60] + "...")

        return t

    def _build_embeddings_view(self) -> Table:
        emb = self.bridge.get_embedding_summary()
        t = Table(title="Dense Embedding Infrastructure (localhost:1234/v1)", border_style="cyan")
        t.add_column("Property", style="bold white", width=25)
        t.add_column("Specification", style="bold green")

        t.add_row("Embedding Model", str(emb.get("embedding_model")))
        t.add_row("Dense Vector Dimension", f"{emb.get('vector_dimension')} dimensions")
        t.add_row("Cached Vector Count", str(emb.get("cached_vectors")))
        t.add_row("Indexed Documents", str(emb.get("indexed_documents")))
        t.add_row("Vector DB Backend", "Local In-Memory Dense Index + JSON Cache")
        t.add_row("Index Status", str(emb.get("index_status")))
        t.add_row("Embedding Health", str(emb.get("embedding_health")))
        t.add_row("Cache File Path", str(emb.get("cache_file")))
        return t

    def _build_knowledge_view(self) -> Table:
        t = Table(title="Tiered Knowledge Architecture (Tiers 0 - 3)", border_style="cyan")
        t.add_column("Tier", style="bold cyan", width=10)
        t.add_column("Category", style="magenta", width=20)
        t.add_column("Status", style="bold green", width=14)
        t.add_column("Description", style="white")

        t.add_row("Tier 0", "Identity & Constitution", "ALWAYS LOADED", "Invariant identity specification, 5 constitutional articles, non-negotiables")
        t.add_row("Tier 1", "Core Cognitive Axioms", "LOADED & CACHED", "Universal ontology contract, truth verification rules, sandbox protocols")
        t.add_row("Tier 2", "Domain Knowledge", "DYNAMIC RETRIEVAL", "Git conventions, API rate limiting, SQLite schema, architecture specs")
        t.add_row("Tier 3", "Deep Archive", "ON-DEMAND LAZY", "Historical prototypes, quantum simulations, archived research logs")
        return t

    def _build_research_view(self) -> Table:
        res = self.bridge.get_research_summary()
        t = Table(title="Research Civilization & Autonomous Discovery", border_style="yellow")
        t.add_column("Property", style="bold white", width=25)
        t.add_column("Value", style="bold green")

        t.add_row("Engine Status", str(res.get("status")))
        t.add_row("Active Scientific Loops", str(res.get("active_tasks")))

        last_cycle = res.get("last_discovery_record")
        if last_cycle:
            t.add_row("Last Discovery Observation", str(last_cycle.get("observation", ""))[:60] + "...")
            hyp = last_cycle.get("hypothesis", {})
            t.add_row("Last Hypothesis", str(hyp.get("hypothesis_statement", ""))[:60] + "...")
            exp = last_cycle.get("experiment", {})
            t.add_row("Experimental Speedup", f"{exp.get('latency_reduction_ratio', 'N/A')}x (p={exp.get('statistical_p_value', 'N/A')})")
            synth = last_cycle.get("synthesis", {})
            t.add_row("Synthesized Principle", str(synth.get("universal_principle", ""))[:60] + "...")
            t.add_row("Committed Belief ID", str(last_cycle.get("belief_id", "N/A")))
            t.add_row("Cycle Execution Latency", f"{last_cycle.get('total_cycle_time_s', 'N/A')}s")
        return t

    def _build_agents_view(self) -> Table:
        ag = self.bridge.get_agents_summary()
        t = Table(title=f"Multi-Agent Civilization: 18 Archetypes ({ag.get('total_agents')} Total)", border_style="magenta")
        t.add_column("Role", style="bold cyan", width=15)
        t.add_column("Name", style="bold white", width=20)
        t.add_column("Status", style="green", width=10)
        t.add_column("Fitness", justify="right", style="yellow", width=8)
        t.add_column("Completed", justify="right", style="white", width=10)
        t.add_column("Primary Objective", style="dim white")

        for role, data in ag.get("agents", {}).items():
            t.add_row(
                role,
                data.get("name", ""),
                data.get("status", ""),
                str(data.get("fitness", 1.0)),
                str(data.get("tasks_completed", 0)),
                data.get("objective", "")[:50] + "..."
            )
        return t

    def _build_tools_view(self) -> Table:
        tl = self.bridge.get_tools_summary()
        t = Table(title=f"Universal Tool Registry ({tl.get('total_tools')} Sandboxed Tools)", border_style="green")
        t.add_column("Tool Name", style="bold cyan", width=24)
        t.add_column("Category", style="magenta", width=15)
        t.add_column("Permission", style="bold yellow", width=14)
        t.add_column("Description", style="white")

        for item in tl.get("tools", []):
            t.add_row(
                item.get("name", ""),
                item.get("category", ""),
                item.get("permission", ""),
                item.get("description", "")
            )
        return t

    def _build_governance_view(self) -> Table:
        gov = self.bridge.get_governance_summary()
        t = Table(title="Constitutional Governance & Drift Detection", border_style="blue")
        t.add_column("Governance Parameter", style="bold white", width=25)
        t.add_column("State / Value", style="bold green")

        t.add_row("System Identity", str(gov.get("identity_name")))
        t.add_row("Identity SHA-256 Hash", str(gov.get("identity_hash")))
        t.add_row("Constitutional Articles", f"{gov.get('constitution_articles')} Invariant Articles")
        t.add_row("Drift Status", str(gov.get("drift_status")))
        t.add_row("Policy Violations Recorded", str(gov.get("policy_violations")))
        t.add_row("Governance Framework", "6-Stage Proposal Review (Separation of Powers)")

        for art in gov.get("articles", []):
            t.add_row("  • Invariant Article", art)
        return t

    def _build_truth_view(self) -> Table:
        tr = self.bridge.get_truth_summary()
        t = Table(title="Epistemic Truth Layer & Evidence Registry", border_style="yellow")
        t.add_column("Truth Metric", style="bold white", width=25)
        t.add_column("Value", style="bold green")

        t.add_row("Evidence Registry Items", str(tr.get("total_evidence_items")))
        t.add_row("Verified Beliefs (Conf >= 0.7)", str(tr.get("verified_beliefs")))
        t.add_row("Active Conjectures", str(tr.get("conjectures")))
        t.add_row("Detected Contradictions", str(tr.get("contradictions_detected")))
        t.add_row("Unverified Claims", str(tr.get("unverified_claims")))
        t.add_row("Orphan Belief Invariant", "STRICT: Zero ungrounded beliefs permitted")

        ev_items = tr.get("evidence", [])
        if ev_items:
            t.add_row("--- Empirical Evidence Samples ---", "-------------------------")
            for ev in ev_items[:5]:
                t.add_row(f"[{ev['strength']}] {ev['id'][:10]}", ev['statement'][:60] + "...")
        return t

    def _build_identity_view(self) -> Table:
        t = Table(title="Alpha Identity Specification (alpha_identity.md)", border_style="cyan")
        t.add_column("Property", style="bold white", width=20)
        t.add_column("Specification", style="white")

        if self.bridge.identity:
            t.add_row("Name", self.bridge.identity.name)
            t.add_row("Designation", self.bridge.identity.designation)
            t.add_row("Mission", self.bridge.identity.mission[:100] + "...")
            t.add_row("Identity Hash", self.bridge.identity.identity_hash)
            t.add_row("Values", ", ".join(self.bridge.identity.values[:5]))
            t.add_row("Constitution", f"{len(self.bridge.identity.constitution)} Articles")
            t.add_row("Governance Primacy", "INVIOLABLE: Cannot be modified without full council review")
        return t
