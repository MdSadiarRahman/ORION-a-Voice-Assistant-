"""
Agent-Client Protocol (ACP) & Event Stream for OpenHands Canvas in VoiceMate.
Manages streaming events for thoughts, terminal output, file diffs, and tool actions.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Dict, Any, Optional
import threading


class EventKind(str, Enum):
    """Canonical ACP Event Kinds from OpenHands."""
    THINKING = "thinking"
    ACTION = "action"
    TERMINAL = "terminal"
    DIFF = "diff"
    OBSERVATION = "observation"
    APPROVAL_REQUIRED = "approval_required"
    STATUS = "status"


@dataclass
class AgentEvent:
    """Represents a discrete event in the agent event stream."""
    kind: EventKind
    message: str
    source: str = "VoiceMate-OpenHands"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind.value,
            "message": self.message,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class CanvasEventStream:
    """
    Thread-safe Pub/Sub Event Stream for the Developer Canvas.
    Allows UI panels, voice output, and loggers to react to real-time events.
    """
    _instance: Optional['CanvasEventStream'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._subscribers: List[Callable[[AgentEvent], None]] = []
        self._history: List[AgentEvent] = []

    @classmethod
    def get_instance(cls) -> 'CanvasEventStream':
        with cls._lock:
            if cls._instance is None:
                cls._instance = CanvasEventStream()
            return cls._instance

    def subscribe(self, listener: Callable[[AgentEvent], None]) -> None:
        """Registers an event subscriber callback."""
        with self._lock:
            if listener not in self._subscribers:
                self._subscribers.append(listener)

    def unsubscribe(self, listener: Callable[[AgentEvent], None]) -> None:
        """Removes a subscriber."""
        with self._lock:
            if listener in self._subscribers:
                self._subscribers.remove(listener)

    def emit(self, kind: EventKind, message: str, payload: Optional[Dict[str, Any]] = None) -> AgentEvent:
        """Emits an event to all subscribers and records in history."""
        event = AgentEvent(
            kind=kind,
            message=message,
            payload=payload or {}
        )
        with self._lock:
            self._history.append(event)
            # Retain last 200 events
            if len(self._history) > 200:
                self._history.pop(0)
            listeners = list(self._subscribers)

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                pass

        return event

    def get_recent_events(self, limit: int = 50) -> List[AgentEvent]:
        """Returns the most recent events."""
        with self._lock:
            return list(self._history[-limit:])

    def clear(self) -> None:
        """Clears event history."""
        with self._lock:
            self._history.clear()
