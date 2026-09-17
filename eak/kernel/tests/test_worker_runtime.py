import pytest

from eak_kernel.events import InMemoryEventStore
from eak_kernel.invocation import InvocationRequest, InvocationResult, InvokerRegistry
from eak_kernel.model import Ref
from eak_kernel.queue import SQLiteWorkQueue
from eak_kernel.telemetry import InMemoryTelemetrySink
from eak_kernel.worker import InvocationDispatcher, InvocationWorker, invocation_from_payload, invocation_to_payload


class SuccessfulInvoker:
    def invoke(self, request: InvocationRequest) -> InvocationResult:
        return InvocationResult(
            status="SUCCEEDED",
            output_artifacts=("artifact://sha256/abc",),
            evidence_refs=("evidence://1",),
            metadata={"bounded": True},
        )


class FailingInvoker:
    def invoke(self, request: InvocationRequest) -> InvocationResult:
        raise RuntimeError("provider failed")


def request(*, side_effecting=False, idempotency_key=None):
    return InvocationRequest(
        execution_id="execution://1",
        node_id="node-a",
        capability=Ref("document.parse", "1.0.0"),
        provider=Ref("provider.test", "1.0.0"),
        inputs=("artifact://input",),
        context={"sideEffecting": side_effecting},
        idempotency_key=idempotency_key,
    )


def test_invocation_payload_round_trip():
    original = request(idempotency_key="idem-1")
    assert invocation_from_payload(invocation_to_payload(original)) == original


def test_dispatcher_requires_idempotency_for_side_effects(tmp_path):
    dispatcher = InvocationDispatcher(SQLiteWorkQueue(tmp_path / "queue.sqlite"))
    with pytest.raises(ValueError):
        dispatcher.submit(request(side_effecting=True))
    item = dispatcher.submit(request(side_effecting=True, idempotency_key="idem-1"))
    assert item.state == "QUEUED"


def test_worker_invokes_acks_audits_and_emits_metadata_only_telemetry(tmp_path):
    queue = SQLiteWorkQueue(tmp_path / "queue.sqlite")
    dispatcher = InvocationDispatcher(queue)
    dispatcher.submit(request(idempotency_key="idem-1"))
    registry = InvokerRegistry()
    registry.register(Ref("provider.test", "1.0.0"), SuccessfulInvoker())
    events = InMemoryEventStore()
    telemetry = InMemoryTelemetrySink()
    worker = InvocationWorker(queue, registry, events, telemetry)
    result = worker.run_once(worker_id="worker-a")
    assert result is not None and result.status == "SUCCEEDED"
    assert [event.type for event in events.stream("execution://1")] == [
        "ProviderInvocationStarted", "ProviderInvocationCompleted"
    ]
    assert [name for name, _ in telemetry.events] == [
        "ProviderInvocationStarted", "ProviderInvocationCompleted"
    ]
    assert queue.lease(worker_id="worker-b") is None


def test_worker_failure_is_audited_and_requeued(tmp_path):
    queue = SQLiteWorkQueue(tmp_path / "queue.sqlite")
    dispatcher = InvocationDispatcher(queue)
    item = dispatcher.submit(request(), max_attempts=2)
    registry = InvokerRegistry()
    registry.register(Ref("provider.test", "1.0.0"), FailingInvoker())
    events = InMemoryEventStore()
    worker = InvocationWorker(queue, registry, events)
    with pytest.raises(RuntimeError):
        worker.run_once(worker_id="worker-a")
    assert queue.get(item.id).state == "QUEUED"
    assert [event.type for event in events.stream("execution://1")] == [
        "ProviderInvocationStarted", "ProviderInvocationFailed"
    ]
