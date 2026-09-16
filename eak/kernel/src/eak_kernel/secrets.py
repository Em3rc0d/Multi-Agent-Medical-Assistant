from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable, Protocol

_SECRET_NAME = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")


@dataclass(frozen=True)
class SecretValue:
    name: str
    _value: str

    def __repr__(self) -> str:
        return f"SecretValue(name={self.name!r}, value=<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"

    def reveal(self) -> str:
        """Explicit secret access point. Callers should never log the result."""
        return self._value


class SecretProvider(Protocol):
    def get(self, name: str) -> SecretValue: ...


class EnvironmentSecretProvider:
    """Resolve explicitly named EAK secrets from environment variables."""

    def __init__(self, *, prefix: str = "EAK_SECRET_") -> None:
        self.prefix = prefix

    def get(self, name: str) -> SecretValue:
        _validate_name(name)
        key = f"{self.prefix}{name}"
        value = os.environ.get(key)
        if value is None or value == "":
            raise KeyError(f"Secret not found: {name}")
        return SecretValue(name=name, _value=value)


class CompositeSecretProvider:
    def __init__(self, providers: Iterable[SecretProvider]) -> None:
        self.providers = tuple(providers)

    def get(self, name: str) -> SecretValue:
        _validate_name(name)
        for provider in self.providers:
            try:
                return provider.get(name)
            except KeyError:
                continue
        raise KeyError(f"Secret not found: {name}")


def _validate_name(name: str) -> None:
    if not _SECRET_NAME.fullmatch(name):
        raise ValueError("Secret names must match [A-Z][A-Z0-9_]{1,127}")
