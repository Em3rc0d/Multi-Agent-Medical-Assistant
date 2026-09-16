from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from typing import Any

from .errors import GraphValidationError


class SemanticGraphValidator:
    def validate(self, graph: dict[str, Any]) -> None:
        spec = graph["spec"]
        graph_type = spec["graphType"]
        nodes = spec["nodes"]
        node_map = {node["id"]: node for node in nodes}
        if len(node_map) != len(nodes):
            raise GraphValidationError("Node ids must be unique")

        for entrypoint in spec["entrypoints"]:
            if entrypoint not in node_map:
                raise GraphValidationError(f"Unknown entrypoint: {entrypoint}")

        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in spec["edges"]:
            source, target = edge["from"], edge["to"]
            if source not in node_map or target not in node_map:
                raise GraphValidationError(f"Edge references unknown node: {source!r}->{target!r}")
            adjacency[source].append(target)

        for node in nodes:
            compensation = node.get("compensationNode")
            if compensation and compensation not in node_map:
                raise GraphValidationError(
                    f"Node {node['id']} references unknown compensation node {compensation}"
                )
            if node["kind"] == "capability":
                if graph_type == "physical" and "provider" not in node:
                    raise GraphValidationError(f"Physical capability node {node['id']} has no provider")
                if graph_type == "logical" and "provider" in node:
                    raise GraphValidationError(f"Logical capability node {node['id']} must not bind a provider")

        reachable = set()
        queue = deque(spec["entrypoints"])
        while queue:
            current = queue.popleft()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(adjacency[current])
        unreachable = set(node_map) - reachable
        if unreachable:
            raise GraphValidationError(f"Unreachable nodes: {sorted(unreachable)}")

        bounded = {node["id"] for node in nodes if node.get("iteration", {}).get("maxIterations")}
        residual_nodes = set(node_map) - bounded
        residual_adj = {
            node: [target for target in adjacency[node] if target in residual_nodes]
            for node in residual_nodes
        }
        if self._has_cycle(residual_nodes, residual_adj):
            raise GraphValidationError("Graph contains an unbounded cycle")

    @staticmethod
    def _has_cycle(nodes: set[str], adjacency: dict[str, list[str]]) -> bool:
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in nodes}

        def visit(node: str) -> bool:
            color[node] = GRAY
            for target in adjacency.get(node, []):
                if color[target] == GRAY:
                    return True
                if color[target] == WHITE and visit(target):
                    return True
            color[node] = BLACK
            return False

        return any(color[node] == WHITE and visit(node) for node in nodes)

    @staticmethod
    def to_physical(logical: dict[str, Any]) -> dict[str, Any]:
        graph = deepcopy(logical)
        graph["spec"]["graphType"] = "physical"
        graph["metadata"]["id"] = f"{logical['metadata']['id']}.compiled"
        name = graph["metadata"].get("displayName")
        if isinstance(name, str):
            graph["metadata"]["displayName"] = name.replace("logical", "physical")
        return graph
