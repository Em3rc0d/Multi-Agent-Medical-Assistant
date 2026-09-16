from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


_ALLOWED_RELATIONS = {
    "supportedBy",
    "contradictedBy",
    "derivedFrom",
    "used",
    "wasGeneratedBy",
    "wasAssociatedWith",
}


@dataclass(frozen=True)
class EvidenceNode:
    id: str
    type: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceEdge:
    source: str
    target: str
    relation: str

    def __post_init__(self) -> None:
        if self.relation not in _ALLOWED_RELATIONS:
            raise ValueError(f"Unsupported evidence relation: {self.relation}")


class EvidenceGraph:
    """Execution-scoped provenance graph with a PROV-O compatible projection."""

    def __init__(self) -> None:
        self._nodes: dict[str, EvidenceNode] = {}
        self._edges: list[EvidenceEdge] = []

    def add_node(self, node: EvidenceNode) -> None:
        if node.id in self._nodes and self._nodes[node.id] != node:
            raise ValueError(f"Evidence node id collision: {node.id}")
        self._nodes[node.id] = node

    def add_edge(self, edge: EvidenceEdge) -> None:
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise ValueError("Evidence edges may only reference registered nodes")
        self._edges.append(edge)

    @property
    def nodes(self) -> tuple[EvidenceNode, ...]:
        return tuple(self._nodes.values())

    @property
    def edges(self) -> tuple[EvidenceEdge, ...]:
        return tuple(self._edges)

    def to_contract(self, *, graph_id: str, version: str = "1.0.0") -> dict[str, Any]:
        return {
            "apiVersion": "eak/v0.2",
            "kind": "EvidenceGraph",
            "metadata": {"id": graph_id, "version": version},
            "spec": {
                "nodes": [
                    {"id": node.id, "type": node.type, **node.attributes}
                    for node in self.nodes
                ],
                "edges": [
                    {"from": edge.source, "to": edge.target, "relation": edge.relation}
                    for edge in self.edges
                ],
            },
        }

    def to_prov(self) -> dict[str, Any]:
        """Return a compact PROV-inspired JSON mapping without external dependencies."""
        entity_types = {
            "claim", "source", "observation", "calculation", "model_inference",
            "artifact", "human_attestation", "external_result",
        }
        entities: dict[str, Any] = {}
        activities: dict[str, Any] = {}
        agents: dict[str, Any] = {}
        for node in self.nodes:
            target = activities if node.type == "activity" else agents if node.type == "agent" else entities
            target[node.id] = {"eak:type": node.type, **node.attributes}
        relations = [
            {"type": edge.relation, "from": edge.source, "to": edge.target}
            for edge in self.edges
        ]
        return {"entity": entities, "activity": activities, "agent": agents, "relations": relations}
