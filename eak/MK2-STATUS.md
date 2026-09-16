# MK2 Status

Status: **ACTIVE**

MK2 starts from the merged EAK v0.2 baseline. The objective is to extract reusable Quarry #001 behavior without importing medical semantics into Kernel Core, while simultaneously closing cross-cutting production boundaries discovered during extraction.

## Current gates

| Gate | State |
|---|---|
| MK1 baseline merged to `main` | PASS |
| Generic provider package boundary | PASS |
| Medical Domain Pack package boundary | PASS |
| Medical image provider adapters | PASS |
| Generic artifact-store boundary | PASS |
| Tenant-scoped local artifact backend | PASS |
| Durable execution event store | PASS |
| Fail-closed tenant RBAC boundary | IMPLEMENTED / CI PENDING |
| Explicit secret-provider boundary | IMPLEMENTED / CI PENDING |
| Durable leased work queue | IMPLEMENTED / CI PENDING |
| Authenticated artifact encryption wrapper | IMPLEMENTED / CI PENDING |
| Recovery integrity manifests | IMPLEMENTED / CI PENDING |
| Generic document parsing extraction | OPEN |
| Generic retrieval/reranking extraction | OPEN |
| Legacy named-agent routing retirement | OPEN |

## Guardrail

MK2 does not permit medical prompts, clinical policy, medical model semantics, or medical interpretation rules to enter `eak/kernel`. Reusable mechanics become providers or kernel boundaries; domain meaning stays in `eak/domains/medical`.

## Exit condition

MK2 closes only when the reusable Quarry components have a single owned implementation in the EAK packages and the legacy path is either removed or explicitly isolated as a compatibility surface.
