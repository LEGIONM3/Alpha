"""World Model Validation Script: Entity, Belief, Relationship, Goal, Capability, Risk creation and queries."""

import json
import time
from alpha.world_model import (
    CognitiveWorldModel,
    EntityType,
    RelationType,
    GoalEntity,
    CapabilityEntity,
    RiskEntity,
    AgentEntity,
    ToolEntity,
    BeliefEntity,
    EvidencePolarity,
    EvidenceStrength
)

def validate_world_model():
    print("Initializing CognitiveWorldModel...")
    wm = CognitiveWorldModel()

    # 1. Goal creation
    goal = GoalEntity(
        id="GOAL_BOOT_01",
        name="Establish Cognitive Boot State",
        objective="Ensure all cognitive subsystems boot cleanly with local foundation model",
        importance=1.0,
        confidence=1.0
    )
    wm.register_entity(goal)
    print(f"Goal created: {goal.id} ({goal.name})")

    # 2. Capability creation
    cap = CapabilityEntity(
        id="CAP_MODEL_REASONING",
        name="Foundation Model Reasoning",
        description="Local inference via gemma-4-e4b-it-ultra-uncensored-heretic at localhost:1234",
        importance=0.95
    )
    wm.register_entity(cap)
    print(f"Capability created: {cap.id} ({cap.name})")

    # 3. Risk creation
    risk = RiskEntity(
        id="RISK_TIMEOUT_DROP",
        name="Model Inference Timeout Risk",
        description="Premature socket closure on long thinking chains",
        severity=0.7,
        likelihood=0.1
    )
    wm.register_entity(risk)
    print(f"Risk created: {risk.id} ({risk.name})")

    # 4. Agent & Tool creation
    agent = AgentEntity(
        id="AGENT_SYSTEM_ENG",
        name="Chief Systems Engineer",
        role="systems_engineer",
        importance=0.9
    )
    wm.register_entity(agent)

    tool = ToolEntity(
        id="TOOL_SANDBOX_EXEC",
        name="SecureExecutionSandbox",
        description="Python code runner in isolated environment",
        importance=0.9
    )
    wm.register_entity(tool)

    # 5. Relationship creation
    r1 = wm.relate(agent.id, tool.id, RelationType.USES, weight=0.9)
    r2 = wm.relate(agent.id, cap.id, RelationType.USES, weight=0.95)
    r3 = wm.relate(cap.id, goal.id, RelationType.SUPPORTS, weight=1.0)
    r4 = wm.relate(risk.id, cap.id, RelationType.CONTRADICTS, weight=0.8)
    print(f"Created 4 relationships across entities.")

    # 6. Belief & Evidence creation (No orphan beliefs)
    ev = wm.record_evidence(
        statement="125/125 successful live inferences benchmarked against local endpoint",
        polarity=EvidencePolarity.SUPPORTING,
        strength=EvidenceStrength.STRONG,
        source_id="benchmark://data/benchmark_125_results.json"
    )

    belief = wm.form_belief(
        statement="Local model gemma-4-e4b supports real-time multi-threaded cognitive inference",
        initial_confidence=0.95,
        evidence_ids=[ev.evidence_id],
        domain="foundation_model"
    )
    print(f"Formed verified belief: '{belief.statement[:60]}...' with confidence {belief.confidence}")

    # 7. Real Queries
    # Entity query
    retrieved_goal = wm.ontology.get(goal.id)
    assert retrieved_goal is not None and retrieved_goal.name == goal.name
    print("Entity query: VERIFIED")

    # Graph path query
    paths = wm.graph_query.find_all_paths(agent.id, goal.id, cutoff=4)
    assert len(paths) > 0, "No path found between Agent and Goal!"
    print(f"Graph path query: VERIFIED (Found path: {' -> '.join(paths[0])})")

    # Belief query
    active_beliefs = wm.beliefs.get_active_beliefs(min_confidence=0.5)
    assert any(b.belief_id == belief.belief_id for b in active_beliefs)
    print(f"Belief query: VERIFIED ({len(active_beliefs)} active beliefs found)")

    # 8. World State Snapshot & Persistence
    snapshot = wm.world_state.get_current_state()
    summary = snapshot.summary()
    assert summary["goal_count"] >= 1
    assert summary["belief_count"] >= 1
    print(f"World State Snapshot captured: {snapshot.state_id} (Summary: {summary})")

    # Serialize snapshot to data/world_state_bootstrap.json
    snapshot_dict = snapshot.model_dump()
    with open("data/world_state_bootstrap.json", "w", encoding="utf-8") as f:
        json.dump(snapshot_dict, f, indent=2)
    print("World State persisted to data/world_state_bootstrap.json")

    # Introspection query
    intro = wm.self_model.introspect()
    print("\nSelf-Model Introspection:")
    print(f"  Who am I: {intro.who_am_i}")
    print(f"  What can I do: {intro.what_can_i_do[:3]}")
    print(f"  Active goals: {len(intro.what_are_my_goals)}")
    print(f"  Beliefs: {len(intro.what_do_i_believe)}")

    print("\nALL WORLD MODEL OPERATIONS VERIFIED WITH 100% SUCCESS!")
    return True

if __name__ == "__main__":
    validate_world_model()
