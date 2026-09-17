from datetime import datetime, timezone

from eak_kernel.readiness import ProductionReadinessChecker


NOW = datetime(2026, 9, 17, tzinfo=timezone.utc)


def test_reference_local_stack_cannot_claim_production_readiness():
    report = ProductionReadinessChecker.check({
        "environment": "production",
        "adapters": {
            "identity": "local",
            "secretManager": "env",
            "artifactStore": "encrypted-local",
            "database": "sqlite",
            "queue": "sqlite",
        },
    }, now=NOW)
    assert not report.ready
    assert "managed-adapter-required:queue" in report.blockers
    assert "restore-drill-required" in report.blockers


def test_managed_profile_with_operational_evidence_can_pass():
    report = ProductionReadinessChecker.check({
        "environment": "production",
        "adapters": {
            "identity": "oidc",
            "secretManager": "managed-secrets",
            "artifactStore": "object-storage-kms",
            "database": "managed-postgres",
            "queue": "managed-queue",
        },
        "slo": {"availabilityTarget": 0.995, "p95LatencyMs": 2500},
        "operations": {
            "incidentOwner": "platform-oncall",
            "onCallChannel": "pager",
            "backupPolicy": "daily-plus-pitr",
            "lastRestoreDrillAt": "2026-09-01T12:00:00Z",
            "maxRestoreDrillAgeDays": 90,
        },
        "security": {
            "sbomRequired": True,
            "dependencyAuditRequired": True,
            "tenantIsolationTested": True,
        },
        "providerCertificationProfile": "production-v1",
        "contentTelemetryEnabled": False,
    }, now=NOW)
    assert report.ready
    assert report.blockers == ()
