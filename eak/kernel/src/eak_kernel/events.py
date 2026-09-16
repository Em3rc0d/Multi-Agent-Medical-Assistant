from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .model import Event


class EventStore(Protocol):
    deployment_tier: str

    def append(self, event: Event) -> None: ...
    def stream(self, execution_id: str) -> tuple[Event, ...]: ...


@dataclass
class InMemoryEventStore:
    deployment_tier = "test"
    _events: list[Event] = field(default_factory=list)

    def append(self, event: Event) -> None:
        self._events.append(event)

    def stream(self, execution_id: str) -> tuple[Event, ...]:
        return tuple(event for event in self._events if event.execution_id == execution_id)
