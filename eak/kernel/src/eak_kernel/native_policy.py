from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .model import PolicyDecision, Ref


@dataclass(frozen=True)
class ProviderUseRule:
    id: str
    capability_prefix: str | None = None
    provider_prefix: str | None = None
    required_roles: tuple[str, ...] = ()
    deny_egress_for_classifications: tuple[str, ...] = ()
    effect: str = "allow"

    def matches(self, capability: Ref, provider: Ref) -> bool:
        if self.capability_prefix and not capability.id.startswith(self.capability_prefix):
            return False
        if self.provider_prefix and not provider.id.startswith(self.provider_prefix):
            return False
        return True


class NativePolicyAdapter:
    """Small fail-closed policy engine for local/development deployments.

    Enterprise deployments may substitute Cedar/OPA or another PDP behind the
    same PolicyAdapter boundary.
    """

    def __init__(self, rules: Iterable[ProviderUseRule], *, default_effect: str = "deny") -> None:
        self.rules = tuple(rules)
        self.default_effect = default_effect

    def decide_provider_use(
        self,
        *,
        principal: dict[str, Any] | None,
        capability: Ref,
        provider: Ref,
        context: dict[str, Any],
    ) -> PolicyDecision:
        roles = set((principal or {}).get("roles", []))
        classification = context.get("dataClassification")
        provider_egress = context.get("providerEgress")
        for rule in self.rules:
            if not rule.matches(capability, provider):
                continue
            if rule.required_roles and not roles.intersection(rule.required_roles):
                return PolicyDecision(
                    effect="deny", reasons=(f"missing-role:{rule.id}",), policy_version="native/v1"
                )
            if (
                classification in rule.deny_egress_for_classifications
                and provider_egress in {"required", "policy-controlled"}
            ):
                return PolicyDecision(
                    effect="deny", reasons=(f"egress-denied:{rule.id}",), policy_version="native/v1"
                )
            return PolicyDecision(effect=rule.effect, reasons=(f"rule:{rule.id}",), policy_version="native/v1")
        return PolicyDecision(
            effect=self.default_effect,
            reasons=("default-policy",),
            policy_version="native/v1",
        )
