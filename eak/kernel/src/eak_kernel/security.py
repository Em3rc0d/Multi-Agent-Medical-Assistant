from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Mapping, Protocol


_SECRET_REF = re.compile(r"^secret://([a-z][a-z0-9-]*)/([A-Za-z0-9_.-]+)$")
_ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True)
class SecretRef:
    """Opaque credential reference. Secret material never belongs in contracts."""

    uri: str

    def __post_init__(self) -> None:
        if _SECRET_REF.fullmatch(self.uri) is None:
            raise ValueError("Invalid secret reference")

    @property
    def backend(self) -> str:
        match = _SECRET_REF.fullmatch(self.uri)
        assert match is not None
        return match.group(1)

    @property
    def key(self) -> str:
        match = _SECRET_REF.fullmatch(self.uri)
        assert match is not None
        return match.group(2)


class SecretResolver(Protocol):
    deployment_tier: str

    def resolve(self, ref: SecretRef) -> str: ...


class MappingSecretResolver:
    """Test-only resolver; values remain outside ExecutionContext contracts."""

    deployment_tier = "test"

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)

    def resolve(self, ref: SecretRef) -> str:
        try:
            return self._values[ref.uri]
        except KeyError as exc:
            raise KeyError("Secret reference not found") from exc


class EnvironmentSecretResolver:
    """Resolve ``secret://env/NAME`` from process environment variables."""

    deployment_tier = "production"

    def resolve(self, ref: SecretRef) -> str:
        if ref.backend != "env" or _ENV_KEY.fullmatch(ref.key) is None:
            raise ValueError("Environment resolver only accepts secret://env/UPPER_CASE_NAME")
        try:
            value = os.environ[ref.key]
        except KeyError as exc:
            raise KeyError("Secret reference not found") from exc
        if not value:
            raise ValueError("Resolved secret is empty")
        return value
