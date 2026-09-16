from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class TelemetrySink(Protocol):
    def event(self, name: str, attributes: dict[str, Any]) -> None: ...


@dataclass
class InMemoryTelemetrySink:
    events: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def event(self, name: str, attributes: dict[str, Any]) -> None:
        # Content fields are rejected by default: observability is metadata-first.
        forbidden = {"prompt", "messages", "document", "content", "raw_output"}
        intersection = forbidden.intersection(attributes)
        if intersection:
            raise ValueError(f"Sensitive content capture is disabled: {sorted(intersection)}")
        self.events.append((name, dict(attributes)))
