from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


_FORBIDDEN_CONTENT_FIELDS = {
    "prompt",
    "messages",
    "document",
    "content",
    "raw_output",
    "rawInput",
    "rawOutput",
}


def _validate_metadata_only(attributes: dict[str, Any]) -> None:
    intersection = _FORBIDDEN_CONTENT_FIELDS.intersection(attributes)
    if intersection:
        raise ValueError(f"Sensitive content capture is disabled: {sorted(intersection)}")


class TelemetrySink(Protocol):
    def event(self, name: str, attributes: dict[str, Any]) -> None: ...


@dataclass
class InMemoryTelemetrySink:
    events: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def event(self, name: str, attributes: dict[str, Any]) -> None:
        _validate_metadata_only(attributes)
        self.events.append((name, dict(attributes)))
