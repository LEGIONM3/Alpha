"""CLI Entrypoint for Starting the Apple Silicon Mac Computer-Use Agent Service.

Usage on Apple Silicon MacBook (inside logged-in Aqua desktop session):
    export ALPHA_MAC_AGENT_TOKEN="<strong-shared-secret>"
    export ALPHA_AUTHORIZED_CLIENT_IPS="127.0.0.1,<legion-private-ip>"
    python -m alpha.computer_use.mac_agent.cli --bind-host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import signal
import sys
import time

from alpha.computer_use.mac_agent.platform_probe import MacPlatformProbe
from alpha.computer_use.mac_agent.policy import MacAgentPolicy
from alpha.computer_use.mac_agent.server import MacAgentHTTPServer, MacAgentServiceCore


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Project Alpha — Apple Silicon macOS Computer-Use Agent Service"
    )
    parser.add_argument(
        "--bind-host",
        default=os.environ.get("ALPHA_MAC_BIND_HOST", "127.0.0.1"),
        help="Private interface IP to bind (127.0.0.1, Tailscale 100.x.y.z, or LAN 192.168.x.y). Never 0.0.0.0.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ALPHA_MAC_BIND_PORT", "8765")),
        help="TCP port to listen on (default: 8765)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force headless Chromium mode (default is visible browser window on macOS Aqua)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run platform, session, and TCC permission probe and exit",
    )
    parser.add_argument(
        "--audit-log",
        default="data/mac_agent_audit.jsonl",
        help="Path to structured JSONL audit log",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    probe = MacPlatformProbe()
    report = probe.inspect_platform()
    if args.check_only:
        print(json.dumps(report.model_dump(), indent=2))
        return 0 if report.ready_for_browser else 1

    token = os.environ.get("ALPHA_MAC_AGENT_TOKEN", "")
    if not token:
        print(
            "ERROR: ALPHA_MAC_AGENT_TOKEN environment variable is not set (min 8 chars required).",
            file=sys.stderr,
        )
        return 2

    core = MacAgentServiceCore(
        auth_token=token,
        policy=MacAgentPolicy(),
        platform_probe=probe,
        audit_log_path=Path(args.audit_log),
        headless_browser=True if args.headless else None,
    )
    server = MacAgentHTTPServer(core=core, bind_host=args.bind_host, bind_port=args.port)
    url = server.start()
    logging.info(f"Alpha Mac Computer-Use Agent listening on {url}/v1")

    stop_flag = {"stop": False}

    def _sig_handler(_signum: int, _frame: object) -> None:
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    try:
        while not stop_flag["stop"]:
            time.sleep(0.5)
    finally:
        logging.info("Shutting down Alpha Mac Computer-Use Agent...")
        server.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
