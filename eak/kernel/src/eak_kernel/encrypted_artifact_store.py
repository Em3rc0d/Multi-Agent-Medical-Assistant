from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from .artifact_store import LocalArtifactStore, StoredArtifact
from .secrets import SecretResolver


class EncryptedLocalArtifactStore:
    """Tenant-isolated content-addressed artifact store encrypted with Fernet.

    The encryption key is injected at runtime or resolved through SecretResolver;
    it is never written to artifact metadata or disk by this class.
    """

    def __init__(self, root: str | Path, key: bytes | str) -> None:
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:  # pragma: no cover - exercised when optional extra is absent
            raise RuntimeError("Install eak-kernel[security] to use encrypted artifact storage") from exc
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        encoded_key = key.encode("ascii") if isinstance(key, str) else key
        self._fernet = Fernet(encoded_key)

    @classmethod
    def from_secret(
        cls,
        root: str | Path,
        *,
        secret_ref: str,
        resolver: SecretResolver,
    ) -> "EncryptedLocalArtifactStore":
        return cls(root, resolver.resolve(secret_ref))

    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact:
        digest = sha256(data).hexdigest()
        tenant_dir = (self.root / LocalArtifactStore._safe_tenant(tenant)).resolve()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        path = (tenant_dir / f"{digest}.fernet").resolve()
        if tenant_dir not in path.parents:
            raise ValueError("Artifact path escaped tenant boundary")
        if not path.exists():
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(self._fernet.encrypt(data))
            temporary.replace(path)
        return StoredArtifact(
            ref=f"artifact://sha256/{digest}", tenant=tenant,
            digest=f"sha256:{digest}", media_type=media_type, size=len(data),
        )

    def get(self, *, tenant: str, ref: str) -> bytes:
        digest = LocalArtifactStore._digest_from_ref(ref)
        tenant_dir = (self.root / LocalArtifactStore._safe_tenant(tenant)).resolve()
        path = (tenant_dir / f"{digest}.fernet").resolve()
        if tenant_dir not in path.parents or not path.is_file():
            raise KeyError("Artifact not found")
        try:
            data = self._fernet.decrypt(path.read_bytes())
        except Exception as exc:
            raise ValueError("Artifact decryption or integrity verification failed") from exc
        if sha256(data).hexdigest() != digest:
            raise ValueError("Artifact integrity check failed")
        return data
