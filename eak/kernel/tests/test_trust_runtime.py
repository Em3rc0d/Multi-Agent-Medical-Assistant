from pathlib import Path

import pytest

from eak_kernel.approval import ApprovalDecision, ApprovalRequest, ApprovalVerifier
from eak_kernel.artifact_store import InMemoryArtifactStore, LocalArtifactStore
from eak_kernel.evidence import EvidenceEdge, EvidenceGraph, EvidenceNode
from eak_kernel.schema import SchemaSet

ROOT = Path(__file__).parents[1]


def test_evidence_graph_is_contract_valid_and_projects_to_prov():
    graph = EvidenceGraph()
    graph.add_node(EvidenceNode("claim://c1", "claim"))
    graph.add_node(EvidenceNode("evidence://s1", "source", {"locator": "page:4"}))
    graph.add_node(EvidenceNode("activity://r1", "activity"))
    graph.add_node(EvidenceNode("agent://provider1", "agent"))
    graph.add_edge(EvidenceEdge("claim://c1", "evidence://s1", "supportedBy"))
    graph.add_edge(EvidenceEdge("evidence://s1", "activity://r1", "wasGeneratedBy"))
    graph.add_edge(EvidenceEdge("activity://r1", "agent://provider1", "wasAssociatedWith"))
    contract = graph.to_contract(graph_id="evidence.test")
    SchemaSet(ROOT / "schemas/v0.2").validate(contract)
    prov = graph.to_prov()
    assert "claim://c1" in prov["entity"]
    assert "activity://r1" in prov["activity"]
    assert "agent://provider1" in prov["agent"]


def test_approval_requires_authenticated_role_scope():
    request = ApprovalRequest(
        "approval-request://1", "execution://1", "review", "expert-review", ("reviewer",)
    )
    valid = ApprovalDecision(
        request.id, request.execution_id, "principal://r1", ("reviewer",), "APPROVE"
    )
    ApprovalVerifier.verify(request, valid)
    invalid = ApprovalDecision(
        request.id, request.execution_id, "principal://r2", ("viewer",), "APPROVE"
    )
    with pytest.raises(PermissionError):
        ApprovalVerifier.verify(request, invalid)


def test_artifact_store_is_tenant_scoped_and_content_addressed(tmp_path):
    memory = InMemoryArtifactStore()
    stored = memory.put(tenant="a", data=b"secret", media_type="application/octet-stream")
    assert memory.get(tenant="a", ref=stored.ref) == b"secret"
    with pytest.raises(KeyError):
        memory.get(tenant="b", ref=stored.ref)

    local = LocalArtifactStore(tmp_path)
    persisted = local.put(tenant="tenant-a", data=b"payload", media_type="text/plain")
    assert local.get(tenant="tenant-a", ref=persisted.ref) == b"payload"
    with pytest.raises(KeyError):
        local.get(tenant="tenant-b", ref=persisted.ref)
