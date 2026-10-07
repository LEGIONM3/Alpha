"""100-Cycle Autonomous Learning Validation for Project Alpha Reality Integration Milestone.

Runs 100 fully autonomous cycles of reality-based learning:
- Real Observation Acquisition (code, docs, reports, logs, telemetry, metadata)
- Real Knowledge Gap Detection (AST, unmodeled modules, untested paths, low confidence)
- Real Question Generation
- Real Research Investigation (code search, AST dependency tracing, documentation citations)
- Real Falsifiable Hypothesis Formulation (with falsification conditions & verification plans)
- Empirical Verification / Testing
- Real Epistemic Belief Revision in CognitiveWorldModel
- Real Novel Knowledge Differential Tracking

Stores all evidence to data/reality_integration_evidence/.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List

from alpha.runtime_cycle import AlphaRuntimeCycle
from alpha.world_model import CognitiveWorldModel


def run_100_cycle_validation():
    print("================================================================================")
    print("EXECUTING REALITY INTEGRATION MILESTONE: 100 AUTONOMOUS LEARNING CYCLES")
    print("================================================================================")

    evidence_dir = Path("data/reality_integration_evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    cycles_log_file = evidence_dir / "learning_cycles.jsonl"
    summary_file = evidence_dir / "final_validation_summary.json"

    # Clean previous run evidence if present
    if cycles_log_file.exists():
        cycles_log_file.unlink()

    # Initialize unified World Model & Runtime Loop
    t_start = time.time()
    world_model = CognitiveWorldModel()
    runner = AlphaRuntimeCycle(world_model=world_model, verbose=False)

    print(f"[{datetime.now(timezone.utc).isoformat()}] CognitiveWorldModel initialized.")
    print(f"Initial Active Beliefs: {len(world_model.beliefs.get_all())}")
    print(f"Initial Ontology Entities: {len(world_model.ontology.get_all())}")
    print("Launching 100-cycle autonomous progression...\n")

    cycle_records: List[Dict[str, Any]] = []

    for c_idx in range(1, 101):
        t0 = time.time()
        res = runner.run_cycle()
        elapsed_ms = round((time.time() - t0) * 1000.0, 2)

        record = {
            "cycle_index": c_idx,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": elapsed_ms,
            "observations_count": res["observations_count"],
            "gaps_count": res["gaps_count"],
            "questions_count": res["questions_count"],
            "findings_count": res["findings_count"],
            "hypotheses_count": res["hypotheses_count"],
            "verified_hypotheses_count": res["verified_hypotheses_count"],
            "beliefs_count": res["beliefs_count"],
            "contradictions_count": res["contradictions_count"],
            "learning_score": res["learning_score"],
            "sample_observation": res.get("sample_observation"),
            "sample_gap": res.get("sample_gap"),
            "sample_finding": res.get("sample_finding"),
            "sample_hypothesis": res.get("sample_hypothesis")
        }

        cycle_records.append(record)

        # Append to jsonl log
        with open(cycles_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        # Milestone progress reporting
        if c_idx % 10 == 0 or c_idx == 1:
            metrics = runner.novel_knowledge_scorer.get_current_metrics()
            print(
                f"Cycle {c_idx:3d}/100 | Time: {elapsed_ms:6.1f}ms | "
                f"Obs: {metrics.new_observations_count:3d} | "
                f"Findings: {metrics.new_findings_count:3d} | "
                f"Hyps: {metrics.new_hypotheses_count:3d} | "
                f"Beliefs: {len(world_model.beliefs.get_all()):3d} | "
                f"Contradictions: {metrics.contradictions_resolved_count:2d} | "
                f"Score: {res['learning_score']:8.2f}"
            )

    total_duration = round(time.time() - t_start, 2)
    final_metrics = runner.novel_knowledge_scorer.get_current_metrics()

    summary_data = {
        "status": "SUCCESS",
        "milestone": "REALITY_INTEGRATION_100_CYCLES",
        "timestamp_completed": datetime.now(timezone.utc).isoformat(),
        "total_cycles_executed": len(cycle_records),
        "total_duration_seconds": total_duration,
        "avg_cycle_duration_ms": round(sum(r["duration_ms"] for r in cycle_records) / len(cycle_records), 2),
        "epistemic_learning_metrics": {
            "total_new_observations": final_metrics.new_observations_count,
            "total_new_findings": final_metrics.new_findings_count,
            "total_new_hypotheses": final_metrics.new_hypotheses_count,
            "total_belief_changes": final_metrics.belief_changes_count,
            "total_contradictions_detected": final_metrics.contradictions_resolved_count,
            "total_verified_discoveries": final_metrics.verified_discoveries_count,
            "final_learning_score": final_metrics.total_learning_score
        },
        "world_model_state": {
            "active_beliefs_count": len(world_model.beliefs.get_all()),
            "ontology_entities_count": len(world_model.ontology.get_all()),
            "knowledge_graph_nodes": len(world_model.graph.get_all_nodes()) if hasattr(world_model.graph, "get_all_nodes") else 0,
            "epistemic_health": world_model.beliefs.summarize_epistemic_state() if hasattr(world_model.beliefs, "summarize_epistemic_state") else {}
        }
    }

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print("\n================================================================================")
    print("100-CYCLE AUTONOMOUS VALIDATION COMPLETED SUCCESSFULLY")
    print("================================================================================")
    print(f"Total Duration: {total_duration}s | Avg Cycle: {summary_data['avg_cycle_duration_ms']}ms")
    print(f"Final Learning Score: {final_metrics.total_learning_score:.2f}")
    print(f"New Observations Discovered: {final_metrics.new_observations_count}")
    print(f"Empirical Research Findings: {final_metrics.new_findings_count}")
    print(f"Falsifiable Hypotheses Formulated: {final_metrics.new_hypotheses_count}")
    print(f"Active Grounded Beliefs in World Model: {len(world_model.beliefs.get_all())}")
    print(f"Evidence Artifacts Stored:")
    print(f"  - {cycles_log_file.as_posix()} ({cycles_log_file.stat().st_size} bytes)")
    print(f"  - {summary_file.as_posix()} ({summary_file.stat().st_size} bytes)")
    print("================================================================================")

    return summary_data


if __name__ == "__main__":
    run_100_cycle_validation()
