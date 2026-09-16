from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..errors import EAKError


class LangGraphDependencyError(EAKError):
    pass


@dataclass(frozen=True)
class LangGraphExecutionIdentity:
    execution_id: str

    @property
    def thread_id(self) -> str:
        return self.execution_id

    def config(self) -> dict[str, Any]:
        return {"configurable": {"thread_id": self.thread_id}}


@dataclass(frozen=True)
class ResumeSignal:
    approval_id: str
    decision: str
    principal_ref: str
    payload: dict[str, Any]

    def value(self) -> dict[str, Any]:
        return {"approvalId": self.approval_id, "decision": self.decision, "principalRef": self.principal_ref, "payload": self.payload}


class LangGraphRuntimeAdapter:
    adapter_id = "langgraph/python-1.2"

    def __init__(self, *, checkpointer: Any, node_executor: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]):
        self.checkpointer = checkpointer
        self.node_executor = node_executor

    @staticmethod
    def _runtime_types() -> tuple[Any, Any, Any, Any, Any]:
        try:
            from langgraph.constants import END, START
            from langgraph.graph import StateGraph
            from langgraph.types import Command, interrupt
        except ImportError as exc:
            raise LangGraphDependencyError("LangGraph adapter requires optional dependency langgraph>=1.2.11,<1.3") from exc
        return StateGraph, START, END, Command, interrupt

    def prepare(self, physical_graph: dict[str, Any], execution_context: dict[str, Any]) -> Any:
        StateGraph, START, END, _Command, interrupt = self._runtime_types()
        builder = StateGraph(dict)
        node_map = {node["id"]: node for node in physical_graph["spec"]["nodes"]}
        outgoing: dict[str, list[dict[str, Any]]] = {}
        for edge in physical_graph["spec"]["edges"]:
            outgoing.setdefault(edge["from"], []).append(edge)

        def make_node(node: dict[str, Any]):
            if node["kind"] == "approval":
                def approval_node(state: dict[str, Any]) -> dict[str, Any]:
                    resume_value = interrupt({
                        "executionId": execution_context["spec"]["executionId"],
                        "nodeId": node["id"],
                        "approvalProfile": node["approvalProfile"],
                    })
                    return {**state, "lastApproval": resume_value}
                return approval_node

            def execute_node(state: dict[str, Any]) -> dict[str, Any]:
                update = self.node_executor(node, state)
                return {**state, **(update or {})}
            return execute_node

        for node in physical_graph["spec"]["nodes"]:
            builder.add_node(node["id"], make_node(node))

        entrypoints = physical_graph["spec"]["entrypoints"]
        if len(entrypoints) != 1:
            raise EAKError("LangGraph adapter v0.1 requires exactly one entrypoint")
        builder.add_edge(START, entrypoints[0])

        for source, edges in outgoing.items():
            ordered = sorted(edges, key=lambda edge: edge.get("priority", 0))
            if len(ordered) == 1 and ordered[0]["on"] in {"success", "always"}:
                builder.add_edge(source, ordered[0]["to"])
                continue

            def make_router(source_edges: list[dict[str, Any]]):
                def route(state: dict[str, Any]) -> str:
                    conditions = state.get("conditions", {})
                    for edge in source_edges:
                        on = edge["on"]
                        if on in {"success", "always"}:
                            return edge["to"]
                        if on == "condition" and conditions.get(edge["conditionRef"]) is True:
                            return edge["to"]
                    raise EAKError("No conforming edge selected by runtime state")
                return route

            targets = sorted({edge["to"] for edge in ordered})
            builder.add_conditional_edges(source, make_router(ordered), {target: target for target in targets})

        for node_id in node_map:
            if node_id not in outgoing:
                builder.add_edge(node_id, END)

        return builder.compile(checkpointer=self.checkpointer)

    def start(self, prepared: Any, *, execution_id: str, state: dict[str, Any], durability: str = "sync") -> Any:
        identity = LangGraphExecutionIdentity(execution_id)
        return prepared.invoke(state, config=identity.config(), durability=durability)

    def resume(self, prepared: Any, *, execution_id: str, signal: ResumeSignal, durability: str = "sync") -> Any:
        _StateGraph, _START, _END, Command, _interrupt = self._runtime_types()
        identity = LangGraphExecutionIdentity(execution_id)
        return prepared.invoke(Command(resume=signal.value()), config=identity.config(), durability=durability)

    def cancel(self, execution_id: str, reason: str | None = None) -> None:
        raise NotImplementedError("Durable cancellation backend is not bound yet")
