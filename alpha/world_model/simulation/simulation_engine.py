"""World Simulation Engine: Reality Sandbox and Multi-Scenario Simulators.

Part 13: World Simulation Engine
Capabilities:
- Future Simulation
- Project Simulation ("If Project X fails, what happens?")
- Risk Simulation
- Strategy Simulation (Plan A vs Plan B)
- Belief Simulation ("If Belief B is falsified, what collapses?")
- Counterfactual Simulation ("If Agent Y is removed, what happens?")
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from alpha.world_model.state.world_state import WorldStateEngine, WorldStateSnapshot
from alpha.world_model.causal.engine import CausalReasoningEngine
from alpha.world_model.ontology.registry import OntologyRegistry
from alpha.world_model.ontology.entities import EntityType, LifecycleState


class SimulationOutcome(BaseModel):
    """Result of running a simulation scenario within the reality sandbox."""
    simulation_id: str
    scenario_type: str
    target_intervention: str
    status: str = "completed"
    cascade_depth: int = 1
    affected_entities: List[Dict[str, Any]] = Field(default_factory=list)
    projected_risk_score: float = 0.5
    counterfactual_delta: Dict[str, Any] = Field(default_factory=dict)
    narrative_summary: str = ""


class WorldSimulationEngine:
    """Reality Sandbox for testing interventions, failures, and policy changes without affecting live state."""

    def __init__(
        self,
        world_state_engine: WorldStateEngine,
        causal_engine: CausalReasoningEngine,
        ontology: OntologyRegistry
    ):
        self.world_state = world_state_engine
        self.causal = causal_engine
        self.ontology = ontology

    def simulate_project_failure(self, project_id: str) -> SimulationOutcome:
        """Simulate: 'If Project X fails, what happens?'"""
        # 1. Fork simulated state
        sim_state = self.world_state.fork_simulated_state(
            simulation_id=f"sim_proj_fail_{project_id}",
            mutations={"fail_project_id": project_id}
        )

        # 2. Causal impact prediction
        impact = self.causal.predict_change_impact(project_id, severity=1.0)

        # 3. Find connected tasks and goals in ontology
        proj = self.ontology.get(project_id)
        proj_name = proj.name if proj else project_id
        tasks = self.ontology.get_by_type(EntityType.TASK)
        impacted_tasks = [t for t in tasks if getattr(t, "assignee_id", "") == project_id or project_id in getattr(t, "dependency_ids", [])]

        affected = [
            {"entity_id": t.id, "name": t.name, "type": "task", "impact": "blocked_or_cancelled"}
            for t in impacted_tasks
        ]
        for aff in impact.get("affected_nodes", []):
            affected.append({"entity_id": aff["node_id"], "name": f"Node_{aff['node_id'][:6]}", "type": "downstream", "impact": aff["predicted_severity"]})

        return SimulationOutcome(
            simulation_id=f"sim_proj_fail_{project_id}",
            scenario_type="project_failure",
            target_intervention=f"Failure of Project '{proj_name}'",
            cascade_depth=impact.get("blast_radius", 1),
            affected_entities=affected,
            projected_risk_score=min(1.0, 0.4 + len(affected) * 0.15),
            counterfactual_delta={
                "failed_project": project_id,
                "stalled_tasks_count": len(impacted_tasks),
                "total_blast_radius": impact.get("blast_radius", 0)
            },
            narrative_summary=(
                f"Simulated failure of project '{proj_name}' blocks {len(impacted_tasks)} active tasks "
                f"and triggers a downstream blast radius of {impact.get('blast_radius', 0)} causal nodes."
            )
        )

    def simulate_agent_removal(self, agent_id: str) -> SimulationOutcome:
        """Simulate: 'If Agent Y is removed, what happens?'"""
        sim_state = self.world_state.fork_simulated_state(
            simulation_id=f"sim_remove_agent_{agent_id}",
            mutations={"remove_agent_id": agent_id}
        )

        agent = self.ontology.get(agent_id)
        agent_name = agent.name if agent else agent_id
        role = getattr(agent, "role", "unknown") if agent else "unknown"

        # Check tasks assigned to agent
        tasks = self.ontology.get_by_type(EntityType.TASK)
        orphaned_tasks = [t for t in tasks if getattr(t, "assignee_id", "") == agent_id]

        affected = [
            {"entity_id": t.id, "name": t.name, "type": "task", "impact": "unassigned_orphaned"}
            for t in orphaned_tasks
        ]

        return SimulationOutcome(
            simulation_id=f"sim_remove_agent_{agent_id}",
            scenario_type="agent_removal",
            target_intervention=f"Removal of Agent '{agent_name}' ({role})",
            cascade_depth=2,
            affected_entities=affected,
            projected_risk_score=0.35 if not orphaned_tasks else 0.75,
            counterfactual_delta={
                "removed_agent": agent_id,
                "orphaned_tasks": len(orphaned_tasks),
                "workforce_capacity_drop": 0.055
            },
            narrative_summary=(
                f"Removing Agent '{agent_name}' leaves {len(orphaned_tasks)} tasks unassigned. "
                f"Workforce rebalancing required for role '{role}'."
            )
        )

    def simulate_belief_falsification(self, belief_id: str) -> SimulationOutcome:
        """Simulate: 'If Belief B is falsified, what happens?'"""
        # Discover dependent beliefs and hypotheses
        rules = self.ontology.get_by_type(EntityType.RULE)
        hypotheses = self.ontology.get_by_type(EntityType.HYPOTHESIS)

        affected = []
        for r in rules:
            if belief_id in r.metadata.get("supporting_beliefs", []):
                affected.append({"entity_id": r.id, "name": r.name, "type": "rule", "impact": "invalidated"})

        for h in hypotheses:
            if belief_id in getattr(h, "premise", ""):
                affected.append({"entity_id": h.id, "name": h.name, "type": "hypothesis", "impact": "refuted"})

        return SimulationOutcome(
            simulation_id=f"sim_falsify_belief_{belief_id}",
            scenario_type="belief_falsification",
            target_intervention=f"Refutation of belief {belief_id}",
            cascade_depth=2,
            affected_entities=affected,
            projected_risk_score=0.45,
            counterfactual_delta={
                "falsified_belief_id": belief_id,
                "invalidated_rules": len(affected)
            },
            narrative_summary=f"Falsifying belief {belief_id} immediately invalidates {len(affected)} dependent operational rules and hypotheses."
        )

    def simulate_strategy_comparison(
        self,
        strategy_a: Dict[str, Any],
        strategy_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate Plan A vs Plan B across cost, latency, and success metrics."""
        score_a = (strategy_a.get("success_prob", 0.8) * 0.6) - (strategy_a.get("cost", 50) * 0.002)
        score_b = (strategy_b.get("success_prob", 0.9) * 0.6) - (strategy_b.get("cost", 80) * 0.002)

        winner = "strategy_a" if score_a >= score_b else "strategy_b"
        return {
            "strategy_a_score": round(score_a, 3),
            "strategy_b_score": round(score_b, 3),
            "recommended_strategy": winner,
            "rationale": f"Strategy {winner.replace('_', ' ').title()} exhibits superior utility-to-cost ratio."
        }
