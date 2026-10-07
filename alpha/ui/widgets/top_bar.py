"""Top Bar Widget for Alpha Terminal Cognitive Console (TCC).

Displays real-time system state across:
Alpha Status | Model Status | Memory Status | World Model Status |
Governance Status | Embedding Status | Research Status | Agent Status |
CPU | RAM | GPU | Uptime
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text


class TopBarWidget(Widget):
    """Top Bar displaying high-density cognitive system metrics and resource usage."""

    DEFAULT_CSS = """
    TopBarWidget {
        dock: top;
        height: 3;
        background: #0d1117;
        color: #c9d1d9;
        border-bottom: solid #30363d;
        padding: 0 1;
    }
    
    #topbar-row1 {
        height: 1;
        align: left middle;
    }

    #topbar-row2 {
        height: 1;
        align: left middle;
    }
    """

    alpha_status = reactive("ONLINE")
    model_status = reactive("gemma-4 / ONLINE")
    memory_status = reactive("ONLINE (WAL)")
    world_status = reactive("ONLINE (25 Ent)")
    gov_status = reactive("INVARIANT (Drift 0.0)")
    emb_status = reactive("768d / nomic-embed")
    res_status = reactive("IDLE")
    agent_status = reactive("18 Archetypes")
    cpu = reactive("0.0%")
    ram = reactive("0.0%")
    gpu = reactive("CUDA (N/A)")
    uptime = reactive("00:00:00")

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar-row1"):
            yield Static(id="topbar-systems-text")
        with Horizontal(id="topbar-row2"):
            yield Static(id="topbar-resources-text")

    def update_telemetry(self, data: dict) -> None:
        """Update reactive values from bridge telemetry dictionary."""
        self.alpha_status = data.get("alpha_status", self.alpha_status)
        self.model_status = data.get("model_status", self.model_status)
        self.memory_status = data.get("memory_status", self.memory_status)
        self.world_status = data.get("world_model_status", self.world_status)
        self.gov_status = data.get("governance_status", self.gov_status)
        self.emb_status = data.get("embedding_status", self.emb_status)
        self.res_status = data.get("research_status", self.res_status)
        self.agent_status = data.get("agent_status", self.agent_status)
        self.cpu = data.get("cpu", self.cpu)
        self.ram = data.get("ram", self.ram)
        self.gpu = data.get("gpu", self.gpu)
        self.uptime = data.get("uptime", self.uptime)

        self._refresh_display()

    def _refresh_display(self) -> None:
        try:
            row1 = self.query_one("#topbar-systems-text", Static)
            row2 = self.query_one("#topbar-resources-text", Static)
        except Exception:
            return

        t1 = Text()
        t1.append(" [ALPHA] ", style="bold black on #58a6ff")
        t1.append(f" {self.alpha_status} ", style="bold green" if "OPERATIONAL" in self.alpha_status or "ONLINE" in self.alpha_status else "bold yellow")
        t1.append("│ ", style="dim")

        t1.append("MODEL: ", style="bold cyan")
        t1.append(f"{self.model_status} ", style="green" if "ONLINE" in self.model_status else "red")
        t1.append("│ ", style="dim")

        t1.append("MEM: ", style="bold magenta")
        t1.append(f"{self.memory_status} ", style="white")
        t1.append("│ ", style="dim")

        t1.append("WORLD: ", style="bold yellow")
        t1.append(f"{self.world_status} ", style="white")
        t1.append("│ ", style="dim")

        t1.append("GOV: ", style="bold blue")
        t1.append(f"{self.gov_status} ", style="cyan")

        row1.update(t1)

        t2 = Text()
        t2.append(" EMB: ", style="bold cyan")
        t2.append(f"{self.emb_status} ", style="white")
        t2.append("│ ", style="dim")

        t2.append("RES: ", style="bold yellow")
        t2.append(f"{self.res_status} ", style="green" if "IDLE" in self.res_status else "bold yellow")
        t2.append("│ ", style="dim")

        t2.append("AGENTS: ", style="bold magenta")
        t2.append(f"{self.agent_status} ", style="white")
        t2.append("│ ", style="dim")

        t2.append("CPU: ", style="bold green")
        t2.append(f"{self.cpu} ", style="white")
        t2.append("│ ", style="dim")

        t2.append("RAM: ", style="bold green")
        t2.append(f"{self.ram} ", style="white")
        t2.append("│ ", style="dim")

        t2.append("GPU: ", style="bold green")
        t2.append(f"{self.gpu} ", style="green" if "N/A" not in self.gpu else "dim")
        t2.append("│ ", style="dim")

        t2.append("UPTIME: ", style="bold white")
        t2.append(f"{self.uptime}", style="bold cyan")

        row2.update(t2)
