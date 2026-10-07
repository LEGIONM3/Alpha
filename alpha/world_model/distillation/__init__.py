"""Distillation module exports for Project Alpha."""

from alpha.world_model.distillation.compression import CompressionEngine
from alpha.world_model.distillation.abstraction import AbstractionEngine, PatternExtractionEngine
from alpha.world_model.distillation.distillation_engine import DistillationEngine

__all__ = [
    "CompressionEngine",
    "AbstractionEngine",
    "PatternExtractionEngine",
    "DistillationEngine",
]
