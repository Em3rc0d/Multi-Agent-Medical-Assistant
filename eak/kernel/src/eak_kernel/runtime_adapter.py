from __future__ import annotations

from typing import Any, Protocol


class RuntimeAdapter(Protocol):
    """Adapter boundary between EAK physical graphs and an execution engine.

    Implementations may use a graph runtime, queue/workflow engine, or a custom
    executor. They MUST consume and emit EAK contracts rather than leaking
    runtime-specific state objects into Kernel Core.
    """

    adapter_id: str

    def prepare(self, physical_graph: dict[str, Any], execution_context: dict[str, Any]) -> Any: ...
    def start(self, prepared: Any) -> str: ...
    def resume(self, execution_id: str, signal: dict[str, Any]) -> None: ...
    def cancel(self, execution_id: str, reason: str | None = None) -> None: ...
