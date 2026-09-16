import pytest

from eak_kernel.errors import StateTransitionError
from eak_kernel.model import ExecutionState
from eak_kernel.state import ExecutionStateMachine


def test_execution_state_machine_happy_path():
    machine = ExecutionStateMachine("execution://unit")
    machine.transition(ExecutionState.COMPILING)
    machine.transition(ExecutionState.READY)
    machine.transition(ExecutionState.RUNNING)
    machine.transition(ExecutionState.SUCCEEDED)
    assert machine.state is ExecutionState.SUCCEEDED
    assert [event.type for event in machine.events] == [
        "ExecutionCompiling",
        "ExecutionReady",
        "ExecutionRunning",
        "ExecutionSucceeded",
    ]


def test_terminal_execution_is_immutable():
    machine = ExecutionStateMachine("execution://unit")
    machine.transition(ExecutionState.CANCELLED)
    with pytest.raises(StateTransitionError):
        machine.transition(ExecutionState.RUNNING)


def test_invalid_transition_fails_closed():
    machine = ExecutionStateMachine("execution://unit")
    with pytest.raises(StateTransitionError):
        machine.transition(ExecutionState.SUCCEEDED)
