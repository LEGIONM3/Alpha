"""Run the Foundation Model Agent.

This script launches Alpha's Foundation Model in autonomous mode,
where it continuously discovers goals, reasons through them,
executes tool-based actions, and learns from outcomes.

Usage:
    python run_foundation_model.py [--model-url http://localhost:1234/v1]
"""

import argparse
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Alpha Foundation Model in autonomous mode"
    )
    parser.add_argument(
        "--workspace", type=str, default=None,
        help="Path to the workspace directory (default: current dir)"
    )
    parser.add_argument(
        "--model-url", type=str, default="http://localhost:1234/v1",
        help="URL of the foundation model endpoint"
    )
    parser.add_argument(
        "--model", type=str, default="gemma-4-e4b-it-ultra-uncensored-heretic",
        help="Default model to use for reasoning"
    )
    parser.add_argument(
        "--interval", type=float, default=5.0,
        help="Seconds between autonomous thought cycles (default: 5)"
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Enable interactive mode with direct user prompts"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    from alpha.foundation_model.agent import FoundationModelAgent
    from alpha.core.model_adapter import ModelAdapter

    workspace_root = Path(args.workspace) if args.workspace else Path.cwd() / "alpha"

    # Initialize the foundation model agent
    print("=" * 70)
    print("  🧠 PROJECT ALPHA: FOUNDATION MODEL AGENT")
    print("  Autonomous Cognitive System v1.0.0")
    print("=" * 70)
    
    agent = FoundationModelAgent(
        workspace_root=workspace_root,
        model_url=args.model_url,
        default_model=args.model,
        thought_interval_seconds=float(args.interval),
        enable_external_model=True if "1234" in args.model_url else False,
    )

    # Show initial state
    print(f"\n  Workspace: {workspace_root.resolve()}")
    print(f"  Model:     {args.model}")
    print(f"  Interval:  every {args.interval}s")
    print("-" * 70)

    if args.interactive:
        # Interactive mode — respond to user prompts
        print("\n💬 Type your request and press Enter (or 'quit' to exit):")
        print("   (The agent will reason through your question autonomously)")
        print("-" * 70)

        while True:
            try:
                user_input = input("\nYou> ").strip()
                
                if not user_input or user_input.lower() in ("quit", "exit"):
                    break
                
                response = agent.respond_to_user(user_input)
                print(f"\n🤖 Agent:\n{response}")

            except KeyboardInterrupt:
                print("\n\n  👋 Goodbye!")
                break
    else:
        # Autonomous mode — the agent discovers and pursues goals itself
        print("\n⚙️  Starting autonomous reasoning cycle...")
        print("   The agent will independently discover goals, reason through them,"
              " execute actions via tools, and learn from outcomes.\n")

        # Give it a head start with an initial goal discovery scan
        print("🔍 Scanning environment for meaningful work to do...\n")
        goals = agent.goal_discovery.discover_all()[:5]

        if not goals:
            print("  No immediate goals detected. Waiting for input...")
            print("\n💡 Tip: Run with --interactive for direct conversation mode.")
        else:
            for g in goals:
                print(f"  📌 {g.status.value}: {g.title}")

    # Save final state before shutdown
    agent.save_state()


if __name__ == "__main__":
    main()