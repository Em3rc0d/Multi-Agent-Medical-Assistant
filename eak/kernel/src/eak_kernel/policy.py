from __future__ import annotations

from typing import Any, Protocol

from .model import PolicyDecision, Ref


class PolicyAdapter(Protocol):
    def decide_provider_use(
        self,
        *,
        principal: dict[str, Any] | None,
        capability: Ref,
        provider: Ref,
        context: dict[str, Any],
    ) -> PolicyDecision: ...


class StaticPolicyAdapter:
    """Deterministic policy adapter for conformance and local tests."""

    def __init__(self, denied: set[Ref] | None = None, preferences: dict[Ref, int] | None = None):
        self.denied = denied or set()
        self.preferences = preferences or {}

    def decide_provider_use(
        self,
        *,
        principal: dict[str, Any] | None,
        capability: Ref,
        provider: Ref,
        context: dict[str, Any],
    ) -> PolicyDecision:
        if provider in self.denied:
            return PolicyDecision(effect="deny", reasons=("provider-denied",))
        preference = self.preferences.get(provider)
        constraints = {} if preference is None else {"policyPreference": preference}
        return PolicyDecision(effect="allow", constraints=constraints, policy_version="static/v1")
