"""Abstraction Engine & Pattern Extraction Engine: Mining invariants from high-volume episodic records."""

from typing import List, Dict, Any, Tuple
from collections import Counter


class PatternExtractionEngine:
    """Discovers recurring sequences, common token collocations, and structural invariants."""

    def extract_common_tokens(self, texts: List[str], top_k: int = 5) -> List[Tuple[str, int]]:
        """Identify highest-frequency informational tokens excluding stopwords."""
        stopwords = {"the", "a", "an", "in", "on", "of", "to", "for", "with", "and", "or", "is", "was", "by", "at"}
        counts = Counter()
        for t in texts:
            words = [w.strip(".,;:!?()[]\"'") for w in t.lower().split()]
            for w in words:
                if len(w) > 2 and w not in stopwords:
                    counts[w] += 1
        return counts.most_common(top_k)

    def extract_attribute_invariants(self, records: List[Dict[str, Any]], consistency_threshold: float = 0.8) -> Dict[str, Any]:
        """Discover key-value pairs that hold true across the majority of records."""
        if not records:
            return {}
        field_values = Counter()
        for r in records:
            for k, v in r.items():
                if isinstance(v, (str, int, float, bool)):
                    field_values[(k, str(v))] += 1

        invariants = {}
        n = len(records)
        for (k, val_str), count in field_values.items():
            if (count / n) >= consistency_threshold:
                invariants[k] = val_str
        return invariants


class AbstractionEngine:
    """Lifts granular episodic details into generalized conceptual statements."""

    def __init__(self, pattern_extractor: PatternExtractionEngine = None):
        self.extractor = pattern_extractor or PatternExtractionEngine()

    def abstract_cluster(self, cluster_texts: List[str], domain_label: str = "CognitiveDomain") -> Dict[str, Any]:
        """Produce a distilled summary and invariant representation for a cluster."""
        tokens = self.extractor.extract_common_tokens(cluster_texts, top_k=3)
        top_words = [t[0].capitalize() for t in tokens] or ["General", "Mechanism"]
        concept_title = f"{' '.join(top_words)} System"
        definition = f"Generalized concept abstracted from {len(cluster_texts)} instances highlighting {', '.join(top_words)}."

        return {
            "title": concept_title,
            "definition": definition,
            "domain": domain_label,
            "exemplar_sample": cluster_texts[:3],
            "instance_count": len(cluster_texts),
            "salient_features": [t[0] for t in tokens]
        }
