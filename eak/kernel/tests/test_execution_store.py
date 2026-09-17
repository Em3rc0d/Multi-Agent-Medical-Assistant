import sqlite3

import pytest

from eak_kernel.execution_store import SQLiteExecutionStore


def context(execution_id="execution://1", provider="provider.a"):
    return {
        "spec": {
            "executionId": execution_id,
            "tenantId": "tenant-a",
            "resolvedProviders": {"capability.a": {"id": provider, "version": "1.0.0"}},
        }
    }


def test_execution_context_snapshots_are_immutable_and_digest_addressed(tmp_path):
    store = SQLiteExecutionStore(tmp_path / "contexts.sqlite")
    original = context()
    digest = store.save(original)
    assert digest.startswith("sha256:")
    assert store.save(original) == digest
    assert store.load("execution://1") == original
    with pytest.raises(ValueError):
        store.save(context(provider="provider.b"))


def test_execution_context_integrity_tampering_is_detected(tmp_path):
    path = tmp_path / "contexts.sqlite"
    store = SQLiteExecutionStore(path)
    store.save(context())
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE eak_execution_contexts SET context_json=? WHERE execution_id=?",
            ('{"spec":{"executionId":"execution://1","tenantId":"attacker"}}', "execution://1"),
        )
    with pytest.raises(ValueError):
        store.load("execution://1")


def test_execution_context_backup_round_trip(tmp_path):
    store = SQLiteExecutionStore(tmp_path / "contexts.sqlite")
    original = context()
    store.save(original)
    backup_path = store.backup_to(tmp_path / "backup" / "contexts.sqlite")
    restored = SQLiteExecutionStore(backup_path)
    assert restored.load("execution://1") == original
