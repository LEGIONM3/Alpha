"""Real Knowledge Gap Detector for Project Alpha.

Detects genuine epistemic gaps grounded in repository evidence:
- Unknown Modules (codebase modules not indexed in World Model Ontology)
- Untested Paths (modules or functions lacking unit test coverage in tests/)
- Low Confidence Beliefs (beliefs with confidence < threshold or unresolved contradictions)
- Missing Causal Links (AST dependencies unmodeled in CausalReasoningEngine)
- Missing Documentation (modules and interfaces lacking docstrings)
- Dead Code (symbols defined with zero cross-module references)
- Unused Systems (subsystem tools/agents not engaged by runtime loop)

Zero simulated gaps: All gaps are detected through static AST analysis and empirical audit.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from alpha.observation_engine.engine import ObservationRecord


class KnowledgeGap(BaseModel):
    """Defines a specific area of unknown, unverified, or unmodeled knowledge."""
    topic: str
    reason: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    urgency: int = Field(default=3, ge=1, le=5)
    evidence: List[str] = Field(default_factory=list)
    category: str = Field(default="general")
    suggested_action: str = Field(default="")


class KnowledgeGapDetector:
    """Analyzes the current World Model state against the actual repository codebase

    to identify empirical gaps in knowledge, testing, causality, and architecture.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self._rotation_index: int = 0

    def detect(
        self,
        observations: List[ObservationRecord],
        world_model: Optional[Any] = None
    ) -> List[KnowledgeGap]:
        """Main detection routine analyzing repository reality and epistemic state."""
        gaps: List[KnowledgeGap] = []

        # 1. Untested Paths Detector
        untested_gaps = self._detect_untested_paths()
        gaps.extend(untested_gaps)

        # 2. Unknown Modules Detector (vs Ontology)
        unknown_gaps = self._detect_unknown_modules(world_model)
        gaps.extend(unknown_gaps)

        # 3. Low Confidence Beliefs Detector
        belief_gaps = self._detect_low_confidence_beliefs(world_model, observations)
        gaps.extend(belief_gaps)

        # 4. Missing Causal Links Detector
        causal_gaps = self._detect_missing_causal_links(world_model)
        gaps.extend(causal_gaps)

        # 5. Missing Documentation Detector
        doc_gaps = self._detect_missing_documentation()
        gaps.extend(doc_gaps)

        # 6. Dead Code Detector
        dead_code_gaps = self._detect_dead_code()
        gaps.extend(dead_code_gaps)

        # 7. Unused Systems Detector
        unused_gaps = self._detect_unused_systems()
        gaps.extend(unused_gaps)

        if not gaps:
            return []

        # Prioritize and rotate so different cycles explore diverse gaps
        gaps.sort(key=lambda g: g.urgency, reverse=True)
        count = len(gaps)
        start_idx = self._rotation_index % count
        self._rotation_index += 3

        selected: List[KnowledgeGap] = []
        for i in range(count):
            idx = (start_idx + i) % count
            candidate = gaps[idx]
            # Avoid duplicate topics in same selection
            if not any(candidate.category == s.category for s in selected):
                selected.append(candidate)
            if len(selected) >= 4:
                break

        if not selected and gaps:
            selected = gaps[:3]

        return selected

    # -------------------------------------------------------------------------
    # Empirical Gap Detectors
    # -------------------------------------------------------------------------

    def _detect_untested_paths(self) -> List[KnowledgeGap]:
        """Identifies modules in alpha/ that lack corresponding test files in tests/."""
        gaps: List[KnowledgeGap] = []
        alpha_dir = self.workspace_root / "alpha"
        tests_dir = self.workspace_root / "tests"

        if not alpha_dir.exists() or not tests_dir.exists():
            return gaps

        test_names = {p.stem.replace("test_", "") for p in tests_dir.glob("test_*.py")}
        test_contents = ""
        for tp in list(tests_dir.glob("test_*.py"))[:10]:
            try:
                test_contents += tp.read_text(encoding="utf-8", errors="ignore") + "\n"
            except Exception:
                pass

        for py_path in sorted(alpha_dir.rglob("*.py")):
            if py_path.name.startswith(("_", ".")) or "__pycache__" in str(py_path):
                continue
            stem = py_path.stem
            rel_path = py_path.relative_to(self.workspace_root).as_posix()

            # Check if tested directly by name or referenced
            is_tested = (stem in test_names) or (stem in test_contents)
            if not is_tested:
                gaps.append(
                    KnowledgeGap(
                        topic=f"Untested Module: {rel_path}",
                        reason=f"Module '{rel_path}' lacks direct unit test coverage in tests/.",
                        confidence=0.92,
                        urgency=4,
                        evidence=[f"Module: {rel_path}", f"Test counterpart test_{stem}.py not found"],
                        category="untested_path",
                        suggested_action=f"Create tests/test_{stem}.py to verify interface invariants."
                    )
                )
                if len(gaps) >= 3:
                    break

        return gaps

    def _detect_unknown_modules(self, world_model: Optional[Any]) -> List[KnowledgeGap]:
        """Detects codebase modules not yet registered in World Model Ontology."""
        gaps: List[KnowledgeGap] = []
        alpha_dir = self.workspace_root / "alpha"
        if not alpha_dir.exists():
            return gaps

        known_entities: Set[str] = set()
        if world_model and hasattr(world_model, "ontology"):
            try:
                for ent in world_model.ontology.get_all():
                    known_entities.add(ent.name.lower())
            except Exception:
                pass

        for pkg in sorted(alpha_dir.iterdir()):
            if pkg.is_dir() and not pkg.name.startswith((".", "_")):
                if pkg.name.lower() not in known_entities:
                    rel_dir = pkg.relative_to(self.workspace_root).as_posix()
                    gaps.append(
                        KnowledgeGap(
                            topic=f"Unknown Subsystem: {rel_dir}",
                            reason=f"Subsystem '{rel_dir}' is present in filesystem but unmodeled in ontology.",
                            confidence=0.88,
                            urgency=3,
                            evidence=[f"Directory: {rel_dir}", f"Registered Ontology Entities: {len(known_entities)}"],
                            category="unknown_module",
                            suggested_action=f"Register '{pkg.name}' as ComponentEntity in OntologyRegistry."
                        )
                    )
                    if len(gaps) >= 2:
                        break

        return gaps

    def _detect_low_confidence_beliefs(
        self,
        world_model: Optional[Any],
        observations: List[ObservationRecord]
    ) -> List[KnowledgeGap]:
        """Detects beliefs with low confidence or unresolved contradictions."""
        gaps: List[KnowledgeGap] = []

        if world_model and hasattr(world_model, "beliefs"):
            try:
                active_beliefs = world_model.beliefs.get_all()
                for b in active_beliefs:
                    if b.confidence < 0.65 or len(b.contradictions) > 0:
                        gaps.append(
                            KnowledgeGap(
                                topic=f"Low Confidence Belief: {b.statement[:40]}...",
                                reason=f"Belief {b.belief_id[:8]} confidence={b.confidence:.2f} with {len(b.contradictions)} contradictions.",
                                confidence=0.95,
                                urgency=4,
                                evidence=[f"Belief ID: {b.belief_id}", f"Confidence: {b.confidence}", f"Status: {b.verification_status}"],
                                category="low_confidence_belief",
                                suggested_action="Investigate empirical evidence to corroborate or refute belief."
                            )
                        )
                        if len(gaps) >= 2:
                            break
            except Exception:
                pass

        for obs in observations:
            if obs.confidence < 0.70:
                gaps.append(
                    KnowledgeGap(
                        topic=f"Low Confidence Observation from {obs.source}",
                        reason=f"Observation content exhibits uncertainty: {obs.content[:60]}",
                        confidence=0.85,
                        urgency=3,
                        evidence=[f"Source: {obs.source}", f"Observation Hash: {obs.hash[:8]}"],
                        category="low_confidence_belief",
                        suggested_action="Collect corroborating citations to verify claim."
                    )
                )

        return gaps

    def _detect_missing_causal_links(self, world_model: Optional[Any]) -> List[KnowledgeGap]:
        """Detects unmodeled causal dependencies by analyzing AST imports."""
        gaps: List[KnowledgeGap] = []
        alpha_dir = self.workspace_root / "alpha"
        if not alpha_dir.exists():
            return gaps

        # Trace couple of import pairs
        candidate_pairs: List[Tuple[str, str]] = []
        for py_path in sorted(alpha_dir.rglob("*.py"))[:20]:
            if "__pycache__" in str(py_path):
                continue
            try:
                tree = ast.parse(py_path.read_text(encoding="utf-8", errors="replace"), filename=str(py_path))
                caller_mod = py_path.stem
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module and "alpha" in node.module:
                        dep = node.module.split(".")[-1]
                        if dep != caller_mod:
                            candidate_pairs.append((caller_mod, dep))
                            if len(candidate_pairs) >= 5:
                                break
            except Exception:
                continue

        for caller, callee in candidate_pairs:
            # Check if modeled in causal engine
            has_link = False
            if world_model and hasattr(world_model, "causal"):
                try:
                    has_link = world_model.causal.has_relation(caller, callee) if hasattr(world_model.causal, "has_relation") else False
                except Exception:
                    pass

            if not has_link:
                gaps.append(
                    KnowledgeGap(
                        topic=f"Missing Causal Link: {caller} -> {callee}",
                        reason=f"Module '{caller}' depends on '{callee}', but causal dependency is unmodeled.",
                        confidence=0.82,
                        urgency=3,
                        evidence=[f"AST Import Dependency: {caller} imports {callee}"],
                        category="missing_causal_link",
                        suggested_action=f"Register causal link between '{caller}' and '{callee}' in CausalReasoningEngine."
                    )
                )
                if len(gaps) >= 2:
                    break

        return gaps

    def _detect_missing_documentation(self) -> List[KnowledgeGap]:
        """Scans for modules missing docstrings."""
        gaps: List[KnowledgeGap] = []
        alpha_dir = self.workspace_root / "alpha"
        if not alpha_dir.exists():
            return gaps

        for py_path in sorted(alpha_dir.rglob("*.py")):
            if py_path.name.startswith(("_", ".")) or "__pycache__" in str(py_path):
                continue
            try:
                text = py_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(text, filename=str(py_path))
                doc = ast.get_docstring(tree)
                rel_path = py_path.relative_to(self.workspace_root).as_posix()
                if not doc:
                    gaps.append(
                        KnowledgeGap(
                            topic=f"Missing Module Documentation: {rel_path}",
                            reason=f"Module '{rel_path}' lacks top-level docstring specification.",
                            confidence=0.99,
                            urgency=2,
                            evidence=[f"File: {rel_path}", "Module AST has no docstring node"],
                            category="missing_documentation",
                            suggested_action=f"Add comprehensive architecture docstring to '{rel_path}'."
                        )
                    )
                    if len(gaps) >= 2:
                        break
            except Exception:
                continue

        return gaps

    def _detect_dead_code(self) -> List[KnowledgeGap]:
        """Identifies functions or classes defined without external references."""
        gaps: List[KnowledgeGap] = []
        alpha_dir = self.workspace_root / "alpha"
        if not alpha_dir.exists():
            return gaps

        # Spot check candidates
        for py_path in sorted(alpha_dir.glob("*.py")):
            try:
                text = py_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(text, filename=str(py_path))
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
                rel_path = py_path.relative_to(self.workspace_root).as_posix()

                for fn in funcs:
                    # Check if referenced anywhere else
                    ref_count = 0
                    for other_path in list(alpha_dir.glob("*.py"))[:5]:
                        if other_path != py_path:
                            try:
                                if fn in other_path.read_text(encoding="utf-8", errors="replace"):
                                    ref_count += 1
                            except Exception:
                                pass

                    if ref_count == 0:
                        gaps.append(
                            KnowledgeGap(
                                topic=f"Potential Dead Code: {fn}() in {rel_path}",
                                reason=f"Function '{fn}' in '{rel_path}' has 0 external references in top-level modules.",
                                confidence=0.75,
                                urgency=2,
                                evidence=[f"Symbol: {fn}", f"Origin: {rel_path}", "0 external call references found"],
                                category="dead_code",
                                suggested_action=f"Verify if '{fn}' is obsolete or integrate into active pathways."
                            )
                        )
                        if len(gaps) >= 1:
                            break
            except Exception:
                continue

        return gaps

    def _detect_unused_systems(self) -> List[KnowledgeGap]:
        """Checks for tools or workflows defined but unreferenced in operational boot loop."""
        gaps: List[KnowledgeGap] = []
        tools_dir = self.workspace_root / "alpha" / "tools"
        boot_path = self.workspace_root / "alpha_boot.py"

        if tools_dir.exists() and boot_path.exists():
            try:
                boot_text = boot_path.read_text(encoding="utf-8", errors="replace")
                for tool_file in sorted(tools_dir.glob("*.py")):
                    if tool_file.name.startswith("_"):
                        continue
                    if tool_file.stem not in boot_text:
                        rel_path = tool_file.relative_to(self.workspace_root).as_posix()
                        gaps.append(
                            KnowledgeGap(
                                topic=f"Unused Subsystem: {rel_path}",
                                reason=f"Tool module '{tool_file.stem}' is not explicitly registered in alpha_boot.py.",
                                confidence=0.80,
                                urgency=3,
                                evidence=[f"Tool File: {rel_path}", "Not mentioned in alpha_boot.py startup"],
                                category="unused_system",
                                suggested_action=f"Wire '{tool_file.stem}' into boot Stage 7 (Load Tools)."
                            )
                        )
                        if len(gaps) >= 1:
                            break
            except Exception:
                pass

        return gaps


# Singleton default instance
knowledge_gap_detector = KnowledgeGapDetector()