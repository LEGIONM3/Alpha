"""Alpha: Tool-Augmented Cognitive Operating System."""

__version__ = "2.0.0"

from alpha.config import AlphaConfig, default_config
from alpha.core.engine import AlphaEngine
from alpha.memory.manager import MemoryManager
from alpha.decomposer.decomposer import TaskDecomposer
from alpha.planner.planner import Planner
from alpha.reflection.engine import ReflectionEngine
from alpha.experience.logger import ExperienceLogger
from alpha.knowledge.store import KnowledgeStore
from alpha.operating_system import AlphaOperatingSystem
from alpha.research import ResearchCivilization

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
    "KnowledgeStore"
]
