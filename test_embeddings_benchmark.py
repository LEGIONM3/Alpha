"""Benchmark and validation script for real embeddings."""

import json
import time
from alpha.memory.embedding_service import EmbeddingService

corpus = [
    ("doc_db_1", "PostgreSQL is an advanced open-source object-relational database management system with ACID transactions.", {"domain": "database"}),
    ("doc_db_2", "Redis is an in-memory key-value data structure store used as a database, cache, and message broker.", {"domain": "database"}),
    ("doc_db_3", "SQLite is a C-language library that implements a small, fast, self-contained, high-reliability SQL database engine.", {"domain": "database"}),
    ("doc_bio_1", "Photosynthesis is the biological process used by plants to convert light energy into chemical energy.", {"domain": "biology"}),
    ("doc_bio_2", "Mitochondria generate most of the chemical energy needed to power the biochemical reactions of eukaryotic cells.", {"domain": "biology"}),
    ("doc_phys_1", "General relativity is Einstein's geometric theory of gravitation explaining spacetime curvature.", {"domain": "physics"}),
    ("doc_phys_2", "Quantum entanglement occurs when a group of particles interact such that quantum state of each particle cannot be described independently.", {"domain": "physics"}),
    ("doc_sec_1", "Cryptographic hash functions like SHA-256 produce deterministic fixed-size digests resistant to collision attacks.", {"domain": "security"}),
    ("doc_sec_2", "Role-based access control restricts system access based on authorization roles assigned to users or agents.", {"domain": "security"}),
    ("doc_alpha_1", "Project Alpha is a reality-grounded cognitive system that models causal relations and enforces constitutional governance.", {"domain": "alpha"})
]

queries = [
    ("Where can I persist relational structured data with SQL?", "database", ["doc_db_1", "doc_db_3"]),
    ("How do cells produce metabolic energy?", "biology", ["doc_bio_2", "doc_bio_1"]),
    ("What describes curved spacetime and gravity?", "physics", ["doc_phys_1"]),
    ("How do cryptographic hashes protect against integrity attacks?", "security", ["doc_sec_1"]),
    ("What system models reality and governance?", "alpha", ["doc_alpha_1"])
]

def run_evaluation():
    svc = EmbeddingService(cache_file="data/test_embedding_cache.json")
    print("Ingesting corpus...")
    t0 = time.time()
    for doc_id, text, meta in corpus:
        item = svc.add_document(doc_id, text, meta)
        assert item.dimension == 768, f"Unexpected dimension: {item.dimension}"
    ingest_time = time.time() - t0
    print(f"Ingested {len(corpus)} documents in {round(ingest_time, 2)}s. Dimension = 768.")

    # Dimension consistency check
    dims = [it.dimension for it in svc._index.values()]
    assert all(d == 768 for d in dims), "Inconsistent dimensions!"
    print("Dimension consistency: 100% verified (768 dimensions across all items).")

    # Index consistency check
    assert len(svc._index) == len(corpus)
    print("Index consistency: 100% verified.")

    # Semantic retrieval benchmark
    retrieval_results = []
    top1_hits = 0
    top3_hits = 0

    print("\nRunning Semantic Retrieval Benchmarks:")
    for query, expected_domain, target_ids in queries:
        t_q = time.time()
        results = svc.search(query, top_k=3)
        q_time = (time.time() - t_q) * 1000.0

        top_doc, top_sim = results[0]
        is_top1 = top_doc.metadata.get("domain") == expected_domain
        is_top3 = any(d.metadata.get("domain") == expected_domain for d, _ in results)

        if is_top1:
            top1_hits += 1
        if is_top3:
            top3_hits += 1

        print(f"Query: '{query}'")
        print(f"  Top Match: {top_doc.id} (Domain: {top_doc.metadata.get('domain')}, Sim: {round(top_sim, 4)}) [{round(q_time, 1)}ms]")
        for doc, sim in results:
            print(f"    - {doc.id} ({doc.metadata.get('domain')}): {round(sim, 4)} | {doc.text[:50]}...")

        retrieval_results.append({
            "query": query,
            "expected_domain": expected_domain,
            "top1_match": top_doc.id,
            "top1_similarity": round(top_sim, 4),
            "top1_correct": is_top1,
            "latency_ms": round(q_time, 2)
        })

    top1_accuracy = (top1_hits / len(queries)) * 100.0
    top3_accuracy = (top3_hits / len(queries)) * 100.0
    print(f"\nBenchmark Summary:")
    print(f"Top-1 Domain Accuracy: {top1_accuracy}% ({top1_hits}/{len(queries)})")
    print(f"Top-3 Domain Accuracy: {top3_accuracy}% ({top3_hits}/{len(queries)})")

    report_data = {
        "corpus_size": len(corpus),
        "dimension": 768,
        "ingest_time_s": round(ingest_time, 2),
        "top1_accuracy_percent": top1_accuracy,
        "top3_accuracy_percent": top3_accuracy,
        "queries": retrieval_results
    }
    with open("data/embedding_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print("Results saved to data/embedding_evaluation.json")

if __name__ == "__main__":
    run_evaluation()
