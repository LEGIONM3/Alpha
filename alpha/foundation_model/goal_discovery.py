"""Autonomous Goal Discovery Engine for the Foundation Model Agent.

This module implements the agent's ability to autonomously identify and pursue
meaningful goals — not just responding to user prompts, but actively discovering
what needs to be done in its environment.

Goal discovery is a fundamental aspect of intelligence:
- A passive system waits for instructions
- An intelligent system notices what *needs* attention

The engine operates on three axes:
┌─────────────────────────────────────────────────────────────────┐
│                    GOAL DISCOVERY AXES                           │
│                                                                  │
│  X-AXIS: Scope                               Y-AXIS: Urgency    │
│  ─────────────────────                         ───────────────   │
│                                                              ╱    │
│              Long-term / Strategic                       ╱        │
│           (What should be done?)                        ╱          │
│                                                   ╱            │
│                                             ╱                │
│                                           ╱                  │
│                                    Immediate Response  ───────────→
│                              (What needs to happen NOW)       Urgency
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Goal Discovery Modes:
1. Reactive Goals — respond to user requests
2. Curiosity-Driven Goals — explore unknown territory
3. Maintenance Goals — keep the system healthy (memory, tool checks)
4. Improvement Goals — identify weaknesses and pursue them

Author: Gemini (Alpha Principal Systems Engineer)
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from alpha.foundation_model.types import Goal, GoalStatus, ThoughtKind, Belief
from alpha.foundation_model.memory_manager import MemoryManager


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DiscoveryContext:
    """State of the environment as it pertains to goal generation."""
    total_goals_discovered: int = 0
    goals_completed_today: int = 0
    time_since_last_goal_discovery_seconds: float = field(default_factory=lambda: time.time())
    
    # What the agent has recently explored (to avoid rediscovering)
    recent_topics_explored: Set[str] = field(default_factory=set)


class GoalDiscoveryEngine:
    """Autonomously discovers meaningful goals for the agent to pursue.

    The engine continuously scans multiple sources of goal generation:
    
    1. ENVIRONMENTAL OBSERVATIONS
       — "The workspace has new files" → "I should index them"
       — "A tool is failing repeatedly" → "I need to fix the failure mode"
       
    2. CURIOSITY GAPS (from world model)
       — "I know A but not B, and they seem related" 
         → "I should investigate how A and B relate"
       
    3. PERFORMANCE SIGNALS (from self-monitoring)
       — "My tool selection accuracy dropped to 60%"
         → "I should analyze my recent decisions and improve"
       
    4. EXTERNAL REQUESTS
       — User: "Write a test for X" → Goal created
       — System: "Time for maintenance cycle" → Maintenance goal
    
    5. LEARNING-DRIVEN GOALS
       — After a failure, extract the lesson into a new improvement goal

    The engine operates asynchronously alongside perception and reasoning,
    continuously adding goals to a priority queue that the agent executes.
    """

    # Goal generation categories — each represents a different "why" the agent acts
    CATEGORIES = [
        {"id": "maintenance", "name": "System Maintenance", 
         "description": "Keep the system healthy and up-to-date"},
        {"id": "exploration", "name": "Exploratory Discovery",
         "description": "Learn about unknown aspects of the environment"},
        {"id": "improvement", "name": "Self-Improvement",
         "description": "Address weaknesses and improve capabilities"},
        {"id": "knowledge_synthesis", "name": "Knowledge Synthesis",
         "description": "Connect dots between existing knowledge to form new insights"},
    ]

    def __init__(self, workspace_root: Optional[Path] = None, 
                 memory_manager: Optional[MemoryManager] = None):
        self._workspace_root = Path(workspace_root) if workspace_root else Path.cwd() / "alpha"
        
        # Persistent goal store (to persist across sessions)
        self._goal_storage_path = self._workspace_root / "goals.jsonl"
        self._stored_goals: List[Goal] = []

        # Memory manager for context-aware discovery
        self.memory_manager = memory_manager or MemoryManager()

        # Discovery state
        self.context = DiscoveryContext()

    def discover_all(self) -> List[Goal]:
        """Run full goal discovery scan across all sources.

        Returns:
            A prioritized list of discovered goals, from most urgent to least urgent.
        """
        discovered_goals: Dict[str, Goal] = {}  # Use dict to deduplicate by title
        
        # 1. Discover from environmental state
        env_goals = self._discover_from_environment()
        
        # 2. Discover from knowledge gaps (curiosity)
        curiosity_goals = self._discover_curiosity_gaps()
        
        # 3. Discover from maintenance needs
        maintenance_goals = self._discover_maintenance_needs()
        
        # 4. Discover improvement goals from past failures
        improvement_goals = self._discover_improvement_goals()
        
        # Combine and deduplicate, sort by urgency
        all_discovered = discovered_goals.values()
        seen_titles = set()
        prioritized = []
        
        for goal in sorted(all_discovered, key=lambda g: -self._compute_priority(g)):
            if goal.title not in seen_titles:
                seen_titles.add(goal.title)
                prioritized.append(goal)

        # Record this discovery cycle
        self.context.total_goals_discovered += len(prioritized)
        
        return prioritized

    def _discover_from_environment(self) -> List[Goal]:
        """Scan the environment for goals that emerge from observed state.
        
        Examples:
          - New files appear → "Catalog recent changes" goal
          - A tool call fails repeatedly → "Fix this failure mode" goal
          - Workspace is stale (last action was hours ago) → "Re-orient to current state" goal
        """
        goals = []
        
        # Check for workspace state indicators
        try:
            if (self._workspace_root / "CURRENT_WORLD_MODEL.md").exists():
                # The world model exists — maybe it's outdated?
                age_days = self._estimate_file_age(self._workspace_root / "CURRENT_WORLD_MODEL.md")
                if age_days > 7:  # More than a week old
                    goals.append(Goal(
                        title="Update World Model (stale)",
                        description=f"The CURRENT_WORLD_MODEL.md is ~{age_days:.0f} days old. "
                                    f"Scan recent changes and update the model.",
                        status=GoalStatus.PENDING,
                    ))
        except Exception:
            pass
        
        # Check for tool availability (maintenance)
        tool_check = self._check_tool_connectivity()
        if tool_check.needs_reconnect:
            goals.append(Goal(
                title="Re-establish Model Connection",
                description=tool_check.message,
                status=GoalStatus.PENDING,
            ))
        
        return goals

    def _discover_curiosity_gaps(self) -> List[Goal]:
        """Identify curiosity-driven exploration goals based on belief gaps.
        
        If the agent knows A and B but not C, where C is a known bridge between A→B,
        this creates an implicit "I should learn about C" goal.

        Simplified heuristic: periodically explore random aspects of knowledge base
        to discover connections the agent hasn't yet made.
        """
        goals = []
        
        # Sample recent beliefs — are there gaps we've noticed?
        if self.memory_manager.total_size["long_term"] > 5:
            samples = [self.memory_manager.retrieve("alpha", limit=2),
                      self.memory_manager.retrieve("filesystem", limit=1)]
            
            if len(samples[0]) + len(samples[1]) < 3:
                # There's a gap — we know about "alpha" but not much more
                goals.append(Goal(
                    title="Expand Alpha knowledge base",
                    description="We have limited knowledge about 'alpha' concepts. "
                                f"Found {len(samples[0]) + len(samples[1])} related entries. "
                                "Seek out additional information.",
                    status=GoalStatus.PENDING,
                ))

        return goals

    def _discover_maintenance_needs(self) -> List[Goal]:
        """Identify system maintenance goals."""
        goals = []
        
        # Memory cleanup goal if too much short-term memory
        recent_count = len([r for r in self.memory_manager.short_term 
                          if (utc_now() - r.created_at).total_seconds() < 3600])  # last hour
        
        if recent_count > 50:
            goals.append(Goal(
                title="Clean up short-term memory",
                description=f"Short-term memory has {recent_count} entries (>1hr old). "
                            f"Candidate for compaction.",
                status=GoalStatus.PENDING,
            ))

        # Tool health check goal
        if not self._check_tool_connectivity().is_healthy:
            goals.append(Goal(
                title="Diagnostic tool connectivity",
                description="Tools may have degraded. Run full diagnostic suite.",
                status=GoalStatus.PENDING,
            ))

        return goals

    def _discover_improvement_goals(self) -> List[Goal]:
        """Discover improvement goals from past failures and lessons."""
        goals = []
        
        # Look for failure patterns in recent experience
        failures = self.memory_manager.retrieve("failure", limit=5)
        if failures:
            # Synthesize an improvement goal from the most common failure type
            failure_keywords = [f.content.lower() for f in failures]
            keywords = ["timeout", "connection error", "permission denied"]
            
            dominant_failure = max(set(failure_keywords), 
                                   key=lambda kw: sum(1 for k in failure_keywords if kw in k))
            
            goals.append(Goal(
                title=f"Address {dominant_failure} failure mode",
                description=f"Pattern detected: {dominant_failure} errors. "
                            f"Proposed mitigation: add retry/backoff/fallback logic.",
                status=GoalStatus.PENDING,
            ))

        return goals

    def _compute_priority(self, goal: Goal) -> float:
        """Compute priority score for a goal (higher = more urgent)."""
        
        # Base priority by category
        category_boosters = {
            "maintenance": 1.0,   # Always highest priority — system health matters first
            "improvement": 0.8,   # Important but can wait until system is stable
            "exploration": 0.5,   # Nice to do when we have capacity
        }
        
        category = goal.id if hasattr(goal, 'id') else "exploration"
        base = category_boosters.get(category, 0.5)
        
        # Boost for recently discovered (recency)
        recency = min(1.0, self.context.total_goals_discovered / max(len(self._stored_goals), 1))
        priority = base * (1.0 + recency * 0.2)
        
        return priority

    def _check_tool_connectivity(self) -> ToolConnectivity:
        """Check if external tools are accessible."""
        result = ToolConnectivity()
        
        try:
            # Try to reach the model endpoint (simplified check)
            import urllib.request
            urllib.request.urlopen("http://localhost:1234/", timeout=2)
            result.is_healthy = True
            result.message = "Tools connected and healthy"
            
        except Exception as e:
            result.needs_reconnect = True
            result.message = f"Tool connection lost or unreachable: {str(e)[:100]}"
        
        return result

    def _estimate_file_age(self, path: Path) -> float:
        """Estimate how many days ago a file was last modified."""
        try:
            mtime = path.stat().st_mtime
            from datetime import datetime as dt
            age_seconds = (utc_now() - dt.fromtimestamp(mtime)).total_seconds()
            return age_seconds / 86400.0
        except Exception:
            return 999.0

    def _persist_goal(self, goal: Goal) -> None:
        """Persist a goal to disk for recovery across sessions."""
        self._stored_goals.append(goal)
        
        with open(self._goal_storage_path, "a") as f:
            f.write(json.dumps({
                "title": goal.title,
                "description": goal.description,
                "status": goal.status.value,
                "created_at": goal.created_at.isoformat(),
            }) + "\n")

    def mark_completed(self, goal_id: str) -> None:
        """Mark a goal as completed (triggers reward signaling to self-model)."""
        for i, goal in enumerate(self._stored_goals):
            if hasattr(goal, 'id') and goal.id == goal_id:
                goal.status = GoalStatus.COMPLETED
                self.context.goals_completed_today += 1
                
                # Update stored goals list
                self._stored_goals[i] = goal
                
                with open(self._goal_storage_path, "w") as f:
                    for g in self._stored_goals:
                        f.write(json.dumps({
                            "id": getattr(g, 'id', ''),
                            "title": g.title,
                            "description": g.description,
                            "status": g.status.value,
                            "created_at": str(getattr(g, 'created_at', utc_now())),
                        }) + "\n")
                return
        
        # Not in stored list — just update the current goal object's status
        pass  # In production, this would find and update an active goal


class ToolConnectivity(BaseModel):
    """Result of a tool health check."""
    is_healthy: bool = True
    needs_reconnect: bool = False
    message: str = "All systems operational"


if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = GoalDiscoveryEngine(workspace_root=Path(tmpdir))
        
        # Simulate some stored goals for testing priority computation
        engine._stored_goals = [Goal(
            title="Test goal",
            description="A test goal",
            status=GoalStatus.PENDING,
        )]
        
        print("=== Goal Discovery Demo ===\n")
        print("Scanning environment for goals...\n")
        
        goals = engine.discover_all()
        
        for i, g in enumerate(goals[:3], 1):
            print(f"{i}. [{g.status.value}] {g.title}")
            print(f"   └─ {g.description[:80]}{'...' if len(g.description) > 80 else ''}")