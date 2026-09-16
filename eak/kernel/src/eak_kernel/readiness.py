from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DeploymentProfile(StrEnum):
    ENGINEERING = "engineering"
    PRODUCTION = "production"


@dataclass(frozen=True)
class ReadinessCheck:
    component: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    profile: DeploymentProfile
    checks: tuple[ReadinessCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(check.detail for check in self.checks if not check.passed)

    def require_ready(self) -> None:
        if not self.ready:
            raise RuntimeError("Deployment profile is not ready: " + "; ".join(self.blockers))


def _tier(component: Any) -> str:
    return str(getattr(component, "deployment_tier", "unknown"))


def assess_deployment_readiness(
    *,
    profile: DeploymentProfile,
    event_store: Any,
    artifact_store: Any,
    policy_adapter: Any,
    telemetry_sink: Any,
    approval_store: Any,
    evidence_store: Any,
    secret_resolver: Any,
) -> ReadinessReport:
    """Fail closed when deployment infrastructure is weaker than its profile.

    ``engineering`` accepts local-durable reference adapters. ``production``
    accepts only adapters that explicitly self-identify as ``production``.
    This prevents SQLite/filesystem reference implementations from being
    accidentally treated as a production certification.
    """

    allowed = {"local-durable", "production"} if profile is DeploymentProfile.ENGINEERING else {"production"}
    checks: list[ReadinessCheck] = []
    for name, component in (
        ("event_store", event_store),
        ("artifact_store", artifact_store),
        ("policy_adapter", policy_adapter),
        ("telemetry_sink", telemetry_sink),
        ("approval_store", approval_store),
        ("evidence_store", evidence_store),
        ("secret_resolver", secret_resolver),
    ):
        tier = _tier(component)
        passed = tier in allowed
        checks.append(
            ReadinessCheck(
                component=name,
                passed=passed,
                detail=(
                    f"{name} tier={tier} accepted for {profile.value}"
                    if passed
                    else f"{name} tier={tier} is not accepted for {profile.value}"
                ),
            )
        )
    return ReadinessReport(profile=profile, checks=tuple(checks))
