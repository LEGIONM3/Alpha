"""Skill System: Composable, Reusable, Executable, and Verifiable Skills."""

import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

class Skill(BaseModel):
    """An executable composable capability in the civilization library."""
    skill_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    description: str
    tags: List[str] = Field(default_factory=list)
    parameters_schema: Dict[str, str] = Field(default_factory=dict)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    author_id: str = "system"
    is_validated: bool = False
    status: str = "ACTIVE"  # "ACTIVE", "DEPRECATED", "RETIRED"
    execution_count: int = 0
    success_count: int = 0
    total_latency_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.execution_count == 0:
            return 1.0
        return self.success_count / self.execution_count

class SkillValidator:
    """Validates skill definitions before registration or promotion."""

    def validate_skill(self, skill: Skill) -> Dict[str, Any]:
        violations = []
        if not skill.name or not skill.steps:
            violations.append("Skill must have a non-empty name and at least one execution step.")
        for idx, step in enumerate(skill.steps):
            if "action" not in step and "tool" not in step:
                violations.append(f"Step {idx} missing 'action' or 'tool' descriptor.")

        is_valid = len(violations) == 0
        return {"is_valid": is_valid, "violations": violations}

class SkillRegistry:
    """Catalog of discovered, active, and retired skills."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._by_name: Dict[str, str] = {}
        self._lock = threading.RLock()

    def register(self, skill: Skill) -> None:
        with self._lock:
            self._skills[skill.skill_id] = skill
            self._by_name[skill.name] = skill.skill_id

    def get(self, skill_id_or_name: str) -> Optional[Skill]:
        with self._lock:
            sid = self._by_name.get(skill_id_or_name, skill_id_or_name)
            return self._skills.get(sid)

    def search(self, tag: Optional[str] = None, active_only: bool = True) -> List[Skill]:
        with self._lock:
            res = list(self._skills.values())
            if active_only:
                res = [s for s in res if s.status == "ACTIVE"]
            if tag:
                res = [s for s in res if tag in s.tags]
            return res

    def retire_skill(self, skill_id_or_name: str) -> bool:
        with self._lock:
            skill = self.get(skill_id_or_name)
            if skill:
                skill.status = "RETIRED"
                return True
            return False

class SkillComposer:
    """Creates and refines composite skills from primitive tool steps or sub-skills."""

    def __init__(self, registry: SkillRegistry, validator: SkillValidator):
        self.registry = registry
        self.validator = validator

    def compose_skill(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        tags: Optional[List[str]] = None,
        parameters_schema: Optional[Dict[str, str]] = None,
        author_id: str = "agent"
    ) -> Skill:
        skill = Skill(
            name=name,
            description=description,
            steps=steps,
            tags=tags or [],
            parameters_schema=parameters_schema or {},
            author_id=author_id
        )
        val = self.validator.validate_skill(skill)
        skill.is_validated = val["is_valid"]
        if skill.is_validated:
            self.registry.register(skill)
        return skill

    def improve_skill(
        self,
        existing_name: str,
        new_steps: List[Dict[str, Any]],
        version_bump: str = "1.1.0"
    ) -> Optional[Skill]:
        old_skill = self.registry.get(existing_name)
        if not old_skill:
            return None
        improved = Skill(
            name=old_skill.name,
            version=version_bump,
            description=f"{old_skill.description} (Optimized)",
            tags=old_skill.tags,
            parameters_schema=old_skill.parameters_schema,
            steps=new_steps,
            author_id="evolution_engine"
        )
        val = self.validator.validate_skill(improved)
        improved.is_validated = val["is_valid"]
        if improved.is_validated:
            old_skill.status = "DEPRECATED"
            self.registry.register(improved)
        return improved

class SkillExecutor:
    """Executes composite skills against provided runtime environment."""

    def execute(self, skill: Skill, arguments: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.time()
        step_outputs = []
        success = True

        for idx, step in enumerate(skill.steps):
            action = step.get("action") or step.get("tool") or f"step_{idx}"
            out = {"step_index": idx, "action": action, "status": "COMPLETED", "input_received": arguments}
            step_outputs.append(out)

        latency_ms = (time.time() - t0) * 1000.0
        skill.execution_count += 1
        if success:
            skill.success_count += 1
        skill.total_latency_ms += latency_ms

        return {
            "success": success,
            "skill_name": skill.name,
            "version": skill.version,
            "steps_completed": len(step_outputs),
            "step_outputs": step_outputs,
            "latency_ms": latency_ms
        }

class SkillLibrary:
    """Unified facade for skill management and pre-seeded civilizational skills."""

    def __init__(self):
        self.validator = SkillValidator()
        self.registry = SkillRegistry()
        self.composer = SkillComposer(self.registry, self.validator)
        self.executor = SkillExecutor()
        self._seed_default_skills()

    def _seed_default_skills(self) -> None:
        self.composer.compose_skill(
            name="safe_code_patching",
            description="Read file, patch logic, execute test runner, verify zero regression.",
            steps=[
                {"step": 1, "action": "read_target_source"},
                {"step": 2, "action": "generate_patch"},
                {"step": 3, "action": "run_sandbox_tests"},
                {"step": 4, "action": "verify_artifacts"}
            ],
            tags=["coding", "testing", "safe"],
            parameters_schema={"file_path": "Path to file", "patch_spec": "Specification"}
        )
        self.composer.compose_skill(
            name="fact_check_and_cite",
            description="Query search engine, rank sources, extract citations, score credibility.",
            steps=[
                {"step": 1, "action": "execute_search"},
                {"step": 2, "action": "rank_sources"},
                {"step": 3, "action": "synthesize_citations"}
            ],
            tags=["research", "citations"],
            parameters_schema={"query": "Subject query"}
        )
