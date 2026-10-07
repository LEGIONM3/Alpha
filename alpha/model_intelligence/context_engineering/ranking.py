"""Context Ranking Engine: Scores and ranks context candidates by relevance and confidence."""

from typing import List, Dict, Any


class ContextRankingEngine:
    """Prioritizes context fragments to ensure the most vital grounding reaches the prompt first."""

    def rank_fragments(
        self,
        fragments: List[Dict[str, Any]],
        task_query: str
    ) -> List[Dict[str, Any]]:
        query_tokens = set(task_query.lower().split())

        def score(item: Dict[str, Any]) -> float:
            content = str(item.get("content", item.get("statement", item.get("text", "")))).lower()
            overlap = sum(1 for tok in query_tokens if tok in content and len(tok) > 3)
            conf = float(item.get("confidence", 0.8))
            importance = float(item.get("importance", 0.7))
            return overlap * 0.4 + conf * 0.3 + importance * 0.3

        return sorted(fragments, key=score, reverse=True)
