from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver

from eak_kernel.adapters.langgraph import LangGraphRuntimeAdapter, ResumeSignal


def main() -> None:
    execution_id = "execution://ci-langgraph-smoke"
    context = {"spec": {"executionId": execution_id}}
    physical_graph = {
        "spec": {
            "entrypoints": ["approval"],
            "nodes": [
                {
                    "id": "approval",
                    "kind": "approval",
                    "approvalProfile": "ci-review",
                }
            ],
            "edges": [],
        }
    }

    saver = InMemorySaver()
    adapter = LangGraphRuntimeAdapter(
        checkpointer=saver,
        node_executor=lambda node, state: {},
    )
    prepared = adapter.prepare(physical_graph, context)

    paused = adapter.start(
        prepared,
        execution_id=execution_id,
        state={"phase": "start"},
    )
    assert "__interrupt__" in paused, paused

    resumed = adapter.resume(
        prepared,
        execution_id=execution_id,
        signal=ResumeSignal(
            approval_id="approval://ci",
            decision="approve",
            principal_ref="principal://ci-reviewer",
            payload={"source": "github-actions"},
        ),
    )
    assert resumed["lastApproval"]["approvalId"] == "approval://ci", resumed
    assert resumed["lastApproval"]["decision"] == "approve", resumed

    checkpoint = saver.get_tuple({"configurable": {"thread_id": execution_id}})
    assert checkpoint is not None
    assert checkpoint.config["configurable"]["thread_id"] == execution_id

    print("EAK LangGraph lifecycle integration: PASS")


if __name__ == "__main__":
    main()
