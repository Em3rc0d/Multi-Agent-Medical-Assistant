from __future__ import annotations

import pytest

from eak_kernel.artifact_store import InMemoryArtifactStore, LocalArtifactStore
from eak_kernel.crypto import AESGCMCipher, EncryptedArtifactStore
from eak_kernel.persistence import SQLiteEventStore
from eak_kernel.model import Event
from eak_kernel.readiness import DeploymentEvidence, ProductionReadinessGate
from eak_kernel.recovery import SnapshotManifest, build_manifest, verify_manifest
from eak_kernel.secrets import CompositeSecretProvider, EnvironmentSecretProvider
from eak_kernel.security import Principal, RBACAuthorizer, RoleGrant
from eak_kernel.workqueue import SQLiteWorkQueue


def test_rbac_is_fail_closed_and_tenant_scoped():
    authorizer = RBACAuthorizer(
        (
            RoleGrant("viewer", ("artifact.read",)),
            RoleGrant("platform-admin", ("*",)),
        )
    )
    viewer = Principal("user-1", "tenant-a", frozenset({"viewer"}))
    assert authorizer.authorize(
        principal=viewer, action="artifact.read", resource_tenant="tenant-a"
    ).allowed
    assert not authorizer.authorize(
        principal=viewer, action="artifact.write", resource_tenant="tenant-a"
    ).allowed
    assert not authorizer.authorize(
        principal=viewer, action="artifact.read", resource_tenant="tenant-b"
    ).allowed
    admin = Principal("admin-1", "platform", frozenset({"platform-admin"}))
    assert authorizer.authorize(
        principal=admin, action="artifact.write", resource_tenant="tenant-b"
    ).allowed


def test_environment_secrets_are_explicit_and_redacted(monkeypatch):
    monkeypatch.setenv("EAK_SECRET_DATABASE_URL", "sqlite:///private")
    provider = CompositeSecretProvider((EnvironmentSecretProvider(),))
    secret = provider.get("DATABASE_URL")
    assert secret.reveal() == "sqlite:///private"
    assert "sqlite:///private" not in repr(secret)
    assert str(secret) == "<redacted>"
    with pytest.raises(ValueError):
        provider.get("../../PATH")


def test_work_queue_leases_retries_and_exhaustion(tmp_path):
    queue = SQLiteWorkQueue(tmp_path / "queue.sqlite")
    queue.enqueue(
        id="job-1",
        tenant="tenant-a",
        kind="workflow-node",
        payload={"execution": "exec-1"},
        max_attempts=2,
        available_at=10.0,
    )
    first = queue.claim(worker="worker-a", lease_seconds=5.0, now=10.0)
    assert first and first.status == "RUNNING" and first.attempts == 1
    with pytest.raises(PermissionError):
        queue.ack(id="job-1", worker="worker-b")
    retry = queue.nack(id="job-1", worker="worker-a", retry_delay=2.0, now=10.0)
    assert retry.status == "QUEUED" and retry.available_at == 12.0
    assert queue.claim(worker="worker-b", now=11.0) is None
    second = queue.claim(worker="worker-b", lease_seconds=5.0, now=12.0)
    assert second and second.attempts == 2
    failed = queue.nack(id="job-1", worker="worker-b", now=12.0)
    assert failed.status == "FAILED"
    assert queue.claim(worker="worker-c", now=100.0) is None


def test_expired_work_queue_lease_can_be_reclaimed(tmp_path):
    queue = SQLiteWorkQueue(tmp_path / "queue.sqlite")
    queue.enqueue(
        id="job-1", tenant="tenant-a", kind="task", payload={}, max_attempts=3, available_at=1.0
    )
    queue.claim(worker="worker-a", lease_seconds=5.0, now=1.0)
    assert queue.claim(worker="worker-b", now=5.9) is None
    reclaimed = queue.claim(worker="worker-b", lease_seconds=5.0, now=6.0)
    assert reclaimed and reclaimed.lease_owner == "worker-b" and reclaimed.attempts == 2


def test_encrypted_artifact_store_round_trip_and_tenant_binding():
    backing = InMemoryArtifactStore()
    cipher = AESGCMCipher(AESGCMCipher.generate_key())
    store = EncryptedArtifactStore(backing, cipher)
    stored = store.put(tenant="tenant-a", data=b"sensitive", media_type="text/plain")
    ciphertext = backing.get(tenant="tenant-a", ref=stored.ref)
    assert ciphertext != b"sensitive"
    assert store.get(tenant="tenant-a", ref=stored.ref) == b"sensitive"
    with pytest.raises(KeyError):
        store.get(tenant="tenant-b", ref=stored.ref)


def test_local_artifact_store_integrity_and_tenant_isolation(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    stored = store.put(tenant="tenant-a", data=b"payload", media_type="application/octet-stream")
    assert store.get(tenant="tenant-a", ref=stored.ref) == b"payload"
    with pytest.raises(KeyError):
        store.get(tenant="tenant-b", ref=stored.ref)


def test_event_store_backup_and_recovery_manifest(tmp_path):
    store = SQLiteEventStore(tmp_path / "events.sqlite")
    store.append(Event("Started", "exec-1", {"tenant": "tenant-a"}))
    backup = store.backup_to(tmp_path / "backup" / "events.sqlite")
    assert store.integrity_check()
    restored = SQLiteEventStore(backup)
    assert restored.integrity_check()
    assert [event.type for event in restored.stream("exec-1")] == ["Started"]

    manifest = build_manifest(tmp_path, (backup,))
    encoded = manifest.to_json()
    decoded = SnapshotManifest.from_json(encoded)
    assert verify_manifest(tmp_path, decoded) == ()
    backup.write_bytes(b"tampered")
    assert verify_manifest(tmp_path, decoded)


def test_production_readiness_rejects_reference_backends_and_missing_evidence():
    result = ProductionReadinessGate().evaluate(
        DeploymentEvidence(
            environment="production",
            event_store="sqlite",
            work_queue="sqlite",
            artifact_store="local",
            secret_provider="environment",
            telemetry="in-memory",
            artifact_encryption=False,
        )
    )
    assert not result.ready
    assert "reference-backend:event_store" in result.failures
    assert "artifact-encryption-required" in result.failures
    assert "backup-restore-unverified" in result.failures


def test_production_readiness_accepts_managed_adapters_with_verified_operations():
    result = ProductionReadinessGate().evaluate(
        DeploymentEvidence(
            environment="production",
            event_store="postgres-managed",
            work_queue="managed-broker",
            artifact_store="object-store-kms",
            secret_provider="vault-managed",
            telemetry="opentelemetry-exporter",
            artifact_encryption=True,
            dependency_scan_verified=True,
            backup_restore_verified=True,
            incident_runbook_verified=True,
            slo_alerting_verified=True,
        )
    )
    assert result.ready and result.failures == ()
