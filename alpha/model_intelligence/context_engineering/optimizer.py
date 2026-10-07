"""Context Optimizer: Coordinates Context Engineering components for optimal prompt scaffolding."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from alpha.model_intelligence.context_engineering.compressor import ContextCompressor
from alpha.model_intelligence.context_engineering.ranking import ContextRankingEngine
from alpha.model_intelligence.context_engineering.layout import ContextLayoutEngine, ContextLayout


class ContextOptimizationConfig(BaseModel):
    max_tokens: int = 1500
    world_model_depth: int = 4
    belief_depth: int = 4
    memory_depth: int = 3
    reflection_depth: int = 2
    example_depth: int = 2
    deduplicate: bool = True


class ContextOptimizer:
    """Orchestrates compression, ranking, layout, and budget bounding for prompt context."""

    def __init__(
        self,
        compressor: Optional[ContextCompressor] = None,
        ranking_engine: Optional[ContextRankingEngine] = None,
        layout_engine: Optional[ContextLayoutEngine] = None
    ):
        self.compressor = compressor or ContextCompressor()
        self.ranking_engine = ranking_engine or ContextRankingEngine()
        self.layout_engine = layout_engine or ContextLayoutEngine()

    def optimize_context(
        self,
        task_query: str,
        world_model_items: Optional[List[Dict[str, Any]]] = None,
        beliefs: Optional[List[Dict[str, Any]]] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
        reflections: Optional[List[Dict[str, Any]]] = None,
        examples: Optional[List[str]] = None,
        config: Optional[ContextOptimizationConfig] = None
    ) -> ContextLayout:
        cfg = config or ContextOptimizationConfig()

        # 1. Rank candidates against task query
        ranked_wm = self.ranking_engine.rank_fragments(world_model_items or [], task_query)[:cfg.world_model_depth]
        ranked_beliefs = self.ranking_engine.rank_fragments(beliefs or [], task_query)[:cfg.belief_depth]
        ranked_memories = self.ranking_engine.rank_fragments(memories or [], task_query)[:cfg.memory_depth]
        ranked_reflections = self.ranking_engine.rank_fragments(reflections or [], task_query)[:cfg.reflection_depth]

        # 2. Stringify items
        wm_strs = [
            f"{item.get('name', item.get('id', 'entity'))}: {item.get('description', item.get('content', ''))}"
            for item in ranked_wm
        ]
        b_strs = [
            f"{b.get('statement', b.get('content', ''))} [conf={b.get('confidence', 1.0):.2f}]"
            for b in ranked_beliefs
        ]
        m_strs = [
            str(m.get('content', m.get('summary', m.get('text', ''))))
            for m in ranked_memories
        ]
        r_strs = [
            str(r.get('lesson', r.get('content', r.get('text', ''))))
            for r in ranked_reflections
        ]
        ex_strs = (examples or [])[:cfg.example_depth]

        # 3. Compress if requested
        if cfg.deduplicate:
            wm_strs = [self.compressor.compress_text(w, max_tokens=100) for w in wm_strs]
            b_strs = [self.compressor.compress_text(b, max_tokens=100) for b in b_strs]
            m_strs = [self.compressor.compress_text(m, max_tokens=100) for m in m_strs]
            r_strs = [self.compressor.compress_text(r, max_tokens=100) for r in r_strs]

        # 4. Assemble layout
        layout = self.layout_engine.assemble_layout(
            world_model_items=wm_strs,
            beliefs=b_strs,
            memories=m_strs,
            reflections=r_strs,
            examples=ex_strs
        )
        return layout
