from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path

from .artifact_store import StoredArtifact

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("EncryptedLocalArtifactStore requires the 'security' extra") from exc


class EncryptedLocalArtifactStore:
    """Tenant-isolated, content-addressed AES-GCM artifact storage.

    The digest/ref is computed over plaintext for reproducibility. Bytes at rest are
    encrypted using a per-tenant key derived from a caller-supplied master key.
    """

    _VERSION = b"EAK1"

    def __init__(self, root: str | Path, *, master_key: bytes) -> None:
        if len(master_key) < 32:
            raise ValueError("master_key must contain at least 32 bytes of entropy")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._master_key = bytes(master_key)

    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact:
        tenant_id = self._safe_tenant(tenant)
        digest = sha256(data).hexdigest()
        tenant_dir = (self.root / tenant_id).resolve()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        path = (tenant_dir / f"{digest}.eak").resolve()
        if tenant_dir not in path.parents:
            raise ValueError("Artifact path escaped tenant boundary")
        if not path.exists():
            nonce = os.urandom(12)
            aad = f"{tenant_id}:{digest}:{media_type}".encode("utf-8")
            ciphertext = AESGCM(self._tenant_key(tenant_id)).encrypt(nonce, bytes(data), aad)
            path.write_bytes(self._VERSION + nonce + ciphertext)
        return StoredArtifact(
            ref=f"artifact://sha256/{digest}",
            tenant=tenant_id,
            digest=f"sha256:{digest}",
            media_type=media_type,
            size=len(data),
        )

    def get(self, *, tenant: str, ref: str, media_type: str = "application/octet-stream") -> bytes:
        tenant_id = self._safe_tenant(tenant)
        digest = self._digest_from_ref(ref)
        tenant_dir = (self.root / tenant_id).resolve()
        path = (tenant_dir / f"{digest}.eak").resolve()
        if tenant_dir not in path.parents or not path.is_file():
            raise KeyError("Artifact not found")
        blob = path.read_bytes()
        if len(blob) < len(self._VERSION) + 12 + 16 or not blob.startswith(self._VERSION):
            raise ValueError("Unsupported or corrupt encrypted artifact")
        nonce = blob[len(self._VERSION):len(self._VERSION) + 12]
        ciphertext = blob[len(self._VERSION) + 12:]
        aad = f"{tenant_id}:{digest}:{media_type}".encode("utf-8")
        data = AESGCM(self._tenant_key(tenant_id)).decrypt(nonce, ciphertext, aad)
        if sha256(data).hexdigest() != digest:
            raise ValueError("Artifact integrity check failed")
        return data

    def _tenant_key(self, tenant: str) -> bytes:
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=sha256(f"eak:{tenant}".encode()).digest(),
            info=b"eak-artifact-store-v1",
        ).derive(self._master_key)

    @staticmethod
    def _safe_tenant(tenant: str) -> str:
        if not tenant or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in tenant):
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
