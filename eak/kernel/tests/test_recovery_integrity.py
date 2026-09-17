import sqlite3

import pytest

from eak_kernel.artifact_store import InMemoryArtifactStore, LocalArtifactStore
from eak_kernel.crypto import AESGCMCipher, EncryptedArtifactStore
from eak_kernel.model import Event
from eak_kernel.persistence import SQLiteEventStore
from eak_kernel.recovery import SnapshotManifest, build_manifest, verify_manifest


def test_event_store_hash_chain_detects_mutation_and_backup_is_valid(tmp_path):
    source = tmp_path / "events.sqlite"
    store = SQLiteEventStore(source)
    store.append(Event("A", "execution://1", {"n": 1}))
    store.append(Event("B", "execution://1", {"n": 2}))
    assert store.verify_chain("execution://1")
    assert store.integrity_check()

    backup_path = store.backup_to(tmp_path / "backup" / "events.sqlite")
    backup = SQLiteEventStore(backup_path)
    assert backup.verify_chain("execution://1")
    assert [event.type for event in backup.stream("execution://1")] == ["A", "B"]

    with sqlite3.connect(source) as connection:
        connection.execute(
            "UPDATE eak_events SET payload_json='{}' WHERE execution_id=? AND sequence=1",
            ("execution://1",),
        )
    assert not store.verify_chain("execution://1")


def test_snapshot_manifest_detects_restore_corruption(tmp_path):
    first = tmp_path / "one.bin"
    second = tmp_path / "nested" / "two.bin"
    second.parent.mkdir()
    first.write_bytes(b"one")
    second.write_bytes(b"two")
    manifest = build_manifest(tmp_path, (first, second))
    encoded = manifest.to_json()
    assert SnapshotManifest.from_json(encoded) == manifest
    assert verify_manifest(tmp_path, manifest) == ()
    second.write_bytes(b"tampered")
    assert verify_manifest(tmp_path, manifest) == ("size:nested/two.bin",)


def test_generic_encrypted_artifact_wrapper_binds_ciphertext_to_tenant():
    pytest.importorskip("cryptography")
    key = AESGCMCipher.generate_key()
    backing = InMemoryArtifactStore()
    store = EncryptedArtifactStore(backing, AESGCMCipher(key))
    stored = store.put(tenant="tenant-a", data=b"secret", media_type="text/plain")
    assert store.get(tenant="tenant-a", ref=stored.ref) == b"secret"
    with pytest.raises(KeyError):
        store.get(tenant="tenant-b", ref=stored.ref)


def test_local_artifact_store_uses_tenant_scoped_atomic_files(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    stored = store.put(tenant="tenant-a", data=b"payload", media_type="application/octet-stream")
    digest = stored.digest.split(":", 1)[1]
    path = tmp_path / "artifacts" / "tenant-a" / digest
    assert path.read_bytes() == b"payload"
    assert not list(path.parent.glob(".eak-artifact-*"))
