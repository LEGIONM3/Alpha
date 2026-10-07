"""Context Compressor: Semantic pruning, deduplication, and token-budget bounding."""

from typing import List, Dict, Any, Tuple


class ContextCompressor:
    """Compresses verbose context blocks while preserving critical factual anchors."""

    def compress_text(self, text: str, max_tokens: int = 500) -> str:
        """Token-budgeted truncation and line-level redundancy pruning."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        seen = set()
        deduped = []
        for line in lines:
            norm = line.lower()
            if norm not in seen:
                seen.add(norm)
                deduped.append(line)

        compressed = "\n".join(deduped)
        words = compressed.split()
        max_words = max_tokens * 3 // 4
        if len(words) > max_words:
            compressed = " ".join(words[:max_words]) + " ... [context truncated for budget]"
        return compressed

    def extract_key_value_anchors(self, records: List[Dict[str, Any]]) -> str:
        """Condense a list of dictionary entities into concise tabular key-values."""
        lines = []
        for r in records[:10]:
            name = r.get("name", r.get("id", "entity"))
            t = r.get("type", r.get("entity_type", "item"))
            status = r.get("status", r.get("lifecycle_state", "active"))
            lines.append(f"[{t.upper()}] {name} (Status: {status})")
        return "\n".join(lines)
