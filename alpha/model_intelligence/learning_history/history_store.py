"""Model Learning History Store: Persistent tracking of prompts, evaluations, failures, and scores."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from alpha.model_intelligence.learning_history.records import ExecutionRecord


class ModelLearningHistory:
    """Maintains a longitudinal record of all foundation model interactions, scores, and failure patterns."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._records: List[ExecutionRecord] = []
        if self.storage_path and self.storage_path.exists():
            self.load()

    def record_run(
        self,
        model_name: str,
        task_domain: str,
        strategy_used: str,
        prompt: str,
        output: str,
        score: float,
        latency_ms: float,
        had_failure: bool = False,
        failure_types: Optional[List[str]] = None,
        prompt_genome_id: Optional[str] = None,
        amplification_factor: Optional[float] = None
    ) -> ExecutionRecord:
        rec = ExecutionRecord(
            model_name=model_name,
            task_domain=task_domain,
            strategy_used=strategy_used,
            prompt_preview=prompt[:200] + ("..." if len(prompt) > 200 else ""),
            output_preview=output[:200] + ("..." if len(output) > 200 else ""),
            score=round(score, 3),
            latency_ms=round(latency_ms, 1),
            had_failure=had_failure,
            failure_types=failure_types or [],
            prompt_genome_id=prompt_genome_id,
            amplification_factor=amplification_factor
        )
        self._records.append(rec)
        if self.storage_path:
            self.save()
        return rec

    def get_history(
        self,
        model_name: Optional[str] = None,
        task_domain: Optional[str] = None,
        limit: int = 100
    ) -> List[ExecutionRecord]:
        results = self._records
        if model_name:
            results = [r for r in results if r.model_name == model_name]
        if task_domain:
            results = [r for r in results if r.task_domain == task_domain]
        return results[-limit:]

    def get_domain_trend(self, task_domain: str) -> Dict[str, Any]:
        runs = [r for r in self._records if r.task_domain == task_domain]
        if not runs:
            return {
                "task_domain": task_domain,
                "total_runs": 0,
                "avg_score": 0.0,
                "failure_rate": 0.0,
                "recent_trajectory": []
            }
        scores = [r.score for r in runs]
        failures = sum(1 for r in runs if r.had_failure)
        return {
            "task_domain": task_domain,
            "total_runs": len(runs),
            "avg_score": round(sum(scores) / len(scores), 3),
            "failure_rate": round(failures / len(runs), 3),
            "recent_trajectory": scores[-10:]
        }

    def get_failure_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = defaultdict(int)
        for r in self._records:
            for ft in r.failure_types:
                dist[ft] += 1
        return dict(dist)

    def get_summary(self) -> Dict[str, Any]:
        if not self._records:
            return {
                "total_executions": 0,
                "overall_avg_score": 0.0,
                "overall_failure_rate": 0.0,
                "avg_amplification_factor": 1.0,
                "top_domains": {}
            }

        scores = [r.score for r in self._records]
        failures = sum(1 for r in self._records if r.had_failure)
        amp_factors = [r.amplification_factor for r in self._records if r.amplification_factor is not None]

        domain_counts: Dict[str, int] = defaultdict(int)
        for r in self._records:
            domain_counts[r.task_domain] += 1

        return {
            "total_executions": len(self._records),
            "overall_avg_score": round(sum(scores) / len(scores), 3),
            "overall_failure_rate": round(failures / len(self._records), 3),
            "avg_amplification_factor": round(sum(amp_factors) / len(amp_factors), 2) if amp_factors else 1.0,
            "domain_runs": dict(domain_counts)
        }

    def save(self):
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([r.model_dump() for r in self._records], f, indent=2)

    def load(self):
        if self.storage_path and self.storage_path.exists():
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._records = [ExecutionRecord(**item) for item in data]
