# Expert Agent Kernel (EAK) — MK1 Incubation

Status: **MK1 ACTIVE / contract-first**

This directory is the executable continuation of EAK MK0 Core Spec v0.2. It deliberately starts with conformance rather than domain features or an agent runtime.

## Current scope

Implemented in this incubation slice:

- frozen EAK v0.2 schemas and normative specs;
- Draft 2020-12 schema validation;
- semantic ExecutionGraph validation;
- versioned registries;
- deterministic Capability → Provider resolution;
- policy adapter boundary;
- certification-aware fail-closed resolution;
- physical graph compilation;
- ExecutionContext snapshot compilation;
- canonical execution state machine;
- minimal in-memory runtime for lifecycle semantics only;
- cross-domain conformance against Medical, AEC, and Legal paper fixtures.

Not implemented yet:

- LangGraph adapter;
- MCP/A2A invocation adapters;
- real persistence/event store;
- real artifact store;
- production policy engine;
- real providers;
- medical Quarry #001 port.

Those remain blocked until the generic conformance layer is green.

## Run

```bash
python -m pip install -e '.[test]'
pytest

eak-conformance --root .
```

The acceptance condition is that the same compiler produces the three expected physical ExecutionGraphs without any domain switch in kernel code.

## Core invariant

```text
A new Domain Pack MUST NOT require a Kernel Core change.
```
