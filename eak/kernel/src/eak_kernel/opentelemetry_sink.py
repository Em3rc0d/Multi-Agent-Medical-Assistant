from __future__ import annotations

from typing import Any


_FORBIDDEN_CONTENT_FIELDS = {"prompt", "messages", "document", "content", "raw_output"}


class OpenTelemetryTelemetrySink:
    """Metadata-only OpenTelemetry event sink.

    Events attach to the current span. The kernel intentionally does not create
    transport/exporter configuration; deployments own their SDK/collector setup.
    """

    def __init__(self, tracer_name: str = "eak.kernel") -> None:
        try:
            from opentelemetry import trace
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install eak-kernel[observability] to use OpenTelemetry") from exc
        self._trace = trace
        self._tracer = trace.get_tracer(tracer_name)

    @staticmethod
    def _validate(attributes: dict[str, Any]) -> None:
        intersection = _FORBIDDEN_CONTENT_FIELDS.intersection(attributes)
        if intersection:
            raise ValueError(f"Sensitive content capture is disabled: {sorted(intersection)}")

    def event(self, name: str, attributes: dict[str, Any]) -> None:
        self._validate(attributes)
        span = self._trace.get_current_span()
        span.add_event(name, attributes=dict(attributes))
