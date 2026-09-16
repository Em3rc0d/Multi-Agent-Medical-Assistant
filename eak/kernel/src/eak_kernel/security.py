from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Iterable, Mapping


@dataclass(frozen=True)
class Principal:
    id: str
    tenant: str
    roles: frozenset[str] = frozenset()
    attributes: Mapping[str, str] | None = None


@dataclass(frozen=True)
class RoleGrant:
    role: str
    actions: tuple[str, ...]

    def allows(self, action: str) -> bool:
        return any(fnmatch(action, pattern) for pattern in self.actions)


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str


class RBACAuthorizer:
    """Fail-closed RBAC with tenant isolation.

    Cross-tenant access is denied unless a configured role is explicitly listed
    in ``cross_tenant_roles`` and grants the requested action.
    """

    def __init__(
        self,
        grants: Iterable[RoleGrant],
        *,
        cross_tenant_roles: Iterable[str] = ("platform-admin",),
    ) -> None:
        self._grants = {grant.role: grant for grant in grants}
        self._cross_tenant_roles = frozenset(cross_tenant_roles)

    def authorize(
        self,
        *,
        principal: Principal | None,
        action: str,
        resource_tenant: str,
    ) -> AuthorizationDecision:
        if principal is None:
            return AuthorizationDecision(False, "anonymous-denied")
        if not action or not resource_tenant:
            return AuthorizationDecision(False, "invalid-request")

        cross_tenant = principal.tenant != resource_tenant
        if cross_tenant and not principal.roles.intersection(self._cross_tenant_roles):
            return AuthorizationDecision(False, "tenant-boundary")

        for role in sorted(principal.roles):
            grant = self._grants.get(role)
            if grant and grant.allows(action):
                return AuthorizationDecision(True, f"role:{role}")

        return AuthorizationDecision(False, "no-grant")
