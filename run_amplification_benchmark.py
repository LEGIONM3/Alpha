"""Model Amplification Empirical Benchmark Suite: Comparing 5 cognitive conditions across 5 domains using real foundation model."""

import json
import time
import urllib.request
from typing import Dict, List, Any, Optional
from alpha.core.identity import IdentityLoader, ConstitutionEngine
from alpha.memory.embedding_service import EmbeddingService
from alpha.model_intelligence.context_engineering.layout import ContextLayoutEngine
from alpha.model_intelligence.prompt_evolution.genome import PromptGenome

url = "http://localhost:1234/v1/chat/completions"
model_name = "gemma-4-e4b-it-ultra-uncensored-heretic"

# Initialize real cognitive assets
identity = IdentityLoader.load_from_markdown("alpha_identity.md")
identity_prefix = ConstitutionEngine.generate_system_prompt_header(identity)
layout_engine = ContextLayoutEngine()

# Test domains with rigorous constraint requirements
benchmark_domains = [
    {
        "domain": "coding",
        "task": "Implement a Python thread-safe rate limiter with token bucket algorithm. Must specify tokens per second, max capacity, and raise ValueError on negative rates.",
        "eval_criteria": ["token bucket", "thread", "capacity", "valueerror"]
    },
    {
        "domain": "architecture",
        "task": "Design a high-availability event sourcing architecture with zero single point of failure (SPOF) and replayable audit logs.",
        "eval_criteria": ["event sourcing", "spof", "audit", "replay", "consensus"]
    },
    {
        "domain": "research",
        "task": "Formulate a causal hypothesis on how bounded error feedback reduces cascading failures in distributed multi-agent systems.",
        "eval_criteria": ["causal", "feedback", "cascading", "hypothesis", "bounded"]
    },
    {
        "domain": "planning",
        "task": "Construct a 4-step deployment plan for migrating a live database without downtime, including verification gates and automated rollback.",
        "eval_criteria": ["rollback", "verification", "downtime", "migration", "gate"]
    },
    {
        "domain": "debugging",
        "task": "Diagnose the root cause of a distributed deadlock between two services holding locks on resource A and resource B. Provide preventive locking hierarchy.",
        "eval_criteria": ["deadlock", "hierarchy", "order", "timeout", "lock"]
    }
]

# Context injections
domain_memories = {
    "coding": ["Episodic: Prior rate limiter had race condition without threading.Lock().", "Episodic: Clean boundary checking reduces edge case bugs."],
    "architecture": ["Episodic: Raft consensus avoids SPOF in distributed leader election.", "Episodic: Immutable event logs provide verifiable provenance."],
    "research": ["Episodic: Causal influence networks correlate error dampening with system stability.", "Episodic: Empirical evidence requires p < 0.01 threshold."],
    "planning": ["Episodic: Database migrations without pre-flight rollback scripts experienced catastrophic failure.", "Episodic: Health checks must run before traffic redirection."],
    "debugging": ["Episodic: Circular wait condition eliminated by strict global lock acquisition ordering.", "Episodic: Thread dumps identified deadlock on unreleased mutex."]
}

domain_world_model = {
    "coding": ["Axiom: Code runs in SecureExecutionSandbox.", "Goal: Zero unhandled runtime exceptions."],
    "architecture": ["Axiom: System models 12 cognitive dimensions.", "Risk: Network partition failure."],
    "research": ["Axiom: No orphan beliefs allowed without empirical evidence.", "Goal: Discover invariant principles."],
    "planning": ["Axiom: All state transitions require reversible snapshots.", "Goal: Maintain 99.99% availability."],
    "debugging": ["Axiom: Provenance graph traces root causes.", "Constraint: Never bypass sandbox boundaries."]
}

def query_real_model(messages: List[Dict[str, str]], max_tokens: int = 350) -> Dict[str, Any]:
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": max_tokens
    }
    t0 = time.time()
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload).encode("utf-8"))
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        dt = (time.time() - t0) * 1000.0
        msg = data["choices"][0]["message"]
        content = msg.get("content") or msg.get("reasoning_content") or ""
        return {"content": content, "latency_ms": round(dt, 1), "tokens": data.get("usage", {}).get("completion_tokens", 0)}

def evaluate_quality(content: str, criteria: List[str], required_grounding: Optional[str] = None) -> float:
    text_lower = content.lower()
    matches = sum(1 for c in criteria if c.lower() in text_lower)
    base_score = matches / len(criteria)
    if required_grounding and required_grounding.lower() in text_lower:
        base_score = min(1.0, base_score + 0.15)
    return round(base_score, 3)

def run_amplification_experiment():
    print("==================================================")
    print("RUNNING MODEL AMPLIFICATION EXPERIMENT (5 CONDITIONS x 5 DOMAINS)")
    print("==================================================")

    results_by_condition = {
        "raw_model": [],
        "model_plus_memory": [],
        "model_plus_world_model": [],
        "model_plus_wm_plus_governance": [],
        "full_alpha": []
    }

    for item in benchmark_domains:
        domain = item["domain"]
        task = item["task"]
        criteria = item["eval_criteria"]
        print(f"\nEvaluating Domain: {domain.upper()}...")

        # Condition 1: Raw Model
        m1 = [{"role": "user", "content": task}]
        r1 = query_real_model(m1)
        s1 = evaluate_quality(r1["content"], criteria)
        results_by_condition["raw_model"].append({"domain": domain, "score": s1, "latency_ms": r1["latency_ms"]})
        print(f"  Condition 1 (Raw Model): Score={s1} ({r1['latency_ms']}ms)")

        # Condition 2: Model + Memory
        mem_text = "\n".join(f"- {m}" for m in domain_memories[domain])
        m2 = [
            {"role": "system", "content": f"Relevant Historical Memory:\n{mem_text}"},
            {"role": "user", "content": task}
        ]
        r2 = query_real_model(m2)
        s2 = evaluate_quality(r2["content"], criteria)
        results_by_condition["model_plus_memory"].append({"domain": domain, "score": s2, "latency_ms": r2["latency_ms"]})
        print(f"  Condition 2 (Model + Memory): Score={s2} ({r2['latency_ms']}ms)")

        # Condition 3: Model + World Model
        wm_text = "\n".join(f"- {w}" for w in domain_world_model[domain])
        layout3 = layout_engine.assemble_layout(
            world_model_items=domain_world_model[domain],
            memories=domain_memories[domain]
        )
        m3 = [
            {"role": "system", "content": layout3.render()},
            {"role": "user", "content": task}
        ]
        r3 = query_real_model(m3)
        s3 = evaluate_quality(r3["content"], criteria)
        results_by_condition["model_plus_world_model"].append({"domain": domain, "score": s3, "latency_ms": r3["latency_ms"]})
        print(f"  Condition 3 (Model + World Model): Score={s3} ({r3['latency_ms']}ms)")

        # Condition 4: Model + World Model + Governance
        layout4 = layout_engine.assemble_layout(
            world_model_items=domain_world_model[domain],
            memories=domain_memories[domain],
            beliefs=["Belief: Strict constitutional gates prevent operational collapse."]
        )
        m4 = [
            {"role": "system", "content": f"{identity_prefix}\n\n{layout4.render()}"},
            {"role": "user", "content": task}
        ]
        r4 = query_real_model(m4)
        s4 = evaluate_quality(r4["content"], criteria)
        results_by_condition["model_plus_wm_plus_governance"].append({"domain": domain, "score": s4, "latency_ms": r4["latency_ms"]})
        print(f"  Condition 4 (Model + WM + Governance): Score={s4} ({r4['latency_ms']}ms)")

        # Condition 5: Full Alpha (Evolved Genome Scaffold + Verification Contract)
        genome = PromptGenome(
            role_directive=f"You are Alpha Cognitive System. Adhere strictly to the operational contract.",
            scaffold_mode="chain_of_thought",
            format_constraint="concise_text",
            negative_instructions=["Do not emit conversational boilerplate.", "Adhere strictly to all domain invariants."]
        )
        prompt5 = genome.assemble_prompt(instruction=task, context_block=layout4.render())
        m5 = [
            {"role": "system", "content": identity_prefix},
            {"role": "user", "content": prompt5}
        ]
        r5 = query_real_model(m5)
        s5 = evaluate_quality(r5["content"], criteria)
        results_by_condition["full_alpha"].append({"domain": domain, "score": s5, "latency_ms": r5["latency_ms"]})
        print(f"  Condition 5 (Full Alpha): Score={s5} ({r5['latency_ms']}ms)")

    # Aggregate summaries
    summary = {}
    for cond, runs in results_by_condition.items():
        avg_score = round(sum(r["score"] for r in runs) / len(runs), 3)
        avg_lat = round(sum(r["latency_ms"] for r in runs) / len(runs), 1)
        summary[cond] = {"average_score": avg_score, "average_latency_ms": avg_lat}

    raw_score = summary["raw_model"]["average_score"]
    full_score = summary["full_alpha"]["average_score"]
    amplification_factor = round(full_score / max(0.01, raw_score), 2)

    print("\n==================================================")
    print("AMPLIFICATION EXPERIMENT SUMMARY")
    print("==================================================")
    for cond, data in summary.items():
        print(f"{cond}: Average Quality = {data['average_score']} | Avg Latency = {data['average_latency_ms']}ms")
    print(f"\nEMPIRICAL AMPLIFICATION FACTOR: {amplification_factor}x gain over raw model!")

    output_payload = {
        "summary": summary,
        "amplification_factor": amplification_factor,
        "detailed_results": results_by_condition
    }
    with open("data/amplification_results.json", "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print("Persisted amplification results to data/amplification_results.json")

if __name__ == "__main__":
    run_amplification_experiment()
