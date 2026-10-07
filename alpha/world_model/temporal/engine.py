"""Time Engine: Clock management, virtual time progression, simulation ticks, and temporal coordination."""

import time
from typing import Dict, Any, Optional


class TimeEngine:
    """Manages system time progression, virtual clock, simulation ticks, and timestamps."""

    def __init__(self, real_time_start: Optional[float] = None):
        self._initial_wall_clock = real_time_start or time.time()
        self._virtual_time = self._initial_wall_clock
        self._current_tick = 0
        self._tick_duration_seconds = 1.0
        self._is_paused = False

    @property
    def current_virtual_time(self) -> float:
        """Current virtual epoch timestamp."""
        return self._virtual_time

    @property
    def current_tick(self) -> int:
        """Current discrete simulation tick."""
        return self._current_tick

    def advance_time(self, seconds: float) -> float:
        """Advance virtual time by a designated delta in seconds."""
        if not self._is_paused and seconds > 0:
            self._virtual_time += seconds
            ticks = int(seconds / self._tick_duration_seconds)
            self._current_tick += max(1, ticks)
        return self._virtual_time

    def tick(self) -> int:
        """Step forward by one discrete tick."""
        if not self._is_paused:
            self._current_tick += 1
            self._virtual_time += self._tick_duration_seconds
        return self._current_tick

    def pause(self) -> None:
        self._is_paused = True

    def resume(self) -> None:
        self._is_paused = False

    def is_paused(self) -> bool:
        return self._is_paused

    def reset_to(self, target_time: float) -> None:
        """Reset virtual clock to a historical or initial point."""
        self._virtual_time = target_time
        self._current_tick = 0
