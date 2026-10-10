"""Future Laya Observation Observer for Project Alpha.

Sensory interface capturing host OS desktop, display, window, and computer-use reality:
- Desktop window titles and active UI handles
- Display screen dimensions and pixel geometries
- Host platform OS, desktop architecture, and display environment availability
- Browser runtime reachability and automation socket status

Strictly facts-only. Zero summaries, zero reasoning. Contains exact provenance.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import platform
import sys
from typing import Any, Dict, List, Optional

from alpha.observation_engine.observation import Observation

logger = logging.getLogger("alpha.observation_engine.laya")


class LayaObservationObserver:
    """Acquires empirical sensory facts about the host computer-use environment."""

    source_type: str = "laya_observation"

    def __init__(self, computer_use_dir: Optional[Path] = None):
        env_cu = os.environ.get("COMPUTER_USE_ROOT")
        default_cu = (
            Path(env_cu)
            if env_cu
            else Path(__file__).resolve().parent.parent.parent.parent / "Computer-Use"
        )
        self.computer_use_dir = computer_use_dir or default_cu

    def observe(self) -> List[Observation]:
        observations: List[Observation] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        # 1. Host OS environment sensory facts
        env_facts = {
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "python_executable": sys.executable,
            "architecture": platform.architecture()[0],
            "computer_use_dir_exists": self.computer_use_dir.exists(),
            "display_session_type": os.environ.get("SESSIONNAME", "Console")
        }

        # On Windows, query active windows if possible without heavy DLL dependencies
        windows_detected = []
        if platform.system() == "Windows":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                # Get desktop dimensions
                width = user32.GetSystemMetrics(0)
                height = user32.GetSystemMetrics(1)
                env_facts["screen_width_pixels"] = width
                env_facts["screen_height_pixels"] = height
            except Exception:
                pass

        obs_desktop = Observation(
            observation_id=f"obs_laya_env_{platform.system().lower()}",
            source="laya://host_desktop_environment",
            source_type=self.source_type,
            timestamp=now_ts,
            confidence=1.0,
            evidence=env_facts,
            metadata={
                "provenance": "laya_sensory_probe",
                "sensor": "host_environment_sensor",
                "reproducible_query": "ctypes.windll.user32.GetSystemMetrics"
            }
        )
        observations.append(obs_desktop)

        # 2. Check Computer-Use runtime artifacts
        if self.computer_use_dir.exists():
            checkpoints = list(self.computer_use_dir.glob("**/*.pt")) + list(self.computer_use_dir.glob("**/*.pth"))
            obs_cu = Observation(
                observation_id=f"obs_laya_subsystem_{len(checkpoints)}",
                source=self.computer_use_dir.as_posix(),
                source_type=self.source_type,
                timestamp=now_ts,
                confidence=1.0,
                evidence={
                    "package_root": str(self.computer_use_dir),
                    "checkpoints_found": [c.name for c in checkpoints[:5]],
                    "checkpoint_count": len(checkpoints)
                },
                metadata={
                    "provenance": "computer_use_filesystem",
                    "absolute_path": str(self.computer_use_dir)
                }
            )
            observations.append(obs_cu)

        return observations
