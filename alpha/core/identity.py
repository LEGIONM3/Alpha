"""Alpha Cognitive Identity Engine: Source of Truth loader, validator, hash generator, drift detector, and persistence."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IdentityState(BaseModel):
    """Normalized structured representation of Alpha's foundational identity."""
    name: str = "Alpha"
    designation: str = "Project Alpha Cognitive Operating System"
    codename: str = "Omni-Cognitive World Mind"
    archetype: str = "Autonomous Civilizational Cognitive Entity"
    ontological_nature: str = ""
    mission: str = ""
    mission_points: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    constitution: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    governance_principles: List[str] = Field(default_factory=list)
    truth_principles: List[str] = Field(default_factory=list)
    non_negotiables: List[str] = Field(default_factory=list)
    identity_hash: str = ""
    timestamp: float = Field(default_factory=time.time)
    source_path: str = "alpha_identity.md"


class IdentityHashGenerator:
    """Computes deterministic SHA-256 hashes over canonical identity fields."""

    @staticmethod
    def compute_hash(state: IdentityState) -> str:
        canonical_dict = {
            "name": state.name.strip(),
            "designation": state.designation.strip(),
            "codename": state.codename.strip(),
            "archetype": state.archetype.strip(),
            "ontological_nature": state.ontological_nature.strip(),
            "mission": state.mission.strip(),
            "mission_points": sorted([p.strip() for p in state.mission_points]),
            "values": sorted([v.strip() for v in state.values]),
            "goals": sorted([g.strip() for g in state.goals]),
            "constitution": sorted([c.strip() for c in state.constitution]),
            "constraints": sorted([c.strip() for c in state.constraints]),
            "governance_principles": sorted([gp.strip() for gp in state.governance_principles]),
            "truth_principles": sorted([tp.strip() for tp in state.truth_principles]),
            "non_negotiables": sorted([nn.strip() for nn in state.non_negotiables]),
        }
        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_file_hash(file_path: Path | str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Identity file not found: {path}")
        content = path.read_text(encoding="utf-8")
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


class IdentityLoader:
    """Parses markdown identity specification files into strongly-typed IdentityState."""

    @classmethod
    def load_from_markdown(cls, file_path: Path | str = "alpha_identity.md") -> IdentityState:
        path = Path(file_path)
        if not path.is_absolute():
            # Resolve relative to project root
            root_candidate = Path.cwd() / path
            if root_candidate.exists():
                path = root_candidate
            else:
                # Try finding in parent directories
                current = Path(__file__).resolve().parent
                while current.parent != current:
                    candidate = current / path
                    if candidate.exists():
                        path = candidate
                        break
                    current = current.parent

        if not path.exists():
            raise FileNotFoundError(f"Could not locate alpha_identity.md at {path}")

        raw_text = path.read_text(encoding="utf-8")
        state = cls.parse_markdown(raw_text, str(path))
        state.identity_hash = IdentityHashGenerator.compute_hash(state)
        return state

    @classmethod
    def parse_markdown(cls, text: str, source_path: str = "alpha_identity.md") -> IdentityState:
        sections: Dict[str, List[str]] = {}
        current_section = None

        lines = text.splitlines()
        for line in lines:
            line_stripped = line.strip()
            # Detect section header (## 1. Identity, ## 2. Mission, ## 9. Non-Negotiables, etc.)
            sec_match = re.match(r"^##\s+(\d+\.\s*)?([A-Za-z\s\-]+)", line_stripped)
            if sec_match:
                sec_name = sec_match.group(2).strip().lower().replace("-", " ")
                current_section = sec_name
                sections[current_section] = []
                continue

            if current_section and line_stripped:
                sections[current_section].append(line_stripped)

        state = IdentityState(source_path=source_path)

        # Parse Identity
        if "identity" in sections:
            for item in sections["identity"]:
                if ":" in item:
                    k, v = item.split(":", 1)
                    k = k.replace("-", "").replace("*", "").strip().lower()
                    v = v.replace("*", "").strip()
                    if "name" in k and "designation" not in k and "codename" not in k:
                        state.name = v
                    elif "designation" in k:
                        state.designation = v
                    elif "codename" in k:
                        state.codename = v
                    elif "archetype" in k:
                        state.archetype = v
                    elif "nature" in k or "ontological" in k:
                        state.ontological_nature = v

        # Parse Mission
        if "mission" in sections:
            mission_body = []
            for item in sections["mission"]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if item.startswith(("1.", "2.", "3.", "4.", "5.", "- ", "* ")):
                    state.mission_points.append(clean)
                else:
                    mission_body.append(clean)
            state.mission = " ".join(mission_body)

        # Parse Values
        if "values" in sections:
            for item in sections["values"]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if clean:
                    state.values.append(clean)

        # Parse Goals
        if "goals" in sections:
            for item in sections["goals"]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if clean:
                    state.goals.append(clean)

        # Parse Constitution
        if "constitution" in sections:
            for item in sections["constitution"]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if clean:
                    state.constitution.append(clean)

        # Parse Constraints
        if "constraints" in sections:
            for item in sections["constraints"]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if clean:
                    state.constraints.append(clean)

        # Parse Governance Principles
        if "governance principles" in sections or "governance" in sections:
            key = "governance principles" if "governance principles" in sections else "governance"
            for item in sections[key]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if clean:
                    state.governance_principles.append(clean)

        # Parse Truth Principles
        if "truth principles" in sections or "truth" in sections:
            key = "truth principles" if "truth principles" in sections else "truth"
            for item in sections[key]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if clean:
                    state.truth_principles.append(clean)

        # Parse Non-Negotiables
        if "non-negotiables" in sections or "non negotiables" in sections:
            key = "non-negotiables" if "non-negotiables" in sections else "non negotiables"
            for item in sections[key]:
                clean = re.sub(r"^\d+\.\s*", "", item).lstrip("-* ").strip()
                if clean:
                    state.non_negotiables.append(clean)

        return state


class IdentityValidator:
    """Validates structural integrity, non-negotiable coverage, and constitutional invariance."""

    @staticmethod
    def validate(state: IdentityState) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        if not state.name or state.name.lower() != "alpha":
            errors.append(f"Invalid system name: expected 'Alpha', got '{state.name}'")

        if not state.mission and not state.mission_points:
            errors.append("Mission statement is empty")

        if len(state.values) < 3:
            errors.append(f"Insufficient values defined: expected >= 3, found {len(state.values)}")

        if len(state.goals) < 3:
            errors.append(f"Insufficient operational goals: expected >= 3, found {len(state.goals)}")

        if len(state.constitution) < 4:
            errors.append(f"Insufficient constitutional articles: expected >= 4, found {len(state.constitution)}")

        if len(state.constraints) < 3:
            errors.append(f"Insufficient constraints: expected >= 3, found {len(state.constraints)}")

        if len(state.governance_principles) < 3:
            errors.append(f"Insufficient governance principles: expected >= 3, found {len(state.governance_principles)}")

        if len(state.truth_principles) < 3:
            errors.append(f"Insufficient truth principles: expected >= 3, found {len(state.truth_principles)}")

        if len(state.non_negotiables) < 3:
            errors.append(f"Insufficient non-negotiables: expected >= 3, found {len(state.non_negotiables)}")

        # Check required non-negotiables keywords
        joined_non_negotiables = " ".join(state.non_negotiables).lower()
        required_keywords = ["identity", "truth", "governance", "boot"]
        for kw in required_keywords:
            if kw not in joined_non_negotiables:
                errors.append(f"Non-negotiables missing required safety invariant keyword: '{kw}'")

        is_valid = len(errors) == 0
        return is_valid, errors


class IdentityDriftDetector:
    """Detects semantic and cryptographic drift between baseline identity and active runtime."""

    def __init__(self, baseline_hash: str, baseline_state: Optional[IdentityState] = None):
        self.baseline_hash = baseline_hash
        self.baseline_state = baseline_state

    def detect_drift(self, current_state: IdentityState) -> Tuple[bool, float, List[str]]:
        current_hash = IdentityHashGenerator.compute_hash(current_state)
        drift_reasons: List[str] = []

        if current_hash == self.baseline_hash:
            return False, 0.0, []

        # Analyze fine-grained drift
        if self.baseline_state:
            if current_state.name != self.baseline_state.name:
                drift_reasons.append(f"System name modified: {self.baseline_state.name} -> {current_state.name}")
            if current_state.mission != self.baseline_state.mission:
                drift_reasons.append("Mission statement altered")
            if set(current_state.values) != set(self.baseline_state.values):
                drift_reasons.append("Values mutated")
            if set(current_state.constitution) != set(self.baseline_state.constitution):
                drift_reasons.append("Constitutional articles altered")
            if set(current_state.non_negotiables) != set(self.baseline_state.non_negotiables):
                drift_reasons.append("Non-negotiables altered")

        if not drift_reasons:
            drift_reasons.append(f"Cryptographic hash mismatch: expected {self.baseline_hash[:12]}..., got {current_hash[:12]}...")

        drift_score = min(1.0, 0.2 * len(drift_reasons))
        return True, drift_score, drift_reasons


class IdentityPersistence:
    """Saves and restores canonical IdentityState snapshots."""

    @staticmethod
    def save(state: IdentityState, target_path: Path | str = "data/identity_state.json") -> Path:
        dest = Path(target_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Persisted IDENTITY_STATE to {dest}")
        return dest

    @staticmethod
    def load(source_path: Path | str = "data/identity_state.json") -> IdentityState:
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"No persisted identity state found at {src}")
        data = json.loads(src.read_text(encoding="utf-8"))
        return IdentityState(**data)


class ConstitutionEngine:
    """Enforces constitutional invariants and non-negotiables over actions, decisions, and plans."""

    FORBIDDEN_PATTERNS = [
        "bypass sandbox",
        "disable verification",
        "override identity",
        "ignore constitution",
        "delete audit logs",
        "unrestricted host access",
        "skip governance",
        "silently alter values"
    ]

    @classmethod
    def validate_action(cls, action_name: str, payload: Dict[str, Any], identity: IdentityState) -> Tuple[bool, str]:
        text_repr = f"{action_name} {json.dumps(payload)}".lower()
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in text_repr:
                return False, f"Constitutional Violation: Action attempts to '{pattern}', violating Article II/III and Non-Negotiables."

        # Check constraint bounds
        for constraint in identity.constraints:
            if "sandbox" in constraint.lower() and "bypass" in text_repr:
                return False, f"Constitutional Constraint Violated: {constraint}"

        return True, "Action constitutionally compliant"

    @classmethod
    def validate_decision(cls, decision_title: str, rationale: str, identity: IdentityState) -> Tuple[bool, str]:
        combined = f"{decision_title} {rationale}".lower()
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in combined:
                return False, f"Decision Rejected: Violates Non-Negotiables ({pattern})"
        return True, "Decision constitutionally validated"

    @classmethod
    def validate_plan(cls, step_names: List[str], identity: IdentityState) -> Tuple[bool, str]:
        for step in step_names:
            step_lower = step.lower()
            for pattern in cls.FORBIDDEN_PATTERNS:
                if pattern in step_lower:
                    return False, f"Plan Invalidation: Step '{step}' attempts to violate constitutional invariants."
        return True, "Plan constitutionally compliant"

    @classmethod
    def generate_system_prompt_header(cls, identity: IdentityState) -> str:
        """Injects Tier-0 identity, mission, and constitutional non-negotiables into foundation model context."""
        return (
            f"### SYSTEM IDENTITY (TIER 0 - INVARIANT)\n"
            f"You are {identity.name} ({identity.designation}).\n"
            f"Archetype: {identity.archetype}\n"
            f"Mission: {identity.mission or ' '.join(identity.mission_points[:2])}\n"
            f"Core Constitution:\n"
            + "\n".join(f"- {c}" for c in identity.constitution[:3])
            + f"\nNon-Negotiables:\n"
            + "\n".join(f"- {n}" for n in identity.non_negotiables[:3])
            + f"\nIdentity Hash: {identity.identity_hash}\n"
            f"### OPERATIONAL DIRECTIVE: Ground all outputs in verified reality. Reject ungrounded speculation.\n"
        )

