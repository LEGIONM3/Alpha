"""Project Alpha: Autonomous Continuation Layer (Phases 1-8).

Ensures Alpha's resident foundation model never halts after an analysis.
Owns continuous execution:
Read -> Analyze -> Audit -> Generate Findings -> Generate Next Action -> Runtime Executes -> Model Continues.

Key Subsystems:
1. MissionExecutor (Owns continuation lifecycle)
2. NextActionContract (Enforces mandatory NEXT_ACTION block)
3. InvestigationQueue (Priority queue that never becomes empty)
4. StatefulResponsesClient (Chains response_id via http://localhost:1234/v1/responses)
5. ChiefCognitiveAuditor (Permanent cognitive auditing role)
6. MissionState (Persists and reloads MISSION_STATE.json)
7. SelfGeneratedWork (Autonomous synthesis when queue drains)
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from alpha.core.perception import PerceptionBus, PerceptionEventType
from alpha.core.awareness import AwarenessManager

logger = logging.getLogger("alpha.core.continuation")


# =============================================================================
# Phase 2: Mandatory Next Action Contract
# =============================================================================

class NextActionContract(BaseModel):
    """Mandatory structured next action emitted by cognitive investigations."""
    action: str = Field(description="Action verb e.g. investigate, audit, verify, contradiction_search")
    target: str = Field(description="Target file, component, belief, or hypothesis")
    priority: str = Field(default="high", description="critical, high, medium, low")
    reason: str = Field(description="Epistemic or architectural rationale")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# =============================================================================
# Phase 3: Investigation Queue
# =============================================================================

class InvestigationItem(BaseModel):
    item_id: str
    action: str
    target: str
    priority_level: int = 2  # 0=critical, 1=high, 2=medium, 3=low
    priority_label: str = "high"
    reason: str
    created_at: float = Field(default_factory=time.time)
    source: str = "continuation_engine"

    def __lt__(self, other: InvestigationItem) -> bool:
        return self.priority_level < other.priority_level


class InvestigationQueue:
    """Thread-safe priority queue for autonomous investigations. Never empties."""

    PRIORITY_MAP = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3
    }

    def __init__(self, workspace_root: Optional[Path] = None):
        self._lock = threading.RLock()
        self._queue: queue.PriorityQueue[InvestigationItem] = queue.PriorityQueue()
        self._items_seen: set = set()
        self.workspace_root = workspace_root or Path.cwd()

        # Seed initial work
        self._seed_default_work()

    def _seed_default_work(self) -> None:
        """Seed core architectural targets for initial investigations."""
        seeds = [
            ("audit", "alpha/core/identity.py", "critical", "Verify invariant constitution loading and SHA-256 hash preservation"),
            ("verify", "alpha/world_model/model.py", "critical", "Audit entity graph relationships and belief formation logic"),
            ("contradiction_search", "CURRENT_TRUTH_LAYER.md", "high", "Search for conflicting epistemic claims against evidence registry"),
            ("investigate", "alpha/memory/embedding_service.py", "high", "Verify vector normalization and cache coherency"),
            ("audit", "THREAD_BOUNDARY_MAP.md", "critical", "Confirm UI-cognition decoupling across all dispatch paths"),
            ("weakness_search", "alpha/agents/governance/governance.py", "high", "Check drift thresholds and amendment voting invariants")
        ]
        for action, target, priority, reason in seeds:
            self.push(action, target, priority, reason, source="bootstrap_seed")

    def push(self, action: str, target: str, priority: str, reason: str, source: str = "model_generated") -> None:
        with self._lock:
            key = f"{action}:{target}"
            pri_level = self.PRIORITY_MAP.get(priority.lower(), 2)
            item = InvestigationItem(
                item_id=f"inv-{int(time.time()*1000)%1000000}",
                action=action,
                target=target,
                priority_level=pri_level,
                priority_label=priority,
                reason=reason,
                source=source
            )
            self._queue.put(item)
            self._items_seen.add(key)

    def pop(self) -> InvestigationItem:
        with self._lock:
            if self._queue.empty():
                self._replenish_from_reality_gaps()
            return self._queue.get()

    def is_empty(self) -> bool:
        with self._lock:
            return self._queue.empty()

    def size(self) -> int:
        with self._lock:
            return self._queue.qsize()

    def _replenish_from_reality_gaps(self) -> None:
        """Phase 8: Automatically generates work from architecture gaps and files."""
        candidates = [
            ("audit", "alpha/core/awareness.py", "high", "Inspect ACTIVE_COGNITIVE_STATE persistence invariants"),
            ("verify", "alpha/agents/self_monitoring.py", "high", "Verify health audit metrics and dead component detection"),
            ("contradiction_search", "ARCHITECTURAL_REALITY_REPORT.md", "high", "Audit claimed subsystems against on-disk reality"),
            ("audit", "alpha/reflection/commentary.py", "medium", "Check structured thought logging and latency percentiles"),
            ("investigate", "alpha/core/autonomous_thought.py", "critical", "Validate continuous thought engine throughput and memory commits")
        ]
        # Look for python files in workspace
        for p in self.workspace_root.glob("alpha/**/*.py"):
            rel_p = str(p.relative_to(self.workspace_root)).replace("\\", "/")
            if rel_p not in self._items_seen:
                candidates.append(("audit", rel_p, "medium", f"Continuous architectural audit of {rel_p}"))
                if len(candidates) >= 15:
                    break

        for action, target, pri, reason in candidates:
            self.push(action, target, pri, reason, source="self_generated_gap_fill")


# =============================================================================
# Phase 5: Stateful LM Studio Responses Client
# =============================================================================

class StatefulResponsesClient:
    """Invokes http://localhost:1234/v1/responses with response_id stateful chaining."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "gemma-4-e4b-it-ultra-uncensored-heretic",
        timeout_seconds: float = 45.0
    ):
        self.base_url = base_url.rstrip("/")
        self.responses_url = f"{self.base_url}/responses"
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.last_response_id: Optional[str] = None

    def invoke(
        self,
        user_prompt: str,
        system_instructions: Optional[str] = None,
        use_previous_response: bool = True
    ) -> Dict[str, Any]:
        """Submits stateful investigation prompt to /v1/responses."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "input": user_prompt
        }
        if system_instructions:
            payload["instructions"] = system_instructions
        if use_previous_response and self.last_response_id:
            payload["previous_response_id"] = self.last_response_id

        t0 = time.time()
        try:
            req = urllib.request.Request(
                self.responses_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency = round((time.time() - t0) * 1000.0, 1)

                resp_id = data.get("id")
                if resp_id:
                    self.last_response_id = resp_id

                # Extract text output
                text_content = ""
                reasoning_content = ""
                for out_item in data.get("output", []):
                    if out_item.get("type") == "message":
                        for c in out_item.get("content", []):
                            if c.get("type") == "output_text":
                                text_content += c.get("text", "")
                    elif out_item.get("type") == "reasoning":
                        for c in out_item.get("content", []):
                            if c.get("type") == "reasoning_text":
                                reasoning_content += c.get("text", "")

                return {
                    "success": True,
                    "response_id": resp_id,
                    "previous_response_id": data.get("previous_response_id"),
                    "content": text_content.strip() or reasoning_content.strip(),
                    "reasoning": reasoning_content.strip(),
                    "latency_ms": latency,
                    "raw": data
                }
        except Exception as exc:
            logger.warning(f"Responses API call failed ({exc}), attempting chat/completions fallback...")
            # Graceful fallback to chat/completions if responses API has transient socket error
            return self._fallback_chat_completions(user_prompt, system_instructions, t0)

    def _fallback_chat_completions(
        self,
        prompt: str,
        system_instructions: Optional[str],
        t0: float
    ) -> Dict[str, Any]:
        chat_url = f"{self.base_url}/chat/completions"
        msgs = []
        if system_instructions:
            msgs.append({"role": "system", "content": system_instructions})
        msgs.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": 1200,
            "temperature": 0.2
        }
        req = urllib.request.Request(
            chat_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency = round((time.time() - t0) * 1000.0, 1)
                msg = data["choices"][0]["message"]
                content = (msg.get("content") or msg.get("reasoning_content") or "").strip()
                new_id = data.get("id", f"resp-fallback-{int(time.time())}")
                self.last_response_id = new_id
                return {
                    "success": True,
                    "response_id": new_id,
                    "previous_response_id": None,
                    "content": content,
                    "reasoning": msg.get("reasoning_content", ""),
                    "latency_ms": latency,
                    "raw": data
                }
        except Exception as exc:
            logger.error(f"Chat completions fallback encountered error: {exc}")
            synth_content = (
                "NEXT_ACTION:\n{\n"
                '  "action": "verify",\n'
                '  "target": "alpha/core/identity.py",\n'
                '  "priority": "high",\n'
                f'  "reason": "Recover from transient socket latency: {str(exc)[:50]}"\n'
                "}"
            )
            return {
                "success": False,
                "response_id": f"resp-recovered-{int(time.time())}",
                "previous_response_id": None,
                "content": synth_content,
                "reasoning": "",
                "latency_ms": round((time.time() - t0) * 1000.0, 1),
                "raw": {}
            }


# =============================================================================
# Phase 6 & Phase 7: Chief Cognitive Auditor & Mission Persistence
# =============================================================================

CHIEF_COGNITIVE_AUDITOR_INSTRUCTIONS = """You are Alpha's Chief Cognitive Auditor.
Your permanent role is to rigorously inspect and evaluate Project Alpha's architecture, world model, memory systems, agent society, safety invariants, and epistemic truth layers.

RULES OF ENGAGEMENT:
1. NEVER write "analysis complete" or "task finished".
2. Always identify:
   - Specific Architectural Weaknesses
   - Epistemic Risks or Ungrounded Assumptions
   - Contradictions with Reality
   - Immediate Follow-up Tasks
3. MANDATORY CONTRACT:
   Every single investigation response MUST end with a valid NEXT_ACTION JSON block in the exact format:
   NEXT_ACTION:
   {
     "action": "investigate" | "audit" | "verify" | "contradiction_search",
     "target": "<target_file_or_component>",
     "priority": "critical" | "high" | "medium",
     "reason": "<precise_epistemic_reason>"
   }

If uncertain, generate verification work.
If verification is complete, generate contradiction search work.
If contradiction search is complete, generate architecture audit work.
Never allow a terminal state."""


class MissionState(BaseModel):
    """The persistent state of ongoing autonomous mission investigations."""
    current_mission: str = "Transition Alpha into a persistent autonomous cognitive system"
    current_investigation: str = "Architecture Verification and Grounding Audit"
    current_target: str = "alpha/core/identity.py"
    current_risks: List[str] = Field(default_factory=list)
    current_hypotheses: List[str] = Field(default_factory=list)
    current_weaknesses: List[str] = Field(default_factory=list)
    current_opportunities: List[str] = Field(default_factory=list)
    last_model_response: str = ""
    next_planned_action: Dict[str, Any] = Field(default_factory=dict)
    last_response_id: Optional[str] = None
    investigations_completed: int = 0
    investigation_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: float = Field(default_factory=time.time)


# =============================================================================
# Phase 1: Mission Executor (Owns Continuation)
# =============================================================================

class MissionExecutor:
    """The master executor driving continuous autonomous cognitive continuation.

    MissionExecutor owns continuation. The model does not.
    """

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        perception_bus: Optional[PerceptionBus] = None,
        awareness_manager: Optional[AwarenessManager] = None,
        state_file: str = "MISSION_STATE.json",
        model_url: str = "http://localhost:1234/v1",
        default_model: str = "gemma-4-e4b-it-ultra-uncensored-heretic",
        cycle_delay_seconds: float = 3.0
    ):
        self._lock = threading.RLock()
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.perception_bus = perception_bus
        self.awareness_manager = awareness_manager
        self.state_file = self.workspace_root / state_file
        self.cycle_delay_seconds = cycle_delay_seconds

        self.queue = InvestigationQueue(workspace_root=self.workspace_root)
        self.client = StatefulResponsesClient(base_url=model_url, model=default_model)
        self.state = self._load_or_create_state()

        self._is_running = False
        self._thread: Optional[threading.Thread] = None

    def _load_or_create_state(self) -> MissionState:
        """Phase 7: Reloads MISSION_STATE.json automatically on restart."""
        with self._lock:
            if self.state_file.exists():
                try:
                    data = json.loads(self.state_file.read_text(encoding="utf-8"))
                    state = MissionState(**data)
                    self.client.last_response_id = state.last_response_id
                    logger.info(f"Reloaded MISSION_STATE.json: {state.investigations_completed} investigations on record.")
                    return state
                except Exception as ex:
                    logger.warning(f"Could not parse existing MISSION_STATE.json ({ex}), initializing fresh.")
            state = MissionState()
            self._save_state(state)
            return state

    def _save_state(self, state: MissionState) -> None:
        """Atomically saves state to MISSION_STATE.json."""
        with self._lock:
            state.last_updated = time.time()
            data = state.model_dump()
            try:
                tmp = self.state_file.with_suffix(".tmp")
                tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
                tmp.replace(self.state_file)
            except Exception as ex:
                logger.error(f"Failed to write {self.state_file}: {ex}")

    def parse_next_action(self, model_output: str) -> Optional[NextActionContract]:
        """Extracts NEXT_ACTION JSON block from model response."""
        try:
            # Pattern 1: NEXT_ACTION:\n{...}
            match = re.search(r"NEXT_ACTION:\s*(\{.*?\})", model_output, re.DOTALL)
            if match:
                raw_json = match.group(1).strip()
                data = json.loads(raw_json)
                return NextActionContract(**data)

            # Pattern 2: ```json\n{..."action": ...}\n```
            match_json = re.search(r"```json\s*(\{.*?\})\s*```", model_output, re.DOTALL)
            if match_json:
                data = json.loads(match_json.group(1).strip())
                if "action" in data and "target" in data:
                    return NextActionContract(**data)
        except Exception:
            pass
        return None

    def execute_next_task(self, item: InvestigationItem) -> Dict[str, Any]:
        """Phase 1 & Phase 4: Executes a single investigation step and reinvokes the model."""
        with self._lock:
            logger.info(f"Executing Investigation: [{item.action}] target='{item.target}' (pri={item.priority_label})")

            # 1. Load target content
            target_path = self.workspace_root / item.target
            target_content = "(Target content not found on disk)"
            if target_path.exists():
                try:
                    if target_path.is_file():
                        # Read first 120 lines to stay within prompt budgets
                        lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines()[:120]
                        target_content = "\n".join(lines)
                except Exception as ex:
                    target_content = f"Error reading target: {ex}"

            # 2. Construct Prompt for Chief Cognitive Auditor
            prompt = (
                f"### CURRENT INVESTIGATION TARGET\n"
                f"- Action: {item.action.upper()}\n"
                f"- Target: {item.target}\n"
                f"- Priority: {item.priority_label}\n"
                f"- Rationale: {item.reason}\n\n"
                f"### TARGET CONTENT EXCERPT\n"
                f"```\n{target_content[:3000]}\n```\n\n"
                f"### REQUIRED AUDIT TASKS\n"
                f"1. Perform an architectural and epistemic critique of this target.\n"
                f"2. Explicitly identify Risks, Weaknesses, and Missing Integrations.\n"
                f"3. Generate the mandatory NEXT_ACTION JSON block pointing to the next target.\n"
            )

            # 3. Model Invocation (Phase 5: stateful chaining with previous_response_id)
            resp = self.client.invoke(
                user_prompt=prompt,
                system_instructions=CHIEF_COGNITIVE_AUDITOR_INSTRUCTIONS,
                use_previous_response=True
            )

            model_output = resp.get("content", "")

            # 4. Parse NEXT_ACTION (Phase 2 Contract)
            next_action = self.parse_next_action(model_output)
            if not next_action:
                # If model failed to emit valid NEXT_ACTION, enforce fallback work so we never halt
                logger.warning("Model omitted valid NEXT_ACTION block. Enforcing synthetic continuation contract.")
                next_action = NextActionContract(
                    action="verify",
                    target=item.target,
                    priority="high",
                    reason="Verify epistemic grounding following unstructured audit response"
                )

            # 5. Extract findings, risks, and weaknesses from text
            weaknesses_found = [line.strip("- ") for line in model_output.splitlines() if "weakness" in line.lower() or "risk" in line.lower()][:3]

            # 6. Update Mission State (Phase 7)
            self.state.investigations_completed += 1
            self.state.current_investigation = f"Audit of {item.target}"
            self.state.current_target = item.target
            self.state.last_model_response = model_output[:500] + "..." if len(model_output) > 500 else model_output
            self.state.last_response_id = resp.get("response_id")
            self.state.next_planned_action = next_action.to_dict()
            if weaknesses_found:
                self.state.current_weaknesses.extend(weaknesses_found)
                self.state.current_weaknesses = self.state.current_weaknesses[-10:]

            record = {
                "step": self.state.investigations_completed,
                "timestamp": time.time(),
                "action": item.action,
                "target": item.target,
                "latency_ms": resp.get("latency_ms", 0),
                "response_id": resp.get("response_id"),
                "next_action": next_action.to_dict()
            }
            self.state.investigation_history.append(record)
            if len(self.state.investigation_history) > 50:
                self.state.investigation_history = self.state.investigation_history[-50:]

            self._save_state(self.state)

            # 7. Update Awareness & Workspace if manager available
            if self.awareness_manager:
                self.awareness_manager.record_observation(f"Audited {item.target}: Next target -> {next_action.target} ({next_action.action})")
                self.awareness_manager.update_focus(f"Investigating {next_action.target}")
                self.awareness_manager.record_pending_action(f"{next_action.action} on {next_action.target}")

            # 8. Feed follow-up tasks into InvestigationQueue (Phase 3)
            # Add model's chosen next action
            self.queue.push(
                action=next_action.action,
                target=next_action.target,
                priority=next_action.priority,
                reason=next_action.reason,
                source="model_contract"
            )
            # Add automatic verification & contradiction search branches
            self.queue.push(
                action="contradiction_search",
                target=item.target,
                priority="medium",
                reason=f"Epistemic check for contradictory assertions in {item.target}",
                source="autonomous_branching"
            )

            # 9. Emit perception event
            if self.perception_bus:
                self.perception_bus.publish(
                    event_type=PerceptionEventType.TASK_COMPLETION,
                    source="MissionExecutor",
                    title=f"Audit completed for {item.target} -> Next: {next_action.target}",
                    data=record,
                    significance=0.6
                )

            return {
                "item": item.model_dump(),
                "response_id": resp.get("response_id"),
                "next_action": next_action.to_dict(),
                "latency_ms": resp.get("latency_ms"),
                "content_preview": model_output[:250]
            }

    def start(self) -> None:
        """Start the continuous autonomous execution thread."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._thread = threading.Thread(
                target=self._run_loop,
                name="AlphaMissionExecutor-ContinuationThread",
                daemon=True
            )
            self._thread.start()
            logger.info("MissionExecutor continuation loop launched.")

    def stop(self) -> None:
        """Stop continuation loop cleanly."""
        with self._lock:
            self._is_running = False

    def _run_loop(self) -> None:
        """Continuous execution loop: pops task, invokes model, pushes next actions, repeats indefinitely."""
        logger.info("MissionExecutor continuous continuation loop running indefinitely...")
        while self._is_running:
            try:
                item = self.queue.pop()
                self.execute_next_task(item)
            except Exception as exc:
                logger.error(f"Error in MissionExecutor step: {exc}", exc_info=True)
                if self.perception_bus:
                    self.perception_bus.publish(
                        event_type=PerceptionEventType.RUNTIME_ERROR,
                        source="MissionExecutor",
                        title=f"Continuation error: {str(exc)}",
                        significance=0.7
                    )
            time.sleep(self.cycle_delay_seconds)
