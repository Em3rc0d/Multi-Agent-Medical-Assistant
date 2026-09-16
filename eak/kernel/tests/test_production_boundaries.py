from eak_kernel.evaluation import EvaluationGate, MetricGate
from eak_kernel.model import Event, Ref
from eak_kernel.native_policy import NativePolicyAdapter, ProviderUseRule
from eak_kernel.persistence import SQLiteEventStore
from eak_kernel.telemetry import InMemoryTelemetrySink


def test_sqlite_event_store_is_ordered_and_execution_scoped(tmp_path):
    store = SQLiteEventStore(tmp_path / "events.sqlite")
    store.append(Event("A", "execution://1", {"n": 1}))
    store.append(Event("B", "execution://2", {"n": 2}))
    store.append(Event("C", "execution://1", {"n": 3}))
    assert [event.type for event in store.stream("execution://1")] == ["A", "C"]


def test_evaluation_gate_fails_closed_on_missing_or_bad_metric():
    gate = EvaluationGate((MetricGate("groundedness", ">=", 0.95), MetricGate("unsupported_rate", "<=", 0.01)))
    assert gate.evaluate({"groundedness": 0.97, "unsupported_rate": 0.0}).passed
    missing = gate.evaluate({"groundedness": 0.97})
    assert not missing.passed and "missing:unsupported_rate" in missing.failures


def test_native_policy_enforces_role_and_restricted_egress():
    adapter = NativePolicyAdapter((ProviderUseRule(
        id="restricted-medical",
        capability_prefix="medical.",
        required_roles=("clinician",),
        deny_egress_for_classifications=("restricted",),
    ),))
    capability = Ref("medical.imaging.classify", "1.0.0")
    provider = Ref("provider.remote", "1.0.0")
    denied_role = adapter.decide_provider_use(
        principal={"roles": ["viewer"]}, capability=capability, provider=provider, context={}
    )
    assert denied_role.effect == "deny"
    denied_egress = adapter.decide_provider_use(
        principal={"roles": ["clinician"]}, capability=capability, provider=provider,
        context={"dataClassification": "restricted", "providerEgress": "required"},
    )
    assert denied_egress.effect == "deny"


def test_telemetry_rejects_content_capture_by_default():
    sink = InMemoryTelemetrySink()
    sink.event("ProviderResolved", {"provider": "x", "latencyMs": 3})
    assert sink.events
    try:
        sink.event("ModelCall", {"prompt": "secret"})
    except ValueError:
        pass
    else:
        raise AssertionError("content capture should have failed")
