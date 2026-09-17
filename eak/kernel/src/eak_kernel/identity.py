from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Principal:
    id: str
    tenant: str
    roles: tuple[str, ...]
    authentication_method: str | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Principal":
        principal_id = value.get("id") or value.get("principalId")
        tenant = value.get("tenant") or value.get("tenantId")
        if not principal_id or not tenant:
            raise ValueError("Principal id and tenant are required")
        roles = tuple(str(role) for role in value.get("roles", ()))
        return cls(
            id=str(principal_id),
            tenant=str(tenant),
            roles=roles,
            authentication_method=(
                str(value["authenticationMethod"])
                if value.get("authenticationMethod") is not None
                else None
            ),
        )


def require_tenant_access(
    principal: Principal | Mapping[str, Any] | None,
    *,
    tenant: str,
    required_roles: tuple[str, ...] = (),
) -> Principal:
    """Fail closed on missing identity, cross-tenant access, or missing roles."""

    if principal is None:
        raise PermissionError("Authenticated principal is required")
    resolved = principal if isinstance(principal, Principal) else Principal.from_dict(principal)
    if resolved.tenant != tenant:
        raise PermissionError("Cross-tenant access denied")
    if required_roles and not set(required_roles).intersection(resolved.roles):
        raise PermissionError("Principal lacks a required role")
    return resolved
