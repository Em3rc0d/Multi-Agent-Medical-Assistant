from __future__ import annotations

from typing import Any

from .telemetry import _validate_metadata_only

try:
    from opentelemetry import trace
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("OpenTelemetrySink requires the 'otel' extra") from exc


class OpenTelemetrySink:
    """Metadata-only OpenTelemetry adapter; sensitive content remains disabled."""

    def __init__(self, *, tracer_name: str = "eak.kernel") -> None:
        self._tracer = trace.get_tracer(tracer_name)

    def event(self, name: str, attributes: dict[str, Any]) -> None:
        _validate_metadata_only(attributes)
        normalized = {key: self._normalize(value) for key, value in attributes.items()}
        with self._tracer.start_as_current_span(name) as span:
            for key, value in normalized.items():
                span.set_attribute(f"eak.{key}", value)

    @staticmethod
    def _normalize(value: Any) -> str | bool | int | float:
        if isinstance(value, (str, bool, int, float)):
            return value
        return str(value)
