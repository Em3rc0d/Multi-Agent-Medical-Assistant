from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentEvidence:
    environment: str
    event_store: str
    work_queue: str
    artifact_store: str
    secret_provider: str
    telemetry: str
    artifact_encryption: bool
    dependency_scan_verified: bool = False
    backup_restore_verified: bool = False
    incident_runbook_verified: bool = False
    slo_alerting_verified: bool = False


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    failures: tuple[str, ...]


class ProductionReadinessGate:
    """Prevent local/reference adapters from being mislabeled as production.

    The gate intentionally checks deployment evidence rather than guessing
    vendor choices. A deployment can use any managed implementation as long as
    it does not identify itself as one of EAK's reference/local backends and it
    provides the required operational evidence.
    """

    _REFERENCE = {
        "event_store": {"memory", "in-memory", "sqlite", "reference-sqlite"},
        "work_queue": {"memory", "in-memory", "sqlite", "reference-sqlite"},
        "artifact_store": {"memory", "in-memory", "local", "filesystem"},
        "secret_provider": {"environment", "env", "dotenv", "memory", "in-memory"},
        "telemetry": {"memory", "in-memory", "none"},
    }

    def evaluate(self, evidence: DeploymentEvidence) -> ReadinessResult:
        environment = evidence.environment.strip().lower()
        if environment not in {"development", "test", "staging", "production"}:
            return ReadinessResult(False, ("unknown-environment",))
        if environment != "production":
            return ReadinessResult(True, ())

        failures: list[str] = []
        for field_name, reference_values in self._REFERENCE.items():
            value = str(getattr(evidence, field_name)).strip().lower()
            if not value:
                failures.append(f"missing:{field_name}")
            elif value in reference_values:
                failures.append(f"reference-backend:{field_name}")

        if not evidence.artifact_encryption:
            failures.append("artifact-encryption-required")
        if not evidence.dependency_scan_verified:
            failures.append("dependency-scan-unverified")
        if not evidence.backup_restore_verified:
            failures.append("backup-restore-unverified")
        if not evidence.incident_runbook_verified:
            failures.append("incident-runbook-unverified")
        if not evidence.slo_alerting_verified:
            failures.append("slo-alerting-unverified")

        return ReadinessResult(not failures, tuple(failures))
