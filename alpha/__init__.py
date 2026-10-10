"""Alpha: Tool-Augmented Cognitive Operating System."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

__version__ = "2.0.0"

if TYPE_CHECKING:
    from alpha.config import AlphaConfig, default_config
    from alpha.core.engine import AlphaEngine
    from alpha.decomposer.decomposer import TaskDecomposer
    from alpha.experience.logger import ExperienceLogger
    from alpha.knowledge.store import KnowledgeStore
    from alpha.memory.manager import MemoryManager
    from alpha.operating_system import AlphaOperatingSystem
    from alpha.planner.planner import Planner
    from alpha.reflection.engine import ReflectionEngine
    from alpha.research import ResearchCivilization

_LAZY_IMPORTS = {
    "AlphaConfig": ("alpha.config", "AlphaConfig"),
    "default_config": ("alpha.config", "default_config"),
    "AlphaEngine": ("alpha.core.engine", "AlphaEngine"),
    "MemoryManager": ("alpha.memory.manager", "MemoryManager"),
    "TaskDecomposer": ("alpha.decomposer.decomposer", "TaskDecomposer"),
    "Planner": ("alpha.planner.planner", "Planner"),
    "ReflectionEngine": ("alpha.reflection.engine", "ReflectionEngine"),
    "ExperienceLogger": ("alpha.experience.logger", "ExperienceLogger"),
    "KnowledgeStore": ("alpha.knowledge.store", "KnowledgeStore"),
    "AlphaOperatingSystem": ("alpha.operating_system", "AlphaOperatingSystem"),
    "ResearchCivilization": ("alpha.research", "ResearchCivilization"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_name, attr_name = _LAZY_IMPORTS[name]
        mod = importlib.import_module(module_name)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AlphaConfig",
    "default_config",
    "AlphaEngine",
    "AlphaOperatingSystem",
    "ResearchCivilization",
    "MemoryManager",
    "TaskDecomposer",
    "Planner",
    "ReflectionEngine",
    "ExperienceLogger",
    "KnowledgeStore",
]
