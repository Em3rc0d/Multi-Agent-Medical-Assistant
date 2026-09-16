from langgraph.checkpoint.memory import MemorySaver

from eak_kernel.adapters.langgraph import (
    LangGraphExecutionIdentity,
    LangGraphRuntimeAdapter,
    ResumeSignal,
)


def _graph():
    return {
        "apiVersion": "eak/v0.2",
        "kind": "ExecutionGraph",
        "metadata": {"id": "test.approval.compiled", "version": "1.0.0"},
        "spec": {
            "graphType": "physical",
            "entrypoints": ["prepare"],
            "nodes": [
                {
                    "id": "prepare",
                    "kind": "capability",
                    "capability": {"id": "test.prepare", "version": "1.0.0"},
                    "provider": {"id": "provider.test.prepare", "version": "1.0.0"},
                },
                {"id": "review", "kind": "approval", "approvalProfile": "test-review/v1"},
                {
                    "id": "finish",
                    "kind": "capability",
                    "capability": {"id": "test.finish", "version": "1.0.0"},
                    "provider": {"id": "provider.test.finish", "version": "1.0.0"},
                },
            ],
            "edges": [
                {"from": "prepare", "to": "review", "on": "success"},
                {"from": "review", "to": "finish", "on": "success"},
            ],
            "termination": {"successStates": ["SUCCEEDED"], "failureStates": ["FAILED"]},
        },
    }


def _context(execution_id: str):
    return {"spec": {"executionId": execution_id}}


def test_execution_id_is_the_langgraph_thread_id():
    identity = LangGraphExecutionIdentity("execution://abc")
    assert identity.config() == {"configurable": {"thread_id": "execution://abc"}}


def test_interrupt_and_resume_continue_same_execution():
    calls = []

    def executor(node, state):
        calls.append(node["id"])
        return {node["id"]: True}

    execution_id = "execution://approval-integration"
    adapter = LangGraphRuntimeAdapter(checkpointer=MemorySaver(), node_executor=executor)
    app = adapter.prepare(_graph(), _context(execution_id))

    first = adapter.start(app, execution_id=execution_id, state={})
    assert "prepare" in calls
    assert "finish" not in calls
    assert "__interrupt__" in first

    resumed = adapter.resume(
        app,
        execution_id=execution_id,
        signal=ResumeSignal(
            approval_id="approval://1",
            decision="APPROVE",
            principal_ref="principal://reviewer",
            payload={"reason": "conformance"},
        ),
    )

    assert calls == ["prepare", "finish"]
    assert resumed["prepare"] is True
    assert resumed["finish"] is True
    assert resumed["lastApproval"]["decision"] == "APPROVE"
