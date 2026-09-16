from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Mapping, Protocol


_FORBIDDEN_CONTENT_KEYS = {"prompt", "messages", "document", "content", "raw_output"}


def _reject_sensitive_content(value: Any, *, path: str = "attributes") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in _FORBIDDEN_CONTENT_KEYS:
                raise ValueError(f"Sensitive content capture is disabled: {path}.{key_text}")
            _reject_sensitive_content(child, path=f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_sensitive_content(child, path=f"{path}[{index}]")


class TelemetrySink(Protocol):
    deployment_tier: str

    def event(self, name: str, attributes: dict[str, Any]) -> None: ...


@dataclass
class InMemoryTelemetrySink:
    deployment_tier = "test"
    events: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def event(self, name: str, attributes: dict[str, Any]) -> None:
        _reject_sensitive_content(attributes)
        self.events.append((name, dict(attributes)))


class JsonLinesTelemetrySink:
    """Metadata-only durable local sink for engineering deployments."""

    deployment_tier = "local-durable"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def event(self, name: str, attributes: dict[str, Any]) -> None:
        _reject_sensitive_content(attributes)
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "attributes": dict(attributes),
        }
        encoded = json.dumps(record, separators=(",", ":"), sort_keys=True)
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(encoded + "\n")
