"""Agent Mailbox: Priority-queued inbox, outbox, and delivery filtering."""

import threading
import queue
from typing import List, Optional, Callable
from alpha.agents.communication.messages import AgentMessage, MessagePriority, MessageType

class AgentMailbox:
    """Mailbox for a single agent with priority ordering and audit log."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # We store tuples of (priority_int, timestamp, AgentMessage) in priority queue
        self._inbox = queue.PriorityQueue()
        self._outbox: List[AgentMessage] = []
        self._received_history: List[AgentMessage] = []
        self._lock = threading.Lock()

    def receive(self, message: AgentMessage) -> None:
        """Enqueue an incoming message into the priority inbox."""
        with self._lock:
            # lower priority value means higher priority (0=CRITICAL, 3=LOW)
            self._inbox.put((message.priority.value, message.created_at, message))
            self._received_history.append(message)

    def pop_next(self, block: bool = False, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Fetch the highest priority unread message."""
        try:
            _, _, msg = self._inbox.get(block=block, timeout=timeout)
            return msg
        except queue.Empty:
            return None

    def record_sent(self, message: AgentMessage) -> None:
        """Record an outgoing message in the agent's outbox."""
        with self._lock:
            self._outbox.append(message)

    def peek_unread_count(self) -> int:
        """Return the number of waiting messages in the priority inbox."""
        return self._inbox.qsize()

    def get_history(self, filter_fn: Optional[Callable[[AgentMessage], bool]] = None) -> List[AgentMessage]:
        """Get copy of all messages received by this mailbox."""
        with self._lock:
            if filter_fn:
                return [m for m in self._received_history if filter_fn(m)]
            return list(self._received_history)

    def get_outbox(self) -> List[AgentMessage]:
        """Get copy of sent messages."""
        with self._lock:
            return list(self._outbox)
