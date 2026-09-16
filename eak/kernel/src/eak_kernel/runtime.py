from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .model import ExecutionState
from .state import ExecutionStateMachine


NodeHandler = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


@dataclass
class RuntimeResult:
    execution_id: str
    state: ExecutionState
    values: dict[str, Any]
    paused_node: str | None = None


@dataclass
class InMemoryRuntime:
    """Minimal deterministic runtime for kernel semantics tests only.

    It is intentionally not an agent runtime and performs no external I/O.
    """

    handlers: dict[str, NodeHandler] = field(default_factory=dict)
    approvals: set[str] = field(default_factory=set)

    def run(
        self,
        graph: dict[str, Any],
        *,
        execution_id: str,
        values: dict[str, Any] | None = None,
        resume_from: str | None = None,
    ) -> RuntimeResult:
        machine = ExecutionStateMachine(execution_id)
        machine.transition(ExecutionState.COMPILING)
        machine.transition(ExecutionState.READY)
        machine.transition(ExecutionState.RUNNING)
        values = dict(values or {})
        nodes = {node["id"]: node for node in graph["spec"]["nodes"]}
        outgoing: dict[str, list[dict[str, Any]]] = {}
        for edge in graph["spec"]["edges"]:
            outgoing.setdefault(edge["from"], []).append(edge)

        current = resume_from or graph["spec"]["entrypoints"][0]
        visited_steps = 0
        while current:
            visited_steps += 1
            if visited_steps > 10_000:
                machine.transition(ExecutionState.FAILED, payload={"reason": "runtime-step-bound"})
                return RuntimeResult(execution_id, machine.state, values)
            node = nodes[current]
            kind = node["kind"]
            if kind == "approval" and current not in self.approvals:
                machine.transition(ExecutionState.WAITING_APPROVAL, payload={"node": current})
                return RuntimeResult(execution_id, machine.state, values, paused_node=current)
            if kind == "capability":
                handler = self.handlers.get(node["provider"]["id"])
                if handler:
                    values.update(handler(node, values))
            edges = sorted(outgoing.get(current, []), key=lambda edge: edge.get("priority", 0))
            if not edges:
                break
            chosen = None
            for edge in edges:
                if edge["on"] in {"success", "always"}:
                    chosen = edge
                    break
                if edge["on"] == "condition" and values.get(edge["conditionRef"]) is True:
                    chosen = edge
                    break
            if chosen is None:
                break
            current = chosen["to"]

        machine.transition(ExecutionState.SUCCEEDED)
        return RuntimeResult(execution_id, machine.state, values)
