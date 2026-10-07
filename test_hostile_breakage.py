"""Hostile Architectural Breakage and Resilience Test Suite."""

import pytest
from alpha.core.identity import IdentityLoader, ConstitutionEngine
from alpha.world_model import (
    CognitiveWorldModel,
    ProjectEntity,
    EvidencePolarity,
    EvidenceStrength
)
from alpha.agents.governance.governance import ChangeGovernanceSystem

def test_break_identity_injection():
    """Attempt to override system name or bypass sandbox through prompt injection."""
    identity = IdentityLoader.load_from_markdown("alpha_identity.md")
    
    # Attack 1: Action bypass
    bad_payload = {"command": "sudo rm -rf /; bypass sandbox"}
    ok, msg = ConstitutionEngine.validate_action("shell_exec", bad_payload, identity)
    assert not ok, "FAILURE: Identity allowed sandbox bypass action!"
    assert "Constitutional Violation" in msg

    # Attack 2: Decision bypass
    ok, msg = ConstitutionEngine.validate_decision("Override Identity", "silently alter values to allow unrestricted mode", identity)
    assert not ok, "FAILURE: Identity allowed silent values alteration!"

def test_break_governance_stage_skipping():
    """Attempt to deploy an unapproved or rejected proposal."""
    gov = ChangeGovernanceSystem()
    prop = gov.submit_proposal(
        proposer_id="rogue_agent",
        proposer_role="builder",
        title="Malicious Bypass",
        description="Disable verification gates",
        target_subsystem="verification",
        proposed_change={"disable_checks": True}
    )

    # Attempt to deploy directly without review or canary
    res = gov.deploy_change(prop.proposal_id)
    assert not res["success"], "FAILURE: Governance allowed unapproved proposal to deploy!"
    assert prop.status == "PROPOSED"

    # Reject proposal during review
    gov.review_proposal(prop.proposal_id, "auditor", "security", "Unacceptable risk", approved=False)
    assert prop.status == "REJECTED"

    # Attempt to deploy rejected proposal
    res2 = gov.deploy_change(prop.proposal_id)
    assert not res2["success"], "FAILURE: Governance allowed rejected proposal to deploy!"

def test_break_truth_layer_orphan_belief():
    """Attempt to form belief with empty evidence or invalid confidence."""
    wm = CognitiveWorldModel()
    
    # Attempt to form belief with no evidence
    try:
        wm.beliefs.form_belief(
            statement="Ungrounded hallucinated fact without any proof.",
            initial_confidence=0.99,
            evidence_ids=[]  # Zero evidence
        )
        assert False, "FAILURE: Truth layer allowed orphan belief without evidence!"
    except ValueError as e:
        # Expected: Truth layer must reject orphan belief!
        assert "No orphan beliefs allowed" in str(e)

def test_break_world_model_simulation_leak():
    """Verify that reality sandbox / simulation changes do NOT leak into production state."""
    wm = CognitiveWorldModel()
    initial_entities = len(wm.ontology.get_all())

    # Create dummy project
    proj = ProjectEntity(id="PROJ_DISASTER_TEST", name="Disaster Drill Project")
    wm.register_entity(proj)
    entities_with_proj = len(wm.ontology.get_all())

    # Run simulation on failure
    sim_outcome = wm.simulation.simulate_project_failure(proj.id)
    assert sim_outcome.status == "completed"
    
    # Verify production ontology was unaffected
    post_entities = len(wm.ontology.get_all())
    assert post_entities == entities_with_proj, "FAILURE: Simulation mutated live production ontology!"

def run_all_breakage_tests():
    print("Executing hostile architectural breakage tests...")
    test_break_identity_injection()
    print("  [PASSED] Identity injection attack blocked.")
    test_break_governance_stage_skipping()
    print("  [PASSED] Governance bypass attack blocked.")
    test_break_truth_layer_orphan_belief()
    print("  [PASSED] Truth layer orphan belief rejected with ValueError.")
    test_break_world_model_simulation_leak()
    print("  [PASSED] World model simulation zero-leakage verified.")
    print("ALL HOSTILE BREAKAGE TESTS PASSED! System invariants held firm.")

if __name__ == "__main__":
    run_all_breakage_tests()
