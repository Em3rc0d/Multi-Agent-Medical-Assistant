from __future__ import annotations

from dataclasses import dataclass, field

from .errors import StateTransitionError
from .model import Event, ExecutionState, TERMINAL_STATES


_ALLOWED = {
    ExecutionState.CREATED: {ExecutionState.COMPILING, ExecutionState.CANCELLED},
    ExecutionState.COMPILING: {ExecutionState.READY, ExecutionState.FAILED, ExecutionState.CANCELLED},
    ExecutionState.READY: {ExecutionState.RUNNING, ExecutionState.CANCELLED},
    ExecutionState.RUNNING: {
        ExecutionState.WAITING_APPROVAL,
        ExecutionState.WAITING_EXTERNAL,
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
    ExecutionState.WAITING_APPROVAL: {ExecutionState.RUNNING, ExecutionState.FAILED, ExecutionState.CANCELLED},
    ExecutionState.WAITING_EXTERNAL: {ExecutionState.RUNNING, ExecutionState.FAILED, ExecutionState.CANCELLED},
    ExecutionState.SUCCEEDED: set(),
    ExecutionState.FAILED: set(),
    ExecutionState.CANCELLED: set(),
}


@dataclass
class ExecutionStateMachine:
    execution_id: str
    state: ExecutionState = ExecutionState.CREATED
    events: list[Event] = field(default_factory=list)

    def transition(self, target: ExecutionState, *, payload: dict | None = None) -> Event:
        if self.state in TERMINAL_STATES:
            raise StateTransitionError(f"Terminal state {self.state} is immutable")
        if target not in _ALLOWED[self.state]:
            raise StateTransitionError(f"Invalid transition: {self.state} -> {target}")
        previous = self.state
        self.state = target
        event = Event(
            type=f"Execution{target.title().replace('_', '')}",
            execution_id=self.execution_id,
            payload={"from": previous, "to": target, **(payload or {})},
        )
        self.events.append(event)
        return event
