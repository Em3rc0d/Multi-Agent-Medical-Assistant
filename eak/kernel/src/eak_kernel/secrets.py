from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class SecretRef:
    provider: str
    name: str

    @classmethod
    def parse(cls, value: str) -> "SecretRef":
        prefix = "secret://"
        if not value.startswith(prefix):
            raise ValueError("Secret references must use secret://<provider>/<name>")
        body = value[len(prefix):]
        provider, separator, name = body.partition("/")
        if not separator or not provider or not name:
            raise ValueError("Invalid secret reference")
        if any(ch.isspace() for ch in provider + name):
            raise ValueError("Secret references may not contain whitespace")
        return cls(provider=provider, name=name)

    def __str__(self) -> str:
        return f"secret://{self.provider}/{self.name}"


class SecretResolver(Protocol):
    def resolve(self, ref: SecretRef | str) -> str: ...


class EnvironmentSecretResolver:
    """Resolve secret://env/NAME without persisting the resolved value."""

    def resolve(self, ref: SecretRef | str) -> str:
        secret = SecretRef.parse(ref) if isinstance(ref, str) else ref
        if secret.provider != "env":
            raise ValueError(f"Unsupported secret provider: {secret.provider}")
        try:
            value = os.environ[secret.name]
        except KeyError as exc:
            raise KeyError(f"Secret is not available: {secret}") from exc
        if not value:
            raise ValueError(f"Secret resolved to an empty value: {secret}")
        return value


class MappingSecretResolver:
    """Deterministic resolver for tests and sealed local environments."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)

    def resolve(self, ref: SecretRef | str) -> str:
        secret = SecretRef.parse(ref) if isinstance(ref, str) else ref
        key = str(secret)
        try:
            value = self._values[key]
        except KeyError as exc:
            raise KeyError(f"Secret is not available: {secret}") from exc
        if not value:
            raise ValueError(f"Secret resolved to an empty value: {secret}")
        return value
