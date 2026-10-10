"""Harmless Local Test Application for Native macOS Vertical Slice Verification.

Provides a lightweight, safe, self-contained Tkinter GUI window ("AlphaMacTestApp")
that can be launched inside the logged-in macOS Aqua session to test:
- Window title and UI hierarchy inspection
- Semantic button click ("Increment Counter")
- Text entry in an input field
- Independent post-action state mutation verification ("Status: Mutated | Counter: 1")
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


def run_test_app(state_file: str = "", auto_close_seconds: float = 120.0) -> None:
    import tkinter as tk

    root = tk.Tk()
    root.title("Alpha Mac Agent Verification App")
    root.geometry("420x260+120+120")

    counter = {"value": 0}
    status_var = tk.StringVar(value="Status: Ready | Counter: 0")
    entry_var = tk.StringVar(value="")

    def _persist_state() -> None:
        if state_file:
            Path(state_file).write_text(
                json.dumps(
                    {
                        "window_title": root.title(),
                        "status": status_var.get(),
                        "counter": counter["value"],
                        "entry_text": entry_var.get(),
                        "timestamp": time.time(),
                    }
                ),
                encoding="utf-8",
            )

    def on_increment() -> None:
        counter["value"] += 1
        txt = entry_var.get().strip()
        suffix = f" | Input: {txt}" if txt else ""
        status_var.set(f"Status: Mutated | Counter: {counter['value']}{suffix}")
        _persist_state()

    header = tk.Label(root, text="Alpha Safe Local Test Target", font=("Helvetica", 14, "bold"))
    header.pack(pady=10)

    status_lbl = tk.Label(root, textvariable=status_var, font=("Helvetica", 12))
    status_lbl.pack(pady=8)

    entry = tk.Entry(root, textvariable=entry_var, width=30)
    entry.pack(pady=6)

    btn = tk.Button(root, text="Increment Counter", command=on_increment, width=20)
    btn.pack(pady=10)

    _persist_state()
    if auto_close_seconds > 0:
        root.after(int(auto_close_seconds * 1000), root.destroy)

    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Harmless Alpha macOS GUI test application")
    parser.add_argument("--state-file", default="", help="Optional JSON file to mirror UI state")
    parser.add_argument("--timeout", type=float, default=120.0, help="Auto-close timeout in seconds")
    args = parser.parse_args()
    run_test_app(state_file=args.state_file, auto_close_seconds=args.timeout)
