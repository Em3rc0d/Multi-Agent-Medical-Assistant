import pytest


def test_opentelemetry_sink_rejects_sensitive_content():
    pytest.importorskip("opentelemetry")
    from eak_kernel.opentelemetry_sink import OpenTelemetryTelemetrySink

    sink = OpenTelemetryTelemetrySink()
    sink.event("ProviderResolved", {"providerId": "provider.test", "latencyMs": 5})
    with pytest.raises(ValueError):
        sink.event("ModelCall", {"prompt": "sensitive"})
