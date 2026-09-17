import pytest

from eak_kernel.approval import ApprovalDecision, ApprovalRequest
from eak_kernel.approval_store import SQLiteApprovalStore
from eak_kernel.encrypted_artifact_store import EncryptedLocalArtifactStore
from eak_kernel.evidence import EvidenceEdge, EvidenceGraph, EvidenceNode
from eak_kernel.evidence_store import SQLiteEvidenceStore
from eak_kernel.identity import Principal, require_tenant_access
from eak_kernel.model import Ref
from eak_kernel.native_policy import NativePolicyAdapter, ProviderUseRule
from eak_kernel.queue import SQLiteWorkQueue
from eak_kernel.secrets import EnvironmentSecretResolver, MappingSecretResolver, SecretRef


def test_secret_references_keep_values_out_of_configuration(monkeypatch):
    ref = SecretRef.parse("secret://env/EAK_TEST_SECRET")
    assert str(ref) == "secret://env/EAK_TEST_SECRET"
    monkeypatch.setenv("EAK_TEST_SECRET", "runtime-value")
    assert EnvironmentSecretResolver().resolve(ref) == "runtime-value"
    mapping = MappingSecretResolver({"secret://env/ALT": "mapped-value"})
    assert mapping.resolve("secret://env/ALT") == "mapped-value"


def test_tenant_access_fails_closed():
    principal = Principal("principal://alice", "tenant-a", ("clinician",))
    assert require_tenant_access(principal, tenant="tenant-a", required_roles=("clinician",)) == principal
    with pytest.raises(PermissionError):
        require_tenant_access(principal, tenant="tenant-b")
    with pytest.raises(PermissionError):
        require_tenant_access(None, tenant="tenant-a")


def test_native_policy_can_enforce_tenant_boundary():
    adapter = NativePolicyAdapter((ProviderUseRule(
        id="tenant-boundary", capability_prefix="medical.", require_tenant_match=True,
    ),))
    decision = adapter.decide_provider_use(
        principal={"tenant": "tenant-a", "roles": ["clinician"]},
        capability=Ref("medical.imaging.classify", "1.0.0"),
        provider=Ref("provider.local", "1.0.0"),
        context={"resourceTenant": "tenant-b"},
    )
    assert decision.effect == "deny"
    assert decision.reasons == ("tenant-mismatch:tenant-boundary",)


def test_sqlite_work_queue_has_leases_retries_and_ack(tmp_path):
    queue = SQLiteWorkQueue(tmp_path / "work.sqlite")
    queued = queue.enqueue(execution_id="execution://1", node_id="node-a", payload={"x": 1}, max_attempts=2)
    leased = queue.lease(worker_id="worker-a", lease_seconds=30)
    assert leased is not None and leased.id == queued.id
    assert leased.state == "LEASED" and leased.attempts == 1
    queue.nack(item_id=leased.id, worker_id="worker-a")
    leased_again = queue.lease(worker_id="worker-b", lease_seconds=30)
    assert leased_again is not None and leased_again.attempts == 2
    queue.ack(item_id=leased_again.id, worker_id="worker-b")
    assert queue.get(queued.id).state == "DONE"


def test_sqlite_work_queue_marks_exhausted_item_dead(tmp_path):
    queue = SQLiteWorkQueue(tmp_path / "dead.sqlite")
    queued = queue.enqueue(execution_id="execution://1", node_id="node-a", payload={}, max_attempts=1)
    leased = queue.lease(worker_id="worker-a")
    assert leased is not None
    queue.nack(item_id=queued.id, worker_id="worker-a")
    assert queue.get(queued.id).state == "DEAD"
    assert queue.lease(worker_id="worker-b") is None


def test_durable_approval_decisions_are_authenticated_tenant_scoped_and_immutable(tmp_path):
    store = SQLiteApprovalStore(tmp_path / "approval.sqlite")
    request = ApprovalRequest(
        id="approval://1", execution_id="execution://1", node_id="review",
        profile="medical-review", required_roles=("clinician",), scope=("claim://1",),
        tenant="tenant-a",
    )
    store.put_request(request)
    principal = Principal("principal://doctor", "tenant-a", ("clinician",))
    decision = ApprovalDecision(
        request_id=request.id, execution_id=request.execution_id,
        principal_ref=principal.id, authenticated_roles=("clinician",), decision="APPROVE",
    )
    store.record_decision(decision, principal=principal)
    assert store.get_decision(request.id) == decision

    conflicting = ApprovalDecision(
        request_id=request.id, execution_id=request.execution_id,
        principal_ref=principal.id, authenticated_roles=("clinician",), decision="REJECT",
    )
    with pytest.raises(ValueError):
        store.record_decision(conflicting, principal=principal)


def test_durable_approval_rejects_cross_tenant_or_forged_roles(tmp_path):
    store = SQLiteApprovalStore(tmp_path / "approval.sqlite")
    request = ApprovalRequest(
        id="approval://2", execution_id="execution://2", node_id="review",
        profile="medical-review", required_roles=("clinician",), tenant="tenant-a",
    )
    store.put_request(request)
    decision = ApprovalDecision(
        request_id=request.id, execution_id=request.execution_id,
        principal_ref="principal://reviewer", authenticated_roles=("clinician",), decision="APPROVE",
    )
    with pytest.raises(PermissionError):
        store.record_decision(
            decision,
            principal=Principal("principal://reviewer", "tenant-b", ("clinician",)),
        )
    with pytest.raises(PermissionError):
        store.record_decision(
            decision,
            principal=Principal("principal://reviewer", "tenant-a", ("viewer",)),
        )


def test_evidence_graph_round_trips_through_sqlite(tmp_path):
    graph = EvidenceGraph()
    graph.add_node(EvidenceNode("artifact://1", "artifact", {"digest": "sha256:abc"}))
    graph.add_node(EvidenceNode("claim://1", "claim", {"statement": "bounded claim"}))
    graph.add_edge(EvidenceEdge("claim://1", "artifact://1", "supportedBy"))
    store = SQLiteEvidenceStore(tmp_path / "evidence.sqlite")
    store.save("execution://1", graph)
    loaded = store.load("execution://1")
    assert loaded.nodes == graph.nodes
    assert loaded.edges == graph.edges


def test_encrypted_artifact_store_is_tenant_isolated_and_not_plaintext(tmp_path):
    pytest.importorskip("cryptography")
    from cryptography.fernet import Fernet

    root = tmp_path / "artifacts"
    key = Fernet.generate_key()
    store = EncryptedLocalArtifactStore(root, key)
    data = b"sensitive-artifact"
    artifact = store.put(tenant="tenant-a", data=data, media_type="application/octet-stream")
    assert store.get(tenant="tenant-a", ref=artifact.ref) == data
    with pytest.raises(KeyError):
        store.get(tenant="tenant-b", ref=artifact.ref)
    digest = artifact.digest.split(":", 1)[1]
    assert (root / "tenant-a" / f"{digest}.fernet").read_bytes() != data
