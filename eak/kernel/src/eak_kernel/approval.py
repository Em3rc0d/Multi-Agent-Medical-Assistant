from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from .identity import Principal


@dataclass(frozen=True)
class ApprovalRequest:
    id: str
    execution_id: str
    node_id: str
    profile: str
    required_roles: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    tenant: str | None = None


@dataclass(frozen=True)
class ApprovalDecision:
    request_id: str
    execution_id: str
    principal_ref: str
    authenticated_roles: tuple[str, ...]
    decision: str
    comment: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence: dict[str, Any] = field(default_factory=dict)


class ApprovalVerifier:
    """Validates approval scope and, when supplied, binds it to verified identity."""

    @staticmethod
    def verify(request: ApprovalRequest, decision: ApprovalDecision) -> None:
        """Validate request/decision shape and declared role evidence.

        This method is suitable for contract validation. Durable acceptance must
        additionally call ``verify_authenticated`` so roles are not self-asserted.
        """
        if request.id != decision.request_id:
            raise ValueError("Approval decision does not match request")
        if request.execution_id != decision.execution_id:
            raise ValueError("Approval decision targets a different execution")
        if decision.decision not in {"APPROVE", "REJECT"}:
            raise ValueError("Unsupported approval decision")
        if request.required_roles and not set(request.required_roles).intersection(decision.authenticated_roles):
            raise PermissionError("Reviewer lacks a required authenticated role")

    @staticmethod
    def verify_authenticated(
        request: ApprovalRequest,
        decision: ApprovalDecision,
        principal: Principal | Mapping[str, Any],
    ) -> Principal:
        resolved = principal if isinstance(principal, Principal) else Principal.from_dict(principal)
        if decision.principal_ref != resolved.id:
            raise PermissionError("Approval principal does not match authenticated identity")
        declared_roles = set(decision.authenticated_roles)
        actual_roles = set(resolved.roles)
        if not declared_roles.issubset(actual_roles):
            raise PermissionError("Approval contains roles not held by authenticated principal")
        if request.required_roles and not set(request.required_roles).intersection(actual_roles):
            raise PermissionError("Authenticated reviewer lacks a required role")
        if request.tenant is not None and request.tenant != resolved.tenant:
            raise PermissionError("Cross-tenant approval denied")
        ApprovalVerifier.verify(request, decision)
        return resolved
