import sqlite3

import pytest

from eak_kernel.approval import ApprovalDecision, ApprovalRequest
from eak_kernel.approval_store import SQLiteApprovalStore
from eak_kernel.evidence import EvidenceEdge, EvidenceGraph, EvidenceNode
from eak_kernel.evidence_store import SQLiteEvidenceStore
from eak_kernel.secure_artifacts import EncryptedLocalArtifactStore
from eak_kernel.security import AuthorizationRule, EnvironmentSecretResolver, Principal, RBACAuthorizer, SecretRef
from eak_kernel.work_queue import SQLiteWorkQueue


def test_rbac_is_fail_closed():
    auth = RBACAuthorizer((AuthorizationRule("artifact.read", "artifact://", ("analyst",)),))
    principal = Principal("u1", "tenant-a", ("analyst",))
    assert auth.authorize(principal=principal, action="artifact.read", resource="artifact://sha256/x")
    assert not auth.authorize(principal=principal, action="artifact.write", resource="artifact://sha256/x")


def test_secret_refs_are_explicit_and_values_stay_external():
    ref = SecretRef.parse("secret://API_KEY")
    assert str(ref) == "secret://API_KEY"
    assert EnvironmentSecretResolver({"API_KEY": "value"}).resolve(ref) == "value"
    with pytest.raises(ValueError):
        SecretRef.parse("secret://lowercase")


def test_encrypted_store_is_tenant_isolated_and_ciphertext_at_rest(tmp_path):
    store = EncryptedLocalArtifactStore(tmp_path, master_key=b"k" * 32)
    saved = store.put(
        tenant="tenant-a",
        data=b"secret medical bytes",
        media_type="application/octet-stream",
    )
    assert store.get(tenant="tenant-a", ref=saved.ref) == b"secret medical bytes"
    encrypted = next((tmp_path / "tenant-a").iterdir()).read_bytes()
    assert b"secret medical bytes" not in encrypted
    with pytest.raises(KeyError):
        store.get(tenant="tenant-b", ref=saved.ref)


def test_durable_approval_store_verifies_roles_and_is_immutable(tmp_path):
    store = SQLiteApprovalStore(tmp_path / "approval.sqlite")
    request = ApprovalRequest("a1", "exec1", "review", "clinical", ("clinician",), ("claim1",))
    store.create(request)
    decision = ApprovalDecision("a1", "exec1", "user1", ("clinician",), "APPROVE")
    store.decide(decision)
    assert store.get_decision("a1").decision == "APPROVE"
    with pytest.raises(sqlite3.IntegrityError):
        store.decide(decision)


def test_evidence_graph_round_trip(tmp_path):
    graph = EvidenceGraph()
    graph.add_node(EvidenceNode("source1", "source", {"uri": "doc://1"}))
    graph.add_node(EvidenceNode("claim1", "claim", {"statement": "x"}))
    graph.add_edge(EvidenceEdge("claim1", "source1", "supportedBy"))
    store = SQLiteEvidenceStore(tmp_path / "evidence.sqlite")
    store.save(execution_id="exec1", graph_id="g1", graph=graph)
    loaded = store.load(execution_id="exec1", graph_id="g1")
    assert loaded.nodes == graph.nodes
    assert loaded.edges == graph.edges


def test_work_queue_lease_retry_and_idempotency(tmp_path):
    queue = SQLiteWorkQueue(tmp_path / "queue.sqlite")
    first = queue.enqueue(
        queue="default",
        payload={"execution": "e1"},
        idempotency_key="e1:n1",
        available_at=0,
    )
    duplicate = queue.enqueue(
        queue="default",
        payload={"execution": "e1"},
        idempotency_key="e1:n1",
        available_at=0,
    )
    assert first == duplicate
    item = queue.claim(queue="default", worker="w1", lease_seconds=10, now=100)
    assert item and item.attempts == 1
    queue.fail(item_id=item.id, worker="w1", error="retry", retry_delay=0, now=100)
    item2 = queue.claim(queue="default", worker="w2", lease_seconds=10, now=200)
    assert item2 and item2.attempts == 2
    queue.ack(item_id=item2.id, worker="w2")
    assert queue.claim(queue="default", worker="w3", now=300) is None
