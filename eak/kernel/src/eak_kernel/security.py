from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class Principal:
    id: str
    tenant: str
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthorizationRule:
    action: str
    resource_prefix: str
    roles: tuple[str, ...]


class Authorizer(Protocol):
    def authorize(self, *, principal: Principal, action: str, resource: str) -> bool: ...


class RBACAuthorizer:
    """Small fail-closed RBAC evaluator for kernel-level authorization boundaries."""

    def __init__(self, rules: tuple[AuthorizationRule, ...]) -> None:
        self.rules = rules

    def authorize(self, *, principal: Principal, action: str, resource: str) -> bool:
        if not principal.id or not principal.tenant:
            return False
        principal_roles = set(principal.roles)
        for rule in self.rules:
            if rule.action != action:
                continue
            if not resource.startswith(rule.resource_prefix):
                continue
            if principal_roles.intersection(rule.roles):
                return True
        return False

    def require(self, *, principal: Principal, action: str, resource: str) -> None:
        if not self.authorize(principal=principal, action=action, resource=resource):
            raise PermissionError(f"principal {principal.id!r} is not authorized for {action!r}")


@dataclass(frozen=True)
class SecretRef:
    name: str

    @classmethod
    def parse(cls, value: str) -> "SecretRef":
        prefix = "secret://"
        if not value.startswith(prefix):
            raise ValueError("secret references must use secret://")
        name = value[len(prefix):]
        if not name or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in name):
            raise ValueError("secret reference names must be uppercase environment-style identifiers")
        return cls(name)

    def __str__(self) -> str:
        return f"secret://{self.name}"


class SecretResolver(Protocol):
    def resolve(self, ref: SecretRef) -> str: ...


class EnvironmentSecretResolver:
    """Resolves explicit secret references without copying values into execution snapshots."""

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = os.environ if environ is None else environ

    def resolve(self, ref: SecretRef) -> str:
        try:
            value = self._environ[ref.name]
        except KeyError as exc:
            raise KeyError(f"secret {ref.name!r} is not available") from exc
        if not value:
            raise ValueError(f"secret {ref.name!r} is empty")
        return value
