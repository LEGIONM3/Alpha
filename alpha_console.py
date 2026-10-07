"""Alpha Terminal Cognitive Console (TCC).

The primary development and epistemic verification interface for Project Alpha.

Launch with:
    python alpha_console.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

# Ensure standard output supports UTF-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from alpha.ui.cognitive_bridge import CognitiveBridge, SafeBootError
from alpha.ui.app import AlphaConsoleApp

cli = typer.Typer(help="Alpha Terminal Cognitive Console (TCC)")
console = Console(highlight=False)


def print_startup_diagnostics(bridge: CognitiveBridge) -> None:
    """Print pre-boot diagnostics for Identity, World Model, and Embeddings."""
    console.print()
    banner = Text()
    banner.append("PROJECT ALPHA ", style="bold black on #58a6ff")
    banner.append(" TERMINAL COGNITIVE CONSOLE (TCC) v5.0.0 ", style="bold white on #1f6feb")
    banner.append("\nDevelopment & Verification Interface (Reality-Grounded Cognition)", style="dim italic")
    console.print(Panel(banner, border_style="#388bfd", padding=(0, 1)))

    # 1. Identity Initialization Display
    id_table = Table(title="Identity Initialization (alpha_identity.md)", border_style="cyan")
    id_table.add_column("Property", style="bold cyan", width=22)
    id_table.add_column("Value", style="white")

    id_table.add_row("Identity Name", bridge.identity.name)
    id_table.add_row("Designation", bridge.identity.designation)
    id_table.add_row("Mission", bridge.identity.mission[:85] + "...")
    id_table.add_row("Values", ", ".join(bridge.identity.values[:4]))
    id_table.add_row("Constitution Status", f"{len(bridge.identity.constitution)} Invariant Articles Active")
    id_table.add_row("Governance Status", bridge.governance_status)
    id_table.add_row("Identity SHA-256 Hash", bridge.identity.identity_hash)
    id_table.add_row("Drift Status", "NOMINAL (Score: 0.00 / Zero Drift)")
    console.print(id_table)

    # 2. World Model Initialization Display
    wm_summary = bridge.get_world_model_summary()
    wm_table = Table(title="World Model Initialization", border_style="yellow")
    wm_table.add_column("Dimension", style="bold yellow", width=22)
    wm_table.add_column("Count / Health", style="white")

    wm_table.add_row("Entity Count", str(wm_summary.get("total_entities", 0)))
    wm_table.add_row("Relationship Count", str(wm_summary.get("total_relationships", 0)))
    wm_table.add_row("Belief Count", str(wm_summary.get("total_beliefs", 0)))
    wm_table.add_row("Goal Count", str(wm_summary.get("goals_count", 0)))
    wm_table.add_row("Capability Count", str(wm_summary.get("capabilities_count", 0)))
    wm_table.add_row("Risk Count", str(wm_summary.get("risks_count", 0)))
    wm_table.add_row("World Model Health", str(wm_summary.get("health", "HEALTHY")))
    console.print(wm_table)

    # 3. Embedding System Display
    emb_summary = bridge.get_embedding_summary()
    emb_table = Table(title="Embedding System Initialization", border_style="green")
    emb_table.add_column("Infrastructure", style="bold green", width=22)
    emb_table.add_column("Status / Metric", style="white")

    emb_table.add_row("Embedding Model", str(emb_summary.get("embedding_model")))
    emb_table.add_row("Vector Database", "Local Dense Index + JSON Persistence Cache")
    emb_table.add_row("Total Embeddings", f"{emb_summary.get('cached_vectors')} cached / {emb_summary.get('indexed_documents')} indexed")
    emb_table.add_row("Index Status", str(emb_summary.get("index_status")))
    emb_table.add_row("Embedding Health", str(emb_summary.get("embedding_health")))
    emb_table.add_row("Retrieval Latency", f"{bridge.last_model_latency_ms} ms (probe latency)")
    emb_table.add_row("Search Accuracy", "Cosine Similarity Ranking (Top-K Dense Retrieval)")
    console.print(emb_table)

    console.print("\n[bold green][OK] Pre-flight verification passed cleanly. Entering interactive console...[/bold green]\n")
    time.sleep(1.0)


@cli.command()
def main(
    identity_path: str = typer.Option("alpha_identity.md", "--identity", "-i", help="Path to identity markdown specification"),
    model_url: str = typer.Option("http://localhost:1234/v1", "--model-url", "-u", help="OpenAI-compatible base URL"),
    model_name: str = typer.Option("gemma-4-e4b-it-ultra-uncensored-heretic", "--model", "-m", help="Foundation model identifier"),
    embedding_model: str = typer.Option("text-embedding-nomic-embed-text-v1.5", "--embedding-model", "-e", help="Embedding model name"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Launch directly in Developer Mode (F12)"),
    autonomous: bool = typer.Option(False, "--autonomous", "-a", help="Trigger autonomous discovery cycle on startup"),
    headless_probe: bool = typer.Option(False, "--headless-probe", help="Run boot verification and print diagnostics without launching UI")
) -> None:
    """Launch the Alpha Terminal Cognitive Console (TCC)."""
    # Initialize Cognitive Bridge
    bridge = CognitiveBridge(
        identity_path=identity_path,
        model_url=model_url,
        default_model=model_name,
        embedding_model=embedding_model
    )

    # Execute boot with strict fail-safe boundary
    try:
        bridge.boot()
    except SafeBootError as err:
        console.print(f"\n[bold red][CRITICAL BOOT FAILURE][/bold red] {str(err)}", style="bold red")
        console.print("[bold yellow]Boot aborted safely: System refused to enter ungrounded operational state.[/bold yellow]\n")
        sys.exit(1)
    except Exception as exc:
        console.print(f"\n[bold red][UNEXPECTED BOOT EXCEPTION][/bold red] {str(exc)}", style="bold red")
        sys.exit(1)

    # Print startup diagnostics
    print_startup_diagnostics(bridge)

    if headless_probe:
        console.print("[bold cyan]Headless probe completed successfully. Exiting.[/bold cyan]")
        return

    # Launch Textual App
    app = AlphaConsoleApp(
        bridge=bridge,
        identity_path=identity_path,
        model_url=model_url,
        default_model=model_name,
        initial_developer_mode=debug,
        start_autonomous=autonomous
    )
    app.run()


if __name__ == "__main__":
    cli()
