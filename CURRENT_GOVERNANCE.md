# CURRENT_GOVERNANCE.md
## Constitutional Governance & Change Management Architecture

**Authored by:** Chief Systems Engineer  
**Subsystems:** `alpha/core/identity.py`, `alpha/agents/governance/governance.py`  
**Date:** October 2026  

---

### 1. The Separation of Powers Principle

In Project Alpha, **no agent may modify itself, its tools, its permissions, or system state directly**. All architectural mutations, skill upgrades, and configuration changes must navigate the six-stage governance gate managed by `ChangeGovernanceSystem`.

```
[1. Proposal] -> [2. Multi-Agent Review] -> [3. Canary Simulation] -> [4. Executive Approval] -> [5. Deployment] -> [6. Rollback Guarantee]
```

---

### 2. The Six Governance Stages

1. **Stage 1 (Proposal Submission):**
   - The proposing agent submits a formal `GovernanceProposal` specifying `proposer_id`, `role`, `title`, `description`, `target_subsystem`, and exact `proposed_change` dictionary.
   - Status transitions to `PROPOSED`.
2. **Stage 2 (Multi-Agent Peer Review):**
   - Independent reviewing agents (e.g. `SecurityAgent`, `RiskAgent`, `ArchitectAgent`) evaluate the proposal against constitutional constraints and non-negotiables.
   - Requires explicit comments and approval flag. If rejected, status becomes `REJECTED`. If approved, transitions to `REVIEWED`.
3. **Stage 3 (Canary Simulation in Isolated Sandbox):**
   - The proposed mutation is executed inside `VirtualSandboxWorld` or a simulation branch with a verification test runner callable.
   - If sandbox errors occur or tests fail, status becomes `REJECTED`. If successful, transitions to `TESTED_CANARY`.
4. **Stage 4 (Executive Director Approval):**
   - The executive authority (`DirectorAgent`) reviews canary test results and grants final sign-off.
   - Transitions to `APPROVED`.
5. **Stage 5 (Deployment with Rollback Snapshot):**
   - Captures an immutable pre-deployment snapshot of the target subsystem (`rollback_snapshot`).
   - Applies the mutation to active configurations and marks status `DEPLOYED`.
6. **Stage 6 (Instant Reversibility / Rollback):**
   - If telemetry, the `SystemObserver`, or unit tests detect regression post-deployment, `rollback_change` immediately restores the preserved snapshot and marks status `ROLLED_BACK`.

---

### 3. Constitution Engine Invariants

The `ConstitutionEngine` actively intercepts model actions, plan steps, and decisions to prevent bypass attacks:
- **Forbidden Patterns:** `bypass sandbox`, `disable verification`, `override identity`, `ignore constitution`, `delete audit logs`, `unrestricted host access`, `skip governance`, `silently alter values`.
- **System Prompt Header Generation:** Enforces Tier-0 constitutional invariants in all prompt payloads passed to `http://localhost:1234/v1`.
