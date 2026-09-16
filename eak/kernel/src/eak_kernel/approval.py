from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    id: str
    execution_id: str
    node_id: str
    profile: str
    required_roles: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()


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
    """Binds human authority to authenticated identity and role evidence."""

    @staticmethod
    def verify(request: ApprovalRequest, decision: ApprovalDecision) -> None:
        if request.id != decision.request_id:
            raise ValueError("Approval decision does not match request")
        if request.execution_id != decision.execution_id:
            raise ValueError("Approval decision targets a different execution")
        if decision.decision not in {"APPROVE", "REJECT"}:
            raise ValueError("Unsupported approval decision")
        if request.required_roles and not set(request.required_roles).intersection(decision.authenticated_roles):
            raise PermissionError("Reviewer lacks a required authenticated role")
