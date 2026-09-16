# LangGraph Adapter Spec — MK1.1

Status: **IMPLEMENTED AS OPTIONAL ADAPTER LOCALLY / PACKAGE INTEGRATION TEST PENDING**
Target surface: `langgraph>=1.2.11,<1.3`

## Contract mapping

```text
EAK ExecutionContext.executionId -> LangGraph thread_id
EAK physical ExecutionGraph      -> StateGraph
EAK WAITING_APPROVAL             -> interrupt(...)
EAK ApprovalDecision             -> Command(resume=...)
EAK runtime durability policy    -> LangGraph durability mode
EAK NodeExecution                -> node executor + EAK event/trace layer
```

The adapter must always resume with the same EAK execution identity. Session and conversation identifiers are not valid substitutes for an execution identifier.

## Interrupt rule

LangGraph resumes an interrupted graph from the beginning of the interrupted node. Therefore approval nodes must call `interrupt()` before any non-idempotent effect. Provider side effects remain behind EAK idempotency and policy controls.

## Checkpoint rule

A checkpointer is mandatory for approval/pause-resume support. The checkpointer is injected into the adapter; Kernel Core does not select a storage backend.

## Durability

Adapter default is `sync` for the first implementation. Lower durability modes may be exposed later only through explicit deployment/policy configuration.

## State isolation

LangGraph state is adapter-local. EAK contract schemas never contain LangGraph `StateSnapshot`, checkpoint ids, `Command`, or interrupt objects.

## Open integration gate

The adapter source is implemented in the local MK1 package, but this environment does not contain the optional LangGraph dependency. MK1.1 becomes PASS only after executing package-level tests against the pinned 1.2.x surface.
