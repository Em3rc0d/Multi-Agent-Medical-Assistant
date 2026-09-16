# EAK Security Policy

EAK is an engineering kernel for verifiable expert systems. It is not, by itself, a medical device, legal authority, structural-analysis product, or autonomous decision maker.

## Security invariants

- Fail closed on missing certification, provider readiness, policy decisions, schema compatibility, or deployment readiness.
- Treat user input, retrieved content, domain packs, providers, models, remote agents, human approvals and infrastructure adapters as separate trust boundaries.
- Never store provider credentials in `ExecutionContext`, traces, manifests or artifacts; contracts store only opaque `secret://` references.
- Artifact access is tenant-scoped and content-addressed. Raw artifact directories must never be exposed as static web roots.
- Content capture in traces is disabled by default, including nested prompt/message/document/content fields.
- Side-effecting providers must declare effects and idempotency semantics before execution.
- High-risk workflows may require authenticated human approval before execution continues. Approval authority is identity + authenticated role + policy, never free-form text.
- Runtime adapters must not leak runtime-native state into EAK contracts.
- Audit and evidence records must be integrity-verifiable.

## Deployment tiers

Reference adapters identify themselves as `test`, `local-durable`, or `production`. `DeploymentProfile.PRODUCTION` accepts only adapters that explicitly declare the production tier. SQLite/filesystem reference implementations are deliberately rejected by that gate even when functionally durable.

## Reporting

Do not open a public issue for suspected vulnerabilities containing secrets, personal data, or exploit details. Use the repository owner's private security-reporting channel when enabled. Until then, contact the maintainer privately through the GitHub account associated with this repository.
