import sqlite3

import pytest

from eak_kernel.approval import ApprovalDecision, ApprovalRequest
from eak_kernel.approval_store import SQLiteApprovalStore
from eak_kernel.artifact_store import LocalArtifactStore
from eak_kernel.evidence import EvidenceEdge, EvidenceGraph, EvidenceNode
from eak_kernel.evidence_store import SQLiteEvidenceStore
from eak_kernel.model import Event
from eak_kernel.native_policy import NativePolicyAdapter
from eak_kernel.persistence import SQLiteEventStore
from eak_kernel.readiness import DeploymentProfile, assess_deployment_readiness
from eak_kernel.security import EnvironmentSecretResolver, MappingSecretResolver, SecretRef
from eak_kernel.telemetry import JsonLinesTelemetrySink


def test_event_store_survives_restart_and_detects_tampering(tmp_path):
    path = tmp_path / "events.sqlite"
    store = SQLiteEventStore(path)
    store.append(Event("Started", "execution://1", {"step": 1}))
    store.append(Event("Finished", "execution://1", {"step": 2}))
    assert store.verify_chain("execution://1")
    assert [event.type for event in SQLiteEventStore(path).stream("execution://1")] == ["Started", "Finished"]

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE eak_events SET payload_json=? WHERE execution_id=? AND sequence=(SELECT MIN(sequence) FROM eak_events WHERE execution_id=?)",
            ('{"step":999}', "execution://1", "execution://1"),
        )
    assert not SQLiteEventStore(path).verify_chain("execution://1")


def test_approval_store_binds_identity_and_is_immutable(tmp_path):
    store = SQLiteApprovalStore(tmp_path / "approvals.sqlite")
    request = ApprovalRequest(
        "approval://1", "execution://1", "review", "expert-review", ("reviewer",), ("claim://1",)
    )
    decision = ApprovalDecision(
        request.id, request.execution_id, "principal://alice", ("reviewer",), "APPROVE"
    )
    store.record(request, decision)
    loaded = store.load(request.id)
    assert loaded is not None
    assert loaded[1].principal_ref == "principal://alice"
    with pytest.raises(ValueError):
        store.record(request, decision)


def test_evidence_store_detects_contract_tampering(tmp_path):
    path = tmp_path / "evidence.sqlite"
    store = SQLiteEvidenceStore(path)
    graph = EvidenceGraph()
    graph.add_node(EvidenceNode("claim://1", "claim"))
    graph.add_node(EvidenceNode("source://1", "source"))
    graph.add_edge(EvidenceEdge("claim://1", "source://1", "supportedBy"))
    snapshot = store.save(execution_id="execution://1", graph=graph, graph_id="graph://1")
    assert snapshot.digest.startswith("sha256:")
    assert store.load(execution_id="execution://1", graph_id="graph://1") is not None

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE eak_evidence_graphs SET contract_json=? WHERE execution_id=?",
            ('{}', "execution://1"),
        )
    with pytest.raises(ValueError):
        store.load(execution_id="execution://1", graph_id="graph://1")


def test_secret_refs_are_opaque_and_environment_resolution_is_explicit(monkeypatch):
    monkeypatch.setenv("EAK_TEST_TOKEN", "value-from-env")
    resolver = EnvironmentSecretResolver()
    assert resolver.resolve(SecretRef("secret://env/EAK_TEST_TOKEN")) == "value-from-env"
    with pytest.raises(ValueError):
        resolver.resolve(SecretRef("secret://vault/token"))
    with pytest.raises(ValueError):
        SecretRef("literal-secret")
    mapping = MappingSecretResolver({"secret://test/token": "test-value"})
    assert mapping.resolve(SecretRef("secret://test/token")) == "test-value"


def test_deployment_readiness_distinguishes_engineering_from_production(tmp_path, monkeypatch):
    monkeypatch.setenv("EAK_TEST_TOKEN", "token")
    kwargs = {
        "event_store": SQLiteEventStore(tmp_path / "events.sqlite"),
        "artifact_store": LocalArtifactStore(tmp_path / "artifacts"),
        "policy_adapter": NativePolicyAdapter(()),
        "telemetry_sink": JsonLinesTelemetrySink(tmp_path / "telemetry.jsonl"),
        "approval_store": SQLiteApprovalStore(tmp_path / "approvals.sqlite"),
        "evidence_store": SQLiteEvidenceStore(tmp_path / "evidence.sqlite"),
        "secret_resolver": EnvironmentSecretResolver(),
    }
    engineering = assess_deployment_readiness(profile=DeploymentProfile.ENGINEERING, **kwargs)
    assert engineering.ready
    production = assess_deployment_readiness(profile=DeploymentProfile.PRODUCTION, **kwargs)
    assert not production.ready
    assert any("event_store" in blocker for blocker in production.blockers)


def test_telemetry_rejects_nested_sensitive_content(tmp_path):
    sink = JsonLinesTelemetrySink(tmp_path / "telemetry.jsonl")
    sink.event("ProviderResolved", {"provider": "x", "metrics": {"latencyMs": 2}})
    with pytest.raises(ValueError):
        sink.event("ModelCall", {"nested": {"prompt": "private"}})
