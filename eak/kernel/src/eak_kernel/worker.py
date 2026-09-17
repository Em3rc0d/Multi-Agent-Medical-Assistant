from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .events import EventStore
from .invocation import InvocationRequest, InvocationResult, InvokerRegistry
from .model import Event, Ref
from .queue import WorkItem, WorkQueue
from .telemetry import TelemetrySink


def invocation_to_payload(request: InvocationRequest) -> dict[str, Any]:
    return {
        "executionId": request.execution_id,
        "nodeId": request.node_id,
        "capability": request.capability.as_dict(),
        "provider": request.provider.as_dict(),
        "inputs": list(request.inputs),
        "context": dict(request.context),
        "idempotencyKey": request.idempotency_key,
    }


def invocation_from_payload(payload: Mapping[str, Any]) -> InvocationRequest:
    return InvocationRequest(
        execution_id=str(payload["executionId"]),
        node_id=str(payload["nodeId"]),
        capability=Ref.from_dict(payload["capability"]),
        provider=Ref.from_dict(payload["provider"]),
        inputs=tuple(str(value) for value in payload.get("inputs", ())),
        context=dict(payload.get("context", {})),
        idempotency_key=(
            None if payload.get("idempotencyKey") is None else str(payload["idempotencyKey"])
        ),
    )


@dataclass
class InvocationDispatcher:
    queue: WorkQueue

    def submit(self, request: InvocationRequest, *, max_attempts: int = 3) -> WorkItem:
        if request.context.get("sideEffecting") and not request.idempotency_key:
            raise ValueError("Side-effecting invocations require an idempotency key")
        return self.queue.enqueue(
            execution_id=request.execution_id,
            node_id=request.node_id,
            payload=invocation_to_payload(request),
            max_attempts=max_attempts,
        )


@dataclass
class InvocationWorker:
    queue: WorkQueue
    invokers: InvokerRegistry
    events: EventStore
    telemetry: TelemetrySink | None = None

    def run_once(self, *, worker_id: str, lease_seconds: float = 30.0) -> InvocationResult | None:
        item = self.queue.lease(worker_id=worker_id, lease_seconds=lease_seconds)
        if item is None:
            return None
        request = invocation_from_payload(item.payload)
        attributes = {
            "executionId": request.execution_id,
            "nodeId": request.node_id,
            "providerId": request.provider.id,
            "providerVersion": request.provider.version,
            "attempt": item.attempts,
        }
        self.events.append(Event("ProviderInvocationStarted", request.execution_id, attributes))
        if self.telemetry is not None:
            self.telemetry.event("ProviderInvocationStarted", dict(attributes))
        try:
            invoker = self.invokers.get(request.provider)
            result = invoker.invoke(request)
        except Exception as exc:
            failed = {**attributes, "errorType": type(exc).__name__}
            self.events.append(Event("ProviderInvocationFailed", request.execution_id, failed))
            if self.telemetry is not None:
                self.telemetry.event("ProviderInvocationFailed", dict(failed))
            self.queue.nack(item_id=item.id, worker_id=worker_id)
            raise
        if result.status.upper() not in {"SUCCEEDED", "SUCCESS"}:
            failed = {**attributes, "status": result.status}
            self.events.append(Event("ProviderInvocationFailed", request.execution_id, failed))
            if self.telemetry is not None:
                self.telemetry.event("ProviderInvocationFailed", dict(failed))
            self.queue.nack(item_id=item.id, worker_id=worker_id)
            return result
        self.queue.ack(item_id=item.id, worker_id=worker_id)
        completed = {
            **attributes,
            "status": result.status,
            "outputArtifactCount": len(result.output_artifacts),
            "evidenceCount": len(result.evidence_refs),
        }
        self.events.append(Event("ProviderInvocationCompleted", request.execution_id, completed))
        if self.telemetry is not None:
            self.telemetry.event("ProviderInvocationCompleted", dict(completed))
        return result
