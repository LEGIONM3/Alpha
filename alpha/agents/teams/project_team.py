"""Dynamic Project Teams: Automatic team formation, collaborative execution, and lifecycle dissolution."""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.agents.core.runtime import AgentRuntime
from alpha.agents.core.base import BaseAgent, AgentRole, AgentStatus
from alpha.agents.communication.context import SharedContextLayer

class TeamMember(BaseModel):
    agent_id: str
    agent_name: str
    agent_role: AgentRole
    is_lead: bool = False

class DynamicTeam:
    """A task-specific collaborative team formed on demand and dissolved upon goal completion."""

    def __init__(
        self,
        name: str,
        mission: str,
        members: List[BaseAgent],
        lead_agent: Optional[BaseAgent],
        parent_context: SharedContextLayer
    ):
        self.team_id = f"team_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.mission = mission
        self.members = members
        self.lead_agent = lead_agent or (members[0] if members else None)
        self.team_context = parent_context.create_child_context(sub_context_id=self.team_id)
        self.status = "FORMED"
        self.created_at = time.time()
        self.execution_results: Dict[str, Any] = {}

    def get_member_by_role(self, role: AgentRole) -> Optional[BaseAgent]:
        for m in self.members:
            if m.role == role:
                return m
        return None

    def execute_workflow(self, workflow_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collaborative pipeline through team members."""
        self.status = "ACTIVE"
        t0 = time.perf_counter()
        pipeline_log = []

        # Step 1: Director / Lead Strategic Framing
        director = self.get_member_by_role(AgentRole.DIRECTOR) or self.lead_agent
        dir_res = director.execute_task({"directive": self.mission, "inputs": workflow_inputs}) if director else {}
        pipeline_log.append({"step": "directive", "output": dir_res})
        self.team_context.set("directive", dir_res, author_id=director.agent_id if director else "lead")

        # Step 2: Architect Blueprint
        architect = self.get_member_by_role(AgentRole.ARCHITECT)
        arch_res = architect.execute_task({"requirements": self.mission}) if architect else {}
        pipeline_log.append({"step": "architecture", "output": arch_res})
        self.team_context.set("architecture", arch_res, author_id=architect.agent_id if architect else "system")

        # Step 3: Planner Decomposition
        planner = self.get_member_by_role(AgentRole.PLANNER)
        plan_res = planner.execute_task({"goal": self.mission, "architecture": arch_res}) if planner else {}
        pipeline_log.append({"step": "plan", "output": plan_res})
        self.team_context.set("plan", plan_res, author_id=planner.agent_id if planner else "system")

        # Step 4: Builder & Coder Construction
        coder = self.get_member_by_role(AgentRole.CODER)
        code_res = coder.execute_task({"spec": self.mission, "target_path": workflow_inputs.get("target_path", "solution.py")}) if coder else {}
        pipeline_log.append({"step": "code", "output": code_res})

        builder = self.get_member_by_role(AgentRole.BUILDER)
        build_res = builder.execute_task({"target": self.name, "components": code_res.get("symbols_defined", [])}) if builder else {}
        pipeline_log.append({"step": "build", "output": build_res})

        # Step 5: Tester Verification
        tester = self.get_member_by_role(AgentRole.TESTER)
        test_res = tester.execute_task({"target_symbol": self.name, "code": code_res.get("code", "")}) if tester else {}
        pipeline_log.append({"step": "tests", "output": test_res})

        # Step 6: Validator Final Sign-off
        validator = self.get_member_by_role(AgentRole.VALIDATOR)
        val_res = validator.execute_task({"artifact": code_res, "required_keys": ["code", "symbols_defined"]}) if validator else {}
        pipeline_log.append({"step": "validation", "output": val_res})

        all_successful = bool(val_res.get("is_valid", True)) and bool(test_res.get("all_passed", True))
        duration_ms = max(0.01, (time.perf_counter() - t0) * 1000.0)

        self.execution_results = {
            "team_id": self.team_id,
            "mission": self.mission,
            "success": all_successful,
            "steps_executed": len(pipeline_log),
            "pipeline_log": pipeline_log,
            "final_code": code_res.get("code"),
            "tests_passed": test_res.get("tests_passed", 0),
            "duration_ms": duration_ms
        }
        self.status = "COMPLETED"
        return self.execution_results

    def dissolve(self) -> Dict[str, Any]:
        """Dissolve the dynamic team, freeing members and archiving state."""
        self.status = "DISSOLVED"
        summary = {
            "team_id": self.team_id,
            "name": self.name,
            "members_released": len(self.members),
            "status": self.status,
            "dissolved_at": time.time()
        }
        return summary


class TeamManager:
    """Orchestrates dynamic team formation, mission dispatch, and dissolution."""

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.active_teams: Dict[str, DynamicTeam] = {}

    def form_coding_team(self, task_name: str, mission_goal: str) -> DynamicTeam:
        """Automatically form dynamic team for complex coding projects."""
        roles = [
            AgentRole.DIRECTOR,
            AgentRole.ARCHITECT,
            AgentRole.PLANNER,
            AgentRole.BUILDER,
            AgentRole.CODER,
            AgentRole.TESTER,
            AgentRole.VALIDATOR
        ]
        members: List[BaseAgent] = []
        for r in roles:
            agent = self.runtime.scheduler.select_agent(role=r)
            if not agent:
                # If no idle agent exists, spawn one dynamically
                from alpha.agents.types import ROLE_TO_CLASS_MAP
                cls = ROLE_TO_CLASS_MAP.get(r)
                if cls:
                    agent = self.runtime.lifecycle.spawn(cls, name=f"Dynamic_{r.value.title()}", role=r)
            if agent:
                members.append(agent)

        director = next((m for m in members if m.role == AgentRole.DIRECTOR), members[0] if members else None)
        team = DynamicTeam(
            name=task_name,
            mission=mission_goal,
            members=members,
            lead_agent=director,
            parent_context=self.runtime.shared_context
        )
        self.active_teams[team.team_id] = team
        return team

    def dissolve_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Dissolve a team and remove from active list."""
        team = self.active_teams.pop(team_id, None)
        if team:
            return team.dissolve()
        return None
