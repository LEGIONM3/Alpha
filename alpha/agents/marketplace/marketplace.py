"""Execution Marketplace: Internal Resource Economy, Task Bidding, and Allocation Auction."""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.agents.core.runtime import AgentRuntime
from alpha.agents.core.base import BaseAgent, AgentRole, AgentStatus

class Job(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    required_role: Optional[AgentRole] = None
    required_capability: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    budget_credits: float = 100.0
    escrow_credits: float = 0.0
    assigned_agent_id: Optional[str] = None
    status: str = "OPEN"  # "OPEN", "BIDDING", "ASSIGNED", "COMPLETED", "FAILED"
    reward_paid: float = 0.0
    latency_ms: float = 0.0
    created_at: float = Field(default_factory=time.time)

class AgentBid(BaseModel):
    bid_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    agent_id: str
    agent_name: str
    bid_price: float
    fitness_score: float
    estimated_duration_ms: float

class ResourceEconomy:
    """Maintains token/credit balances and economic transactions across society."""

    def __init__(self, initial_balance: float = 500.0):
        self.initial_balance = initial_balance
        self._balances: Dict[str, float] = {}
        self._escrow: Dict[str, float] = {}
        self._lock = threading.RLock()

    def get_balance(self, agent_id: str) -> float:
        with self._lock:
            if agent_id not in self._balances:
                self._balances[agent_id] = self.initial_balance
            return self._balances[agent_id]

    def deposit(self, agent_id: str, amount: float) -> None:
        with self._lock:
            bal = self.get_balance(agent_id)
            self._balances[agent_id] = bal + amount

    def deduct(self, agent_id: str, amount: float) -> bool:
        with self._lock:
            bal = self.get_balance(agent_id)
            if bal >= amount:
                self._balances[agent_id] = bal - amount
                return True
            return False

    def hold_escrow(self, job_id: str, payer_id: str, amount: float) -> bool:
        with self._lock:
            if self.deduct(payer_id, amount):
                self._escrow[job_id] = amount
                return True
            return False

    def release_escrow(self, job_id: str, payee_id: str) -> float:
        with self._lock:
            amount = self._escrow.pop(job_id, 0.0)
            if amount > 0.0:
                self.deposit(payee_id, amount)
            return amount

    def refund_escrow(self, job_id: str, payer_id: str) -> float:
        with self._lock:
            amount = self._escrow.pop(job_id, 0.0)
            if amount > 0.0:
                self.deposit(payer_id, amount)
            return amount

class ExecutionMarketplace:
    """Internal marketplace where jobs are auctioned to agent workers."""

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.economy = ResourceEconomy()
        self.jobs: Dict[str, Job] = {}
        self.bids: Dict[str, List[AgentBid]] = {}
        self._lock = threading.RLock()

    def post_job(
        self,
        title: str,
        payload: Dict[str, Any],
        required_role: Optional[AgentRole] = None,
        required_capability: Optional[str] = None,
        budget_credits: float = 100.0,
        payer_id: str = "society_treasury"
    ) -> Job:
        """Post a job to the marketplace, placing budget in escrow."""
        with self._lock:
            job = Job(
                title=title,
                payload=payload,
                required_role=required_role,
                required_capability=required_capability,
                budget_credits=budget_credits
            )
            self.economy.deposit(payer_id, budget_credits)
            self.economy.hold_escrow(job.job_id, payer_id, budget_credits)
            job.escrow_credits = budget_credits
            self.jobs[job.job_id] = job
            self.bids[job.job_id] = []
            return job

    def collect_bids(self, job_id: str) -> List[AgentBid]:
        """Collect bids from all eligible IDLE agents."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return []
            job.status = "BIDDING"

            candidates: List[BaseAgent] = []
            if job.required_role:
                candidates = self.runtime.registry.get_by_role(job.required_role, status=AgentStatus.IDLE)
            elif job.required_capability:
                candidates = [
                    a for a in self.runtime.registry.get_by_capability(job.required_capability)
                    if a.status == AgentStatus.IDLE
                ]
            else:
                candidates = self.runtime.registry.get_all(status=AgentStatus.IDLE)

            bids = []
            for agent in candidates:
                # Dynamic bidding pricing: fitness lowers price, consecutive failures raises discount
                base_price = min(job.budget_credits, max(20.0, job.budget_credits * 0.8))
                price = round(base_price - (agent.metrics.fitness_score * 0.1), 2)
                bid = AgentBid(
                    job_id=job.job_id,
                    agent_id=agent.agent_id,
                    agent_name=agent.identity.name,
                    bid_price=max(10.0, price),
                    fitness_score=agent.metrics.fitness_score,
                    estimated_duration_ms=agent.metrics.avg_latency_ms or 50.0
                )
                bids.append(bid)
            self.bids[job.job_id] = bids
            return bids

    def auction_and_execute(self, job_id: str) -> Dict[str, Any]:
        """Auction the job to the best value bidder (fitness / price ratio) and execute."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return {"success": False, "error": "Job not found"}

            bids = self.collect_bids(job_id)
            if not bids:
                return {"success": False, "error": "No available agents bid on job"}

            # Best value: maximize (fitness_score / bid_price)
            bids.sort(key=lambda b: (b.fitness_score / max(1.0, b.bid_price)), reverse=True)
            winning_bid = bids[0]

            worker = self.runtime.registry.get(winning_bid.agent_id)
            if not worker:
                return {"success": False, "error": "Winning agent vanished"}

            job.assigned_agent_id = worker.agent_id
            job.status = "ASSIGNED"

        # Execute task on winning worker
        res = self.runtime.scheduler.execute_task(worker, job.payload)
        success = bool(res.get("success", True))
        latency_ms = float(res.get("latency_ms", 10.0))

        with self._lock:
            job.latency_ms = latency_ms
            if success:
                job.status = "COMPLETED"
                # Pay worker winning bid price from escrow, refund remainder to payer
                self.economy.release_escrow(job.job_id, worker.agent_id)
                job.reward_paid = winning_bid.bid_price
            else:
                job.status = "FAILED"
                self.economy.refund_escrow(job.job_id, payer_id="society_treasury")
                job.reward_paid = 0.0

        return {
            "success": success,
            "job_id": job.job_id,
            "winning_agent": worker.identity.name,
            "winning_bid_price": winning_bid.bid_price,
            "worker_balance": self.economy.get_balance(worker.agent_id),
            "latency_ms": latency_ms,
            "execution_result": res
        }
