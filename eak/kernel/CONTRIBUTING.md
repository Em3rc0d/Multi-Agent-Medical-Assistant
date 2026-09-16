# Contributing to EAK Incubation

EAK follows a contract-first workflow.

1. Change the specification before changing runtime semantics.
2. Add or update JSON Schema and fixtures.
3. Add semantic/conformance tests.
4. Keep kernel core domain-agnostic: no `if domain == ...` branches in `src/eak_kernel`.
5. Add runtime-specific behavior only behind adapters.
6. Add domain-specific behavior only through Domain Packs, providers, policies, knowledge, and evaluation profiles.
7. Do not port Quarry #001 code into the kernel merely to make a test pass.

A change is mergeable only when core conformance and every enabled runtime integration workflow are green.
