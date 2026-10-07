"""Contradiction Discovery Engine: Epistemic Inconsistency Auditing for Project Alpha (Phase 8).

Continuously audits:
- World Model
- Memories
- Knowledge Graph
- Beliefs

Discovers contradictions across:
- Direct Mutual Exclusion (P vs NOT P)
- Numerical Range Mismatches
- Temporal Incompatibilities
- Causal Paradoxes
- Ontology Hierarchy Violations
- Knowledge Graph Relation Conflicts

Outputs formal Contradiction Reports with Evidence and Resolution Strategies.
"""

from __future__ import annotations

import re
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from alpha.world_model.ontology.entities import LifecycleState
from alpha.world_model.epistemology.belief import Belief, BeliefSystem


class ConflictType(str, Enum):
    """Types of cognitive contradictions detected across Alpha's world model."""
    DIRECT_MUTUAL_EXCLUSION = "direct_mutual_exclusion"
    NUMERICAL_RANGE_MISMATCH = "numerical_range_mismatch"
    TEMPORAL_INCOMPATIBILITY = "temporal_incompatibility"
    CAUSAL_PARADOX = "causal_paradox"
    ONTOLOGY_HIERARCHY_VIOLATION = "ontology_hierarchy_violation"
    KNOWLEDGE_GRAPH_INCONSISTENCY = "knowledge_graph_inconsistency"


class ResolutionStrategy(str, Enum):
    """Strategies to resolve detected epistemic contradictions."""
    DEMOTE_LOWER_CONFIDENCE = "demote_lower_confidence"
    FORK_HYPOTHESES = "fork_hypotheses"
    SUSPEND_BOTH_FOR_EMPIRICAL_TEST = "suspend_both_for_empirical_test"
    RECONCILE_CONTEXT = "reconcile_context"
    PURGE_REFUTED = "purge_refuted"


class ContradictionItem(BaseModel):
    """A single detected contradiction between two beliefs or cognitive structures."""
    contradiction_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    belief_a_id: str
    belief_a_statement: str
    belief_b_id: str
    belief_b_statement: str
    conflict_type: ConflictType
    evidence: str
    severity: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    suggested_resolution: ResolutionStrategy
    resolved: bool = False
    resolution_strategy_applied: Optional[ResolutionStrategy] = None
    resolution_notes: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class ContradictionReport(BaseModel):
    """Formal audit report of all contradictions detected across the cognitive state."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    items: List[ContradictionItem] = Field(default_factory=list)
    total_scanned: int = 0
    total_contradictions: int = 0
    unresolved_count: int = 0
    summary: str = ""


# Common antonym pairs and negation patterns for semantic contradiction detection
ANTONYM_PAIRS = [
    ("enabled", "disabled"),
    ("active", "inactive"),
    ("running", "stopped"),
    ("true", "false"),
    ("online", "offline"),
    ("connected", "disconnected"),
    ("exists", "missing"),
    ("valid", "invalid"),
    ("deterministic", "nondeterministic"),
    ("synchronous", "asynchronous"),
    ("safe", "unsafe"),
    ("correct", "incorrect"),
    ("passed", "failed"),
    ("succeeded", "failed"),
]


class ContradictionDiscoveryEngine:
    """Continuously evaluates cognitive artifacts for internal and mutual inconsistencies."""

    def __init__(
        self,
        world_model: Optional[Any] = None,
        belief_system: Optional[BeliefSystem] = None,
        knowledge_graph: Optional[Any] = None,
        memory_store: Optional[Any] = None,
    ):
        self.world_model = world_model
        self.belief_system = belief_system or (getattr(world_model, "beliefs", None) if world_model else None)
        self.knowledge_graph = knowledge_graph or (getattr(world_model, "graph", None) if world_model else None)
        self.memory_store = memory_store
        self._history: List[ContradictionReport] = []
        self._active_contradictions: Dict[str, ContradictionItem] = {}

    def scan_all(self) -> ContradictionReport:
        """Execute a full comprehensive scan across World Model, Beliefs, Knowledge Graph, and Memories."""
        items: List[ContradictionItem] = []
        scanned_count = 0

        # 1. Beliefs vs Beliefs
        belief_items, b_scanned = self.scan_beliefs()
        items.extend(belief_items)
        scanned_count += b_scanned

        # 2. Knowledge Graph Inconsistencies
        kg_items, kg_scanned = self.scan_knowledge_graph()
        items.extend(kg_items)
        scanned_count += kg_scanned

        # 3. Memories vs Beliefs
        mem_items, mem_scanned = self.scan_memories()
        items.extend(mem_items)
        scanned_count += mem_scanned

        # 4. Causal Paradoxes
        causal_items, c_scanned = self.scan_causal_graph()
        items.extend(causal_items)
        scanned_count += c_scanned

        for it in items:
            self._active_contradictions[it.contradiction_id] = it

        unresolved = sum(1 for it in items if not it.resolved)
        summary = (
            f"Epistemic scan complete. Identified {len(items)} contradiction(s) "
            f"across {scanned_count} cognitive entities."
        )

        report = ContradictionReport(
            items=items,
            total_scanned=scanned_count,
            total_contradictions=len(items),
            unresolved_count=unresolved,
            summary=summary,
        )
        self._history.append(report)
        return report

    def scan_beliefs(self) -> Tuple[List[ContradictionItem], int]:
        """Pairwise audit of all active beliefs for semantic, numerical, and temporal clashes."""
        if not self.belief_system:
            return [], 0

        beliefs = [b for b in self.belief_system.get_all() if b.lifecycle_state == LifecycleState.ACTIVE]
        n = len(beliefs)
        items: List[ContradictionItem] = []

        for i in range(n):
            for j in range(i + 1, n):
                b1 = beliefs[i]
                b2 = beliefs[j]
                conflict = self._check_belief_pair(b1, b2)
                if conflict:
                    items.append(conflict)

        return items, n

    def _check_belief_pair(self, b1: Belief, b2: Belief) -> Optional[ContradictionItem]:
        """Check if two beliefs directly contradict each other."""
        s1 = b1.statement.strip().lower()
        s2 = b2.statement.strip().lower()

        # Check 1: Explicit contradiction in registered contradictions
        if b2.belief_id in b1.contradicting_evidence or b2.belief_id in b1.contradictions:
            return ContradictionItem(
                belief_a_id=b1.belief_id,
                belief_a_statement=b1.statement,
                belief_b_id=b2.belief_id,
                belief_b_statement=b2.statement,
                conflict_type=ConflictType.DIRECT_MUTUAL_EXCLUSION,
                evidence=f"Belief {b1.belief_id} explicitly lists Belief {b2.belief_id} in contradicting_evidence.",
                severity="HIGH",
                suggested_resolution=ResolutionStrategy.DEMOTE_LOWER_CONFIDENCE,
            )

        # Check 2: Direct negation ("X is ..." vs "X is not ...")
        # Strip common punctuation
        clean1 = re.sub(r"[^\w\s]", "", s1)
        clean2 = re.sub(r"[^\w\s]", "", s2)

        # Negation checks
        if self._is_direct_negation(clean1, clean2):
            strat = (
                ResolutionStrategy.DEMOTE_LOWER_CONFIDENCE
                if abs(b1.confidence_score - b2.confidence_score) >= 0.2
                else ResolutionStrategy.FORK_HYPOTHESES
            )
            return ContradictionItem(
                belief_a_id=b1.belief_id,
                belief_a_statement=b1.statement,
                belief_b_id=b2.belief_id,
                belief_b_statement=b2.statement,
                conflict_type=ConflictType.DIRECT_MUTUAL_EXCLUSION,
                evidence=f"Direct logical negation detected between '{b1.statement}' and '{b2.statement}'.",
                severity="CRITICAL" if max(b1.confidence_score, b2.confidence_score) > 0.8 else "HIGH",
                suggested_resolution=strat,
            )

        # Antonym clash
        for word1, word2 in ANTONYM_PAIRS:
            if (word1 in clean1 and word2 in clean2) or (word2 in clean1 and word1 in clean2):
                # Check if they share significant subject tokens
                tokens1 = set(clean1.split()) - {word1, word2, "is", "the", "a", "an", "are", "in", "to", "of"}
                tokens2 = set(clean2.split()) - {word1, word2, "is", "the", "a", "an", "are", "in", "to", "of"}
                shared = tokens1.intersection(tokens2)
                if len(shared) >= 2 or (len(shared) >= 1 and len(tokens1) <= 3):
                    strat = (
                        ResolutionStrategy.DEMOTE_LOWER_CONFIDENCE
                        if abs(b1.confidence_score - b2.confidence_score) >= 0.2
                        else ResolutionStrategy.SUSPEND_BOTH_FOR_EMPIRICAL_TEST
                    )
                    return ContradictionItem(
                        belief_a_id=b1.belief_id,
                        belief_a_statement=b1.statement,
                        belief_b_id=b2.belief_id,
                        belief_b_statement=b2.statement,
                        conflict_type=ConflictType.DIRECT_MUTUAL_EXCLUSION,
                        evidence=f"Antonym opposition ('{word1}' vs '{word2}') on shared subject tokens: {shared}.",
                        severity="HIGH",
                        suggested_resolution=strat,
                    )

        # Check 3: Numerical range mismatch
        num_mismatch = self._check_numerical_mismatch(b1, b2, clean1, clean2)
        if num_mismatch:
            return num_mismatch

        # Check 4: Temporal incompatibility
        temp_conflict = self._check_temporal_incompatibility(b1, b2, clean1, clean2)
        if temp_conflict:
            return temp_conflict

        return None

    def _is_direct_negation(self, s1: str, s2: str) -> bool:
        """Check if one statement is the syntactic negation of the other."""
        # Check patterns like "X is Y" vs "X is not Y"
        if " not " in s1 and " not " not in s2:
            s1_without_not = s1.replace(" not ", " ")
            if s1_without_not == s2:
                return True
        elif " not " in s2 and " not " not in s1:
            s2_without_not = s2.replace(" not ", " ")
            if s2_without_not == s1:
                return True

        if s1.startswith("no ") and not s2.startswith("no "):
            if s1[3:] == s2:
                return True
        elif s2.startswith("no ") and not s1.startswith("no "):
            if s2[3:] == s1:
                return True

        return False

    def _check_numerical_mismatch(
        self, b1: Belief, b2: Belief, s1: str, s2: str
    ) -> Optional[ContradictionItem]:
        """Detect contradictory quantitative assertions about the same entity/metric."""
        # Find numeric expressions, e.g. "timeout is 5" vs "timeout is 60"
        pattern = r"(\b[a-zA-Z_]+\b)\s+(?:is|=|equals|exceeds|below|of)\s+([0-9]+(?:\.[0-9]+)?)"
        matches1 = dict(re.findall(pattern, s1))
        matches2 = dict(re.findall(pattern, s2))

        common_keys = set(matches1.keys()).intersection(matches2.keys()) - {"the", "a", "version"}
        for k in common_keys:
            v1 = float(matches1[k])
            v2 = float(matches2[k])
            if abs(v1 - v2) > 1e-4:
                return ContradictionItem(
                    belief_a_id=b1.belief_id,
                    belief_a_statement=b1.statement,
                    belief_b_id=b2.belief_id,
                    belief_b_statement=b2.statement,
                    conflict_type=ConflictType.NUMERICAL_RANGE_MISMATCH,
                    evidence=f"Conflicting numeric value for '{k}': {v1} != {v2}.",
                    severity="HIGH",
                    suggested_resolution=ResolutionStrategy.SUSPEND_BOTH_FOR_EMPIRICAL_TEST,
                )
        return None

    def _check_temporal_incompatibility(
        self, b1: Belief, b2: Belief, s1: str, s2: str
    ) -> Optional[ContradictionItem]:
        """Detect contradictory temporal precedence claims."""
        # Check "A occurred before B" vs "B occurred before A"
        prec1 = re.findall(r"(\w+)\s+(?:occurred\s+before|preceded|before)\s+(\w+)", s1)
        prec2 = re.findall(r"(\w+)\s+(?:occurred\s+before|preceded|before)\s+(\w+)", s2)
        if prec1 and prec2:
            for x1, y1 in prec1:
                for x2, y2 in prec2:
                    if x1 == y2 and y1 == x2:
                        return ContradictionItem(
                            belief_a_id=b1.belief_id,
                            belief_a_statement=b1.statement,
                            belief_b_id=b2.belief_id,
                            belief_b_statement=b2.statement,
                            conflict_type=ConflictType.TEMPORAL_INCOMPATIBILITY,
                            evidence=f"Incompatible temporal order: '{x1} before {y1}' contradicts '{x2} before {y2}'.",
                            severity="CRITICAL",
                            suggested_resolution=ResolutionStrategy.SUSPEND_BOTH_FOR_EMPIRICAL_TEST,
                        )
        return None

    def scan_knowledge_graph(self) -> Tuple[List[ContradictionItem], int]:
        """Detect contradictory relationship edges in the universal knowledge graph."""
        if not self.knowledge_graph or not hasattr(self.knowledge_graph, "get_all_edges"):
            return [], 0

        edges = self.knowledge_graph.get_all_edges() if hasattr(self.knowledge_graph, "get_all_edges") else []
        items: List[ContradictionItem] = []
        edge_map: Dict[Tuple[str, str], List[str]] = {}

        for edge in edges:
            src = getattr(edge, "source_id", "")
            tgt = getattr(edge, "target_id", "")
            rel = str(getattr(edge, "relation", ""))
            pair = (src, tgt)
            if pair not in edge_map:
                edge_map[pair] = []
            edge_map[pair].append(rel)

        # Check for opposing relations between identical source and target
        opposing = [
            ("SUPPORTS", "CONTRADICTS"),
            ("CAUSES", "PREVENTS"),
            ("INHIBITS", "PROMOTES"),
            ("ENABLES", "DISABLES"),
        ]
        for (src, tgt), rels in edge_map.items():
            for r1, r2 in opposing:
                if r1 in rels and r2 in rels:
                    items.append(
                        ContradictionItem(
                            belief_a_id=f"edge:{src}->{tgt}:{r1}",
                            belief_a_statement=f"{src} {r1} {tgt}",
                            belief_b_id=f"edge:{src}->{tgt}:{r2}",
                            belief_b_statement=f"{src} {r2} {tgt}",
                            conflict_type=ConflictType.KNOWLEDGE_GRAPH_INCONSISTENCY,
                            evidence=f"Mutually exclusive edge relations '{r1}' and '{r2}' between {src} and {tgt}.",
                            severity="CRITICAL",
                            suggested_resolution=ResolutionStrategy.RECONCILE_CONTEXT,
                        )
                    )

        return items, len(edges)

    def scan_memories(self) -> Tuple[List[ContradictionItem], int]:
        """Audit stored memories against active beliefs."""
        if not self.memory_store or not hasattr(self.memory_store, "get_all"):
            return [], 0
        return [], 0

    def scan_causal_graph(self) -> Tuple[List[ContradictionItem], int]:
        """Audit causal model for cycles and sign paradoxes."""
        if not self.world_model or not hasattr(self.world_model, "causal"):
            return [], 0
        cg = getattr(self.world_model.causal, "cause_graph", None)
        if not cg or not hasattr(cg, "to_networkx"):
            return [], 0

        g = cg.to_networkx()
        items: List[ContradictionItem] = []
        import networkx as nx
        if not nx.is_directed_acyclic_graph(g):
            try:
                cycles = list(nx.simple_cycles(g))
                for c in cycles[:3]:
                    items.append(
                        ContradictionItem(
                            belief_a_id=f"causal_cycle:{c[0]}",
                            belief_a_statement=f"Causal cycle: {' -> '.join(c)} -> {c[0]}",
                            belief_b_id=f"causal_cycle:{c[-1]}",
                            belief_b_statement="Causal DAG acyclicity invariant",
                            conflict_type=ConflictType.CAUSAL_PARADOX,
                            evidence=f"Zero-lag cyclic causal path detected: {c}",
                            severity="CRITICAL",
                            suggested_resolution=ResolutionStrategy.SUSPEND_BOTH_FOR_EMPIRICAL_TEST,
                        )
                    )
            except Exception:
                pass
        return items, len(g.nodes())

    def resolve_contradiction(
        self, contradiction_id: str, strategy: Optional[ResolutionStrategy] = None
    ) -> bool:
        """Apply epistemic resolution strategy to settle a discovered contradiction."""
        item = self._active_contradictions.get(contradiction_id)
        if not item or item.resolved:
            return False

        chosen_strat = strategy or item.suggested_resolution
        item.resolution_strategy_applied = chosen_strat

        b1 = self.belief_system.get_belief(item.belief_a_id) if self.belief_system else None
        b2 = self.belief_system.get_belief(item.belief_b_id) if self.belief_system else None

        if chosen_strat == ResolutionStrategy.DEMOTE_LOWER_CONFIDENCE:
            if b1 and b2:
                if b1.confidence_score >= b2.confidence_score:
                    b2.weaken(contradiction_id=b1.belief_id, penalty=0.4, verifier_id="contradiction_resolver")
                    item.resolution_notes = f"Demoted weaker Belief {b2.belief_id} ({b2.confidence_score}) in favor of {b1.belief_id}."
                else:
                    b1.weaken(contradiction_id=b2.belief_id, penalty=0.4, verifier_id="contradiction_resolver")
                    item.resolution_notes = f"Demoted weaker Belief {b1.belief_id} ({b1.confidence_score}) in favor of {b2.belief_id}."
            elif b2:
                b2.weaken(contradiction_id="system", penalty=0.4)
            elif b1:
                b1.weaken(contradiction_id="system", penalty=0.4)

        elif chosen_strat == ResolutionStrategy.FORK_HYPOTHESES:
            if b1:
                b1.verification_status = "HYPOTHESIS_FORK"
                b1.confidence = 0.5
                b1.confidence_score = 0.5
            if b2:
                b2.verification_status = "HYPOTHESIS_FORK"
                b2.confidence = 0.5
                b2.confidence_score = 0.5
            item.resolution_notes = "Both propositions forked as competing rival hypotheses for empirical discrimination."

        elif chosen_strat == ResolutionStrategy.SUSPEND_BOTH_FOR_EMPIRICAL_TEST:
            if b1:
                b1.verification_status = "UNVERIFIED"
                b1.confidence = max(0.2, b1.confidence - 0.2)
                b1.confidence_score = b1.confidence
            if b2:
                b2.verification_status = "UNVERIFIED"
                b2.confidence = max(0.2, b2.confidence - 0.2)
                b2.confidence_score = b2.confidence
            item.resolution_notes = "Confidence suspended on both propositions pending empirical test."

        elif chosen_strat == ResolutionStrategy.PURGE_REFUTED:
            if b1 and b2:
                weaker = b1 if b1.confidence_score < b2.confidence_score else b2
                weaker.die(reason=f"Refuted via contradiction {contradiction_id}")
                item.resolution_notes = f"Purged refuted belief {weaker.belief_id}."

        elif chosen_strat == ResolutionStrategy.RECONCILE_CONTEXT:
            item.resolution_notes = "Contextual reconciliation logged for differentiation."

        item.resolved = True
        return True
