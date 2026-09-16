# MK1 Status

Status: **ACTIVE**

| Gate | State |
|---|---|
| Frozen v0.2 contracts imported | PASS |
| Draft 2020-12 schema validator | PASS |
| Semantic graph validator | PASS |
| Capability registry | PASS |
| Provider registry | PASS |
| Certification registry | PASS |
| Deterministic capability/provider resolver | PASS |
| Fail-closed certification/readiness filtering | PASS |
| Policy adapter boundary | PASS |
| Physical graph compiler | PASS |
| ExecutionContext snapshot compiler | PASS |
| Event/state model | PASS |
| Provider invocation boundary | PASS |
| Runtime adapter boundary | PASS |
| Minimal in-memory lifecycle runtime | PASS |
| Medical/AEC/Legal same-compiler conformance | PASS |
| Domain switch scan in Kernel Core | PASS |

## Current acceptance result

The Medical, AEC, and Legal logical fixtures compile with the same generic compiler into their frozen physical graph goldens. Provider registries are independent fixtures; expected physical graphs are not used to synthesize provider candidates at runtime.

## MK1.1 LangGraph adapter

Adapter code and version target are defined locally against the current LangGraph 1.2.x public surface. Package-level execution against `langgraph>=1.2.11,<1.3` is **PENDING** because the current build environment has no LangGraph installation/network package access. This gate remains open; Quarry #001 stays blocked.
