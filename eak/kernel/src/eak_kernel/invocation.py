from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .model import Ref


@dataclass(frozen=True)
class InvocationRequest:
    execution_id: str
    node_id: str
    capability: Ref
    provider: Ref
    inputs: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None


@dataclass(frozen=True)
class InvocationResult:
    status: str
    output_artifacts: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderInvoker(Protocol):
    def invoke(self, request: InvocationRequest) -> InvocationResult: ...


class InvokerRegistry:
    """Runtime-only dispatch table keyed by Provider ref.

    Provider selection remains a compiler concern. Invocation begins only after
    the physical graph has frozen the selected provider.
    """

    def __init__(self) -> None:
        self._invokers: dict[Ref, ProviderInvoker] = {}

    def register(self, provider: Ref, invoker: ProviderInvoker) -> None:
        if provider in self._invokers:
            raise ValueError(f"Invoker already registered for {provider}")
        self._invokers[provider] = invoker

    def get(self, provider: Ref) -> ProviderInvoker:
        return self._invokers[provider]
