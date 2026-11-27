"""Small in-process event stream for canvas task progress."""

import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class EventKind(str, Enum):
    THINKING = "thinking"
    PROGRESS = "progress"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass(frozen=True)
class CanvasEvent:
    kind: EventKind
    message: str


class CanvasEventStream:
    _instance: "CanvasEventStream | None" = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._listeners: list[Callable[[CanvasEvent], None]] = []
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "CanvasEventStream":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def subscribe(self, listener: Callable[[CanvasEvent], None]) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[CanvasEvent], None]) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def emit(self, kind: EventKind, message: str) -> None:
        event = CanvasEvent(kind=kind, message=message)
        with self._lock:
            listeners = tuple(self._listeners)
        for listener in listeners:
            listener(event)
