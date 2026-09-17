from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...] = ()


class ProductionReadinessChecker:
    """Fail-closed deployment-profile checker.

    This does not replace environment validation. It prevents reference/local
    adapters from being mislabeled as production-ready and requires explicit
    operational ownership/evidence before a production claim.
    """

    LOCAL_ONLY = {
        "identity": {"dictionary", "local", "none"},
        "secretManager": {"env", "mapping", "none"},
        "artifactStore": {"local", "encrypted-local", "memory"},
        "database": {"sqlite", "memory"},
        "queue": {"sqlite", "memory"},
    }

    @classmethod
    def check(cls, profile: Mapping[str, Any], *, now: datetime | None = None) -> ReadinessReport:
        blockers: list[str] = []
        warnings: list[str] = []
        environment = str(profile.get("environment", "")).lower()
        if environment != "production":
            blockers.append("environment-must-be-production")

        adapters = dict(profile.get("adapters", {}))
        for key, local_values in cls.LOCAL_ONLY.items():
            value = str(adapters.get(key, "none")).lower()
            if value in local_values:
                blockers.append(f"managed-adapter-required:{key}")

        slo = dict(profile.get("slo", {}))
        availability = slo.get("availabilityTarget")
        latency = slo.get("p95LatencyMs")
        if not isinstance(availability, (int, float)) or not 0 < float(availability) <= 1:
            blockers.append("valid-availability-slo-required")
        if not isinstance(latency, (int, float)) or float(latency) <= 0:
            blockers.append("valid-p95-latency-slo-required")

        operations = dict(profile.get("operations", {}))
        if not operations.get("incidentOwner"):
            blockers.append("incident-owner-required")
        if not operations.get("onCallChannel"):
            blockers.append("on-call-channel-required")
        if not operations.get("backupPolicy"):
            blockers.append("backup-policy-required")

        now = now or datetime.now(timezone.utc)
        restore_value = operations.get("lastRestoreDrillAt")
        if not restore_value:
            blockers.append("restore-drill-required")
        else:
            try:
                restored_at = datetime.fromisoformat(str(restore_value).replace("Z", "+00:00"))
                if restored_at.tzinfo is None:
                    restored_at = restored_at.replace(tzinfo=timezone.utc)
                age_days = (now - restored_at.astimezone(timezone.utc)).days
                if age_days > int(operations.get("maxRestoreDrillAgeDays", 90)):
                    blockers.append("restore-drill-stale")
            except (TypeError, ValueError):
                blockers.append("restore-drill-timestamp-invalid")

        security = dict(profile.get("security", {}))
        if security.get("sbomRequired") is not True:
            blockers.append("sbom-required")
        if security.get("dependencyAuditRequired") is not True:
            blockers.append("dependency-audit-required")
        if security.get("tenantIsolationTested") is not True:
            blockers.append("tenant-isolation-validation-required")

        if not profile.get("providerCertificationProfile"):
            blockers.append("provider-certification-profile-required")

        if profile.get("contentTelemetryEnabled") is True:
            warnings.append("content-telemetry-enabled-review-data-policy")

        return ReadinessReport(not blockers, tuple(sorted(set(blockers))), tuple(sorted(set(warnings))))


def load_profile(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
