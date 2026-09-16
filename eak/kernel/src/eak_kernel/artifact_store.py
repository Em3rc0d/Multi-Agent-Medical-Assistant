from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class StoredArtifact:
    ref: str
    tenant: str
    digest: str
    media_type: str
    size: int


class ArtifactStore(Protocol):
    deployment_tier: str

    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact: ...
    def get(self, *, tenant: str, ref: str) -> bytes: ...


class InMemoryArtifactStore:
    deployment_tier = "test"

    def __init__(self) -> None:
        self._objects: dict[tuple[str, str], bytes] = {}

    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact:
        digest = sha256(data).hexdigest()
        ref = f"artifact://sha256/{digest}"
        self._objects[(tenant, ref)] = bytes(data)
        return StoredArtifact(ref, tenant, f"sha256:{digest}", media_type, len(data))

    def get(self, *, tenant: str, ref: str) -> bytes:
        try:
            return self._objects[(tenant, ref)]
        except KeyError as exc:
            raise KeyError("Artifact not found") from exc


class LocalArtifactStore:
    """Content-addressed local backend for engineering, never raw static serving."""

    deployment_tier = "local-durable"

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact:
        digest = sha256(data).hexdigest()
        tenant_dir = (self.root / self._safe_tenant(tenant)).resolve()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        path = (tenant_dir / digest).resolve()
        if tenant_dir not in path.parents:
            raise ValueError("Artifact path escaped tenant boundary")
        if not path.exists():
            path.write_bytes(data)
        return StoredArtifact(
            ref=f"artifact://sha256/{digest}", tenant=tenant,
            digest=f"sha256:{digest}", media_type=media_type, size=len(data),
        )

    def get(self, *, tenant: str, ref: str) -> bytes:
        digest = self._digest_from_ref(ref)
        tenant_dir = (self.root / self._safe_tenant(tenant)).resolve()
        path = (tenant_dir / digest).resolve()
        if tenant_dir not in path.parents or not path.is_file():
            raise KeyError("Artifact not found")
        data = path.read_bytes()
        if sha256(data).hexdigest() != digest:
            raise ValueError("Artifact integrity check failed")
        return data

    @staticmethod
    def _safe_tenant(tenant: str) -> str:
        if not tenant or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in tenant):
            raise ValueError("Invalid tenant identifier")
        return tenant

    @staticmethod
    def _digest_from_ref(ref: str) -> str:
        prefix = "artifact://sha256/"
        if not ref.startswith(prefix):
            raise ValueError("Unsupported artifact reference")
        digest = ref[len(prefix):]
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("Invalid artifact digest")
        return digest
