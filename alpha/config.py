"""Configuration settings for Alpha Phase 1 Cognitive Scaffolding Layer."""

from pathlib import Path
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"

class AlphaConfig(BaseModel):
    """Configuration for Alpha Scaffolding System."""
    
    # Storage settings
    db_path: str = Field(
        default=str(DATA_DIR / "alpha_scaffolding.db"),
        description="Path to SQLite database file"
    )
    
    # Context window & token budgeting for low-reasoning SLMs
    max_context_tokens: int = Field(
        default=2048,
        description="Maximum prompt context token budget for small models"
    )
    max_memory_retrieval_tokens: int = Field(
        default=600,
        description="Budget allocated for retrieved memories in prompt"
    )
    max_knowledge_retrieval_tokens: int = Field(
        default=500,
        description="Budget allocated for retrieved knowledge documents in prompt"
    )
    max_working_memory_items: int = Field(
        default=10,
        description="Max items kept in active working memory scratchpad"
    )
    
    # Task Decomposer settings
    max_decomposition_depth: int = Field(
        default=3,
        description="Max depth: 0=Goal, 1=SubGoal, 2=Task, 3=AtomicAction"
    )
    max_task_retries: int = Field(
        default=3,
        description="Maximum attempts for an individual task before escalating failure"
    )
    
    # Reflection & Learning settings
    reflection_threshold: float = Field(
        default=0.75,
        description="Score threshold below which an output requires revision/retry"
    )
    auto_record_experience: bool = Field(
        default=True,
        description="Whether to automatically record every step execution in experience log"
    )
    auto_store_lessons: bool = Field(
        default=True,
        description="Whether to commit distilled lessons to memory automatically"
    )
    
    # Foundation Model Settings (OpenAI-compatible local/remote endpoint)
    model_endpoint: str = Field(
        default="http://localhost:1234/v1",
        description="Base URL for OpenAI-compatible LLM endpoint"
    )
    model_name: str = Field(
        default="gemma-4-e4b-it-ultra-uncensored-heretic",
        description="Target model identifier at endpoint"
    )

    # Environment
    debug_mode: bool = Field(
        default=False,
        description="Enable verbose logging and execution traces"
    )

default_config = AlphaConfig()
