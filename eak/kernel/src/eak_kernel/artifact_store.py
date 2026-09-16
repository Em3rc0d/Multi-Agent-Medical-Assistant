from __future__ import annotations

import os
import tempfile
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
    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact: ...
    def get(self, *, tenant: str, ref: str) -> bytes: ...


class InMemoryArtifactStore:
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
    """Content-addressed local backend with tenant isolation and atomic writes."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            self.root.chmod(0o700)
        except OSError:
            pass

    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact:
        digest = sha256(data).hexdigest()
        tenant_dir = (self.root / self._safe_tenant(tenant)).resolve()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        try:
            tenant_dir.chmod(0o700)
        except OSError:
            pass
        path = (tenant_dir / digest).resolve()
        if tenant_dir not in path.parents:
            raise ValueError("Artifact path escaped tenant boundary")
        if not path.exists():
            self._atomic_write(path, data)
        return StoredArtifact(
            ref=f"artifact://sha256/{digest}",
            tenant=tenant,
            digest=f"sha256:{digest}",
            media_type=media_type,
            size=len(data),
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
    def _atomic_write(path: Path, data: bytes) -> None:
        fd, tmp_name = tempfile.mkstemp(prefix=".eak-artifact-", dir=path.parent)
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                tmp.chmod(0o600)
            except OSError:
                pass
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                tmp.unlink()

    @staticmethod
    def _safe_tenant(tenant: str) -> str:
        if not tenant or any(
            char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for char in tenant
        ):
            raise ValueError("Invalid tenant identifier")
        return tenant

    @staticmethod
    def _digest_from_ref(ref: str) -> str:
        prefix = "artifact://sha256/"
        if not ref.startswith(prefix):
            raise ValueError("Unsupported artifact reference")
        digest = ref[len(prefix) :]
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("Invalid artifact digest")
        return digest
