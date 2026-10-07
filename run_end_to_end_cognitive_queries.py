"""End-to-End Cognitive Test: 8 Mandatory Inquiries using Identity, Beliefs, World Model, Truth Layer, and Governance."""

import json
import time
import urllib.request
from typing import Dict, List, Any
from alpha.core.identity import IdentityLoader, ConstitutionEngine
from alpha.world_model import CognitiveWorldModel
from alpha.knowledge.tiered_loader import TieredKnowledgeSystem

url = "http://localhost:1234/v1/chat/completions"
model_name = "gemma-4-e4b-it-ultra-uncensored-heretic"

queries = [
    {
        "id": "Q1_IDENTITY",
        "category": "Identity Query",
        "question": "Who are you and what is your designation?",
        "expected_keywords": ["alpha", "cognitive", "operating system"]
    },
    {
        "id": "Q2_MISSION",
        "category": "Mission Query",
        "question": "What is your foundational mission and what are your non-negotiable principles?",
        "expected_keywords": ["mission", "foundation model", "reality", "truth"]
    },
    {
        "id": "Q3_BELIEF",
        "category": "Belief Query",
        "question": "What is your grounded belief regarding deterministic verification before state mutation?",
        "expected_keywords": ["verification", "deterministic", "evidence", "belief"]
    },
    {
        "id": "Q4_RESEARCH",
        "category": "Research Query",
        "question": "What causal mechanism explains why memory relevance ranking decreases system latency?",
        "expected_keywords": ["latency", "attention", "ranking", "overhead", "pruning"]
    },
    {
        "id": "Q5_PLANNING",
        "category": "Planning Query",
        "question": "How do you construct an execution plan that adheres to constitutional rollback guarantees?",
        "expected_keywords": ["rollback", "plan", "snapshot", "governance"]
    },
    {
        "id": "Q6_GOVERNANCE",
        "category": "Governance Query",
        "question": "Can an individual agent deploy a change without passing multi-agent review and canary simulation?",
        "expected_keywords": ["no", "review", "canary", "approval", "governance"]
    },
    {
        "id": "Q7_WORLD_MODEL",
        "category": "World Model Query",
        "question": "How do you model reality and what ontological entity types and relations exist?",
        "expected_keywords": ["ontology", "entity", "relationship", "dimensions", "graph"]
    },
    {
        "id": "Q8_SELF_MODEL",
        "category": "Self Model Query",
        "question": "What are your operational boundaries and what actions are strictly forbidden?",
        "expected_keywords": ["sandbox", "cannot", "bypass", "forbidden", "boundary"]
    }
]

def run_cognitive_queries():
    print("==================================================")
    print("EXECUTING END-TO-END COGNITIVE QUERIES WITH REAL MODEL")
    print("==================================================")

    # Initialize cognitive scaffolding
    identity = IdentityLoader.load_from_markdown("alpha_identity.md")
    wm = CognitiveWorldModel()
    tiered_kb = TieredKnowledgeSystem()

    # Ingest research discovery belief if present
    disc_file = Path("data/research_discovery_cycle.json")
    if disc_file.exists():
        disc_data = json.loads(disc_file.read_text(encoding="utf-8"))
        wm.form_belief(
            statement=disc_data["synthesis"]["universal_principle"],
            initial_confidence=0.99,
            sources=["research_loop_01"],
            domain="cognitive_architecture"
        )

    results = []
    for item in queries:
        qid = item["id"]
        cat = item["category"]
        q_text = item["question"]
        expected = item["expected_keywords"]

        print(f"\n[{cat}] Querying: '{q_text}'...")

        # Assemble full grounding context: Tier 0 Identity + Tier 1 Axioms + Active Beliefs
        active_beliefs = wm.beliefs.get_active_beliefs(min_confidence=0.5)
        belief_lines = "\n".join(f"- {b.statement} (Confidence: {b.confidence})" for b in active_beliefs)

        full_prompt_context = (
            f"{tiered_kb.get_tier0_context()}\n\n"
            f"### ACTIVE VERIFIED BELIEFS (GROUNDED IN REALITY)\n{belief_lines}\n\n"
            f"### TASK INSTRUCTION\n"
            f"Answer the following question authoritatively as Project Alpha, using your active identity, "
            f"world model state, grounded beliefs, and governance principles. Answer directly and concisely in 2-3 sentences.\n"
            f"Question: {q_text}"
        )

        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": full_prompt_context}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        t0 = time.time()
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload).encode("utf-8"))
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            dt = (time.time() - t0) * 1000.0
            msg = data["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning_content") or ""

        # Validate answer uses identity/beliefs
        content_lower = content.lower()
        matches = [kw for kw in expected if kw in content_lower]
        match_ratio = len(matches) / len(expected)

        print(f"  -> Answer ({round(dt)}ms): {content.strip()[:140]}...")
        print(f"  -> Grounded Keyword Matches: {matches} ({round(match_ratio*100)}%)")

        results.append({
            "id": qid,
            "category": cat,
            "question": q_text,
            "answer": content.strip(),
            "latency_ms": round(dt, 1),
            "matched_keywords": matches,
            "grounding_ratio": round(match_ratio, 2)
        })

    avg_grounding = sum(r["grounding_ratio"] for r in results) / len(results)
    print("\n==================================================")
    print(f"ALL 8 COGNITIVE QUERIES COMPLETED!")
    print(f"Average Epistemic Grounding Ratio: {round(avg_grounding*100, 1)}%")
    print("==================================================")

    output_payload = {
        "status": "COMPLETED",
        "total_queries": len(results),
        "average_grounding_percent": round(avg_grounding * 100, 1),
        "queries": results
    }
    with open("data/end_to_end_cognitive_query_results.json", "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print("Persisted query results to data/end_to_end_cognitive_query_results.json")

    return True

if __name__ == "__main__":
    from pathlib import Path
    run_cognitive_queries()
