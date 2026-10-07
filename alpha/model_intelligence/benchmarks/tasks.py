"""Benchmark Tasks and Procedural Generator: 1000+ benchmark task battery across 7 domains."""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class BenchmarkTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"bm_{uuid.uuid4().hex[:8]}")
    domain: str
    subdomain: str
    difficulty: str  # simple, medium, hard, expert
    prompt: str
    ground_truth_assertion: str
    expected_invariants: List[str] = Field(default_factory=list)


class BenchmarkBatteryGenerator:
    """Procedurally generates 1000+ structured benchmark tasks spanning 7 canonical domains."""

    DOMAINS = [
        "coding",
        "architecture",
        "reasoning",
        "planning",
        "retrieval",
        "memory",
        "simulation"
    ]

    DIFFICULTIES = ["simple", "medium", "hard", "expert"]

    def generate_domain_tasks(self, domain: str, count: int = 150) -> List[BenchmarkTask]:
        tasks: List[BenchmarkTask] = []

        templates = {
            "coding": [
                ("data_structures", "Implement an LRU cache in Python with O(1) get and put operations.", "LRUCache class with dict and doubly linked list", ["O(1)", "capacity"]),
                ("algorithms", "Implement Dijkstra's shortest path algorithm using a min-heap.", "dijkstra function with heapq", ["heapq", "distances"]),
                ("concurrency", "Write a thread-safe token bucket rate limiter with lock acquisition.", "RateLimiter with mutex lock", ["threading.Lock", "acquire"]),
                ("refactoring", "Refactor a monolithic God function into decoupled SOLID classes.", "Clean interfaces and dependency injection", ["class", "decoupled"]),
                ("debugging", "Identify and fix the off-by-one indexing error in binary search.", "Low <= high and mid calculation", ["while low <= high", "mid"]),
            ],
            "architecture": [
                ("cqrs_events", "Design a CQRS event-sourcing system with idempotent replay.", "EventStore, CommandHandler, ReadProjection", ["idempotent", "replay"]),
                ("caching", "Architect a multi-tier write-through cache with invalidation bus.", "L1 memory cache and L2 Redis cluster", ["invalidation", "consistency"]),
                ("distributed_consensus", "Explain Raft leader election and log replication guarantees.", "Term numbers, heartbeats, majority quorum", ["quorum", "election"]),
                ("partitioning", "Design a consistent hashing ring for distributed node sharding.", "Virtual nodes on hash circle", ["virtual nodes", "hash ring"]),
            ],
            "reasoning": [
                ("deduction", "Given premises: All P are Q; No Q are R; Some S are P. Prove: Some S are not R.", "Formal syllogistic derivation", ["valid", "deduction"]),
                ("causality", "Distinguish causal influence from confounding variable in medical trials.", "Confounder adjustment and do-calculus", ["confounder", "causal"]),
                ("logic_puzzles", "Solve the Einstein five-house constraint satisfaction problem.", "Direct constraint propagation", ["constraint", "solution"]),
                ("bayesian", "Calculate posterior probability given 99% test accuracy and 1% base rate.", "Bayes rule application: 50% posterior", ["posterior", "base rate"]),
            ],
            "planning": [
                ("dependency_dag", "Order 10 interdependent deployment tasks into a topological sequence.", "Topological sort DAG resolution", ["topological", "order"]),
                ("critical_path", "Calculate the critical path and total float for a construction schedule.", "Earliest start, latest finish, zero float", ["critical path", "float"]),
                ("resource_allocation", "Assign 4 engineers to 8 sprint deliverables under capacity limits.", "Constrained capacity optimization", ["capacity", "allocation"]),
                ("failover_recovery", "Formulate a multi-stage disaster recovery runbook under zero data loss.", "RPO=0 failover sequence", ["runbook", "failover"]),
            ],
            "retrieval": [
                ("needle_haystack", "Locate the secret security key embedded at position 85% in 100 pages.", "Key extraction without loss", ["key", "found"]),
                ("multi_hop", "Triangulate the CEO of the subsidiary of the holding company acquired in 2021.", "Two-hop entity traversal", ["holding", "subsidiary"]),
                ("contradiction_filter", "Given 5 conflicting documents, identify the authoritative latest version.", "Temporal timestamp prioritization", ["timestamp", "authoritative"]),
                ("precision_qa", "Extract exact numerical tolerance threshold from ISO spec document.", "Exact numeric quotation", ["tolerance", "threshold"]),
            ],
            "memory": [
                ("long_horizon", "Recall user preferences established 50 turns prior regarding output syntax.", "Preference retention", ["preference", "recalled"]),
                ("belief_updating", "Revise belief state when new telemetry invalidates old hypothesis.", "Bayesian belief revision", ["revision", "updated"]),
                ("cross_conversation", "Synthesize findings across three disjoint historical conversation sessions.", "Episodic synthesis", ["synthesis", "memory"]),
                ("session_grounding", "Preserve persistent state across simulated server restarts.", "State serialization", ["persistent", "state"]),
            ],
            "simulation": [
                ("agent_dynamics", "Simulate a 50-agent internal token market across 20 rounds.", "Price clearing equilibrium", ["equilibrium", "market"]),
                ("cascade_failure", "Model cascading outage when 3 core microservice nodes drop offline.", "Blast radius and circuit breaker tripping", ["cascade", "circuit breaker"]),
                ("game_theory", "Simulate repeated Prisoner's Dilemma with Tit-for-Tat vs Grudger.", "Cooperation stability", ["tit-for-tat", "payoff"]),
                ("stress_testing", "Simulate 10,000 QPS load spike against rate limiter.", "Rejection rate and queue stability", ["queue", "throughput"]),
            ]
        }

        domain_temps = templates.get(domain, templates["reasoning"])

        for i in range(count):
            sub, prompt_pattern, ground_truth, invariants = domain_temps[i % len(domain_temps)]
            diff = self.DIFFICULTIES[i % len(self.DIFFICULTIES)]
            task = BenchmarkTask(
                domain=domain,
                subdomain=sub,
                difficulty=diff,
                prompt=f"[{domain.upper()} - {diff.upper()}] Case #{i + 1}: {prompt_pattern} (Variation {i // len(domain_temps)})",
                ground_truth_assertion=ground_truth,
                expected_invariants=invariants + [sub]
            )
            tasks.append(task)

        return tasks

    def generate_full_battery(self, count_per_domain: int = 150) -> List[BenchmarkTask]:
        """Generates 7 * count_per_domain tasks (default: 7 * 150 = 1050 tasks)."""
        all_tasks = []
        for d in self.DOMAINS:
            all_tasks.extend(self.generate_domain_tasks(d, count=count_per_domain))
        return all_tasks
