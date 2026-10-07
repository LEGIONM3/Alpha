"""Agent Communication Bus: Central messaging switchboard, pub/sub, broadcast, and audit log."""

import threading
import time
from typing import Dict, List, Optional, Callable, Any
from alpha.agents.communication.messages import AgentMessage, MessageType, MessagePriority
from alpha.agents.communication.mailbox import AgentMailbox

class AgentMessageBus:
    """Enterprise-grade message bus for the cognitive civilization."""

    def __init__(self):
        self._mailboxes: Dict[str, AgentMailbox] = {}
        self._agent_roles: Dict[str, str] = {}
        self._topic_subscribers: Dict[str, List[str]] = {}  # topic -> list of agent_ids
        self._audit_log: List[AgentMessage] = []
        self._waiting_correlations: Dict[str, threading.Event] = {}
        self._correlation_responses: Dict[str, AgentMessage] = {}
        self._lock = threading.RLock()

    def register_agent(self, agent_id: str, role: str) -> AgentMailbox:
        """Register an agent with the message bus and return its mailbox."""
        with self._lock:
            if agent_id not in self._mailboxes:
                self._mailboxes[agent_id] = AgentMailbox(agent_id=agent_id)
            self._agent_roles[agent_id] = role
            return self._mailboxes[agent_id]

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        with self._lock:
            self._mailboxes.pop(agent_id, None)
            self._agent_roles.pop(agent_id, None)
            for subscribers in self._topic_subscribers.values():
                if agent_id in subscribers:
                    subscribers.remove(agent_id)

    def get_mailbox(self, agent_id: str) -> Optional[AgentMailbox]:
        with self._lock:
            return self._mailboxes.get(agent_id)

    def subscribe_topic(self, topic: str, agent_id: str) -> None:
        """Subscribe agent to a broadcast topic."""
        with self._lock:
            if topic not in self._topic_subscribers:
                self._topic_subscribers[topic] = []
            if agent_id not in self._topic_subscribers[topic]:
                self._topic_subscribers[topic].append(agent_id)

    def publish_topic(self, topic: str, message: AgentMessage) -> int:
        """Publish message to all subscribers of a topic."""
        with self._lock:
            subscribers = list(self._topic_subscribers.get(topic, []))
            count = 0
            for sub_id in subscribers:
                if sub_id != message.sender_id:
                    mbox = self._mailboxes.get(sub_id)
                    if mbox:
                        mbox.receive(message)
                        count += 1
            self._record_audit(message)
            return count

    def send(self, message: AgentMessage) -> bool:
        """Deliver a message to a specific agent or broadcast."""
        if not message.verify_integrity():
            raise ValueError(f"Message {message.message_id} failed cryptographic integrity check")

        with self._lock:
            # Check if this resolves a pending synchronous correlation
            if message.correlation_id and message.correlation_id in self._waiting_correlations:
                self._correlation_responses[message.correlation_id] = message
                self._waiting_correlations[message.correlation_id].set()

            # Record outgoing in sender mailbox if sender exists
            sender_mbox = self._mailboxes.get(message.sender_id)
            if sender_mbox:
                sender_mbox.record_sent(message)

            self._record_audit(message)

            if message.recipient_id == "*":
                # Broadcast
                for aid, mbox in self._mailboxes.items():
                    if aid != message.sender_id:
                        mbox.receive(message)
                return True
            else:
                target_mbox = self._mailboxes.get(message.recipient_id)
                if target_mbox:
                    target_mbox.receive(message)
                    return True
                return False

    def broadcast(self, message: AgentMessage, role_filter: Optional[str] = None) -> int:
        """Broadcast message to all agents matching an optional role filter."""
        message.recipient_id = "*"
        if not message.verify_integrity():
            raise ValueError(f"Message {message.message_id} failed cryptographic integrity check")

        delivered = 0
        with self._lock:
            self._record_audit(message)
            sender_mbox = self._mailboxes.get(message.sender_id)
            if sender_mbox:
                sender_mbox.record_sent(message)

            for aid, mbox in self._mailboxes.items():
                if aid == message.sender_id:
                    continue
                if role_filter and self._agent_roles.get(aid) != role_filter:
                    continue
                mbox.receive(message)
                delivered += 1
        return delivered

    def send_and_wait(self, request_msg: AgentMessage, timeout: float = 5.0) -> Optional[AgentMessage]:
        """Send a request and synchronously wait for matching response."""
        corr_id = request_msg.message_id
        request_msg.correlation_id = corr_id
        evt = threading.Event()

        with self._lock:
            self._waiting_correlations[corr_id] = evt

        try:
            delivered = self.send(request_msg)
            if not delivered:
                return None
            signaled = evt.wait(timeout=timeout)
            if signaled:
                with self._lock:
                    return self._correlation_responses.pop(corr_id, None)
            return None
        finally:
            with self._lock:
                self._waiting_correlations.pop(corr_id, None)

    def _record_audit(self, message: AgentMessage) -> None:
        self._audit_log.append(message)

    def get_audit_trail(
        self,
        trace_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        msg_type: Optional[MessageType] = None
    ) -> List[AgentMessage]:
        """Query messages from the persistent audit trail."""
        with self._lock:
            results = self._audit_log
            if trace_id:
                results = [m for m in results if m.trace_id == trace_id]
            if sender_id:
                results = [m for m in results if m.sender_id == sender_id]
            if recipient_id:
                results = [m for m in results if m.recipient_id in (recipient_id, "*")]
            if msg_type:
                results = [m for m in results if m.message_type == msg_type]
            return list(results)
