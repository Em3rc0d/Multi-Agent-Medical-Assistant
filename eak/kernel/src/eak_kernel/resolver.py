from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ResolutionError
from .model import CandidateSelection, Ref
from .policy import PolicyAdapter
from .registry import CertificationRegistry, ProviderRegistry


@dataclass(frozen=True)
class ResolutionContext:
    domain: Ref
    principal: dict[str, Any] | None = None
    runtime: dict[str, Any] | None = None
    artifacts: tuple[dict[str, Any], ...] = ()


class CapabilityResolver:
    SELECTION_PROFILE = "eak.default-provider-selection/v0.2"

    def __init__(
        self,
        providers: ProviderRegistry,
        policy: PolicyAdapter,
        certifications: CertificationRegistry,
    ) -> None:
        self.providers = providers
        self.policy = policy
        self.certifications = certifications

    def resolve(
        self,
        capability: Ref,
        *,
        domain_pack: dict[str, Any],
        context: ResolutionContext,
    ) -> CandidateSelection:
        candidates = self.providers.implementing(capability)
        if not candidates:
            raise ResolutionError(f"No provider implements {capability.id}@{capability.version}")

        required_profile = self._required_profile(domain_pack, capability)
        rejected: dict[Ref, tuple[str, ...]] = {}
        survivors: list[tuple[tuple[Any, ...], Ref]] = []

        for ref, provider, metadata in candidates:
            reasons: list[str] = []
            decision = self.policy.decide_provider_use(
                principal=context.principal,
                capability=capability,
                provider=ref,
                context={"domain": context.domain.as_dict(), "runtime": context.runtime or {}},
            )
            if decision.effect != "allow":
                reasons.append("policy-denied")

            if required_profile:
                advertised = provider["spec"]["trust"]["certificationProfiles"]
                if required_profile not in advertised:
                    reasons.append(f"profile-not-advertised:{required_profile}")
                if not self.certifications.certified(ref, required_profile, context.domain):
                    reasons.append(f"not-certified:{required_profile}")

            readiness = provider["spec"].get("health", {}).get("readiness")
            if readiness == "required" and not metadata.ready:
                reasons.append("provider-not-ready")

            egress = provider["spec"]["dataHandling"]["egress"]
            if egress == "required" and any(
                artifact.get("egressAllowed") is False for artifact in context.artifacts
            ):
                reasons.append("artifact-egress-denied")

            if reasons:
                rejected[ref] = tuple(reasons)
                continue

            policy_preference = int(decision.constraints.get("policyPreference", metadata.policy_preference))
            rank = (
                -policy_preference,
                -metadata.certification_specificity,
                -metadata.quality_tier,
                -metadata.locality_preference,
                metadata.cost_class,
                ref.id,
                ref.version,
            )
            survivors.append((rank, ref))

        if not survivors:
            detail = ", ".join(
                f"{ref.id}@{ref.version}={list(reasons)}" for ref, reasons in sorted(rejected.items())
            )
            raise ResolutionError(f"No eligible provider for {capability.id}@{capability.version}: {detail}")

        survivors.sort(key=lambda item: item[0])
        selected = survivors[0][1]
        return CandidateSelection(
            provider=selected,
            rejected=rejected,
            selection_profile=self.SELECTION_PROFILE,
        )

    @staticmethod
    def _required_profile(domain_pack: dict[str, Any], capability: Ref) -> str | None:
        for requirement in domain_pack["spec"].get("providerRequirements", []):
            if Ref.from_dict(requirement["capability"]) == capability:
                return requirement["certificationProfile"]
        return None
