from __future__ import annotations

import os
from typing import Protocol

from .artifact_store import ArtifactStore, StoredArtifact


class Cipher(Protocol):
    def encrypt(self, plaintext: bytes, *, aad: bytes = b"") -> bytes: ...
    def decrypt(self, ciphertext: bytes, *, aad: bytes = b"") -> bytes: ...


class AESGCMCipher:
    """Authenticated encryption backed by the optional ``cryptography`` extra."""

    PREFIX = b"EAK-AESGCM-1\x00"

    def __init__(self, key: bytes) -> None:
        if len(key) not in {16, 24, 32}:
            raise ValueError("AES-GCM key must be 128, 192, or 256 bits")
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError as exc:
            raise RuntimeError(
                "AESGCMCipher requires the eak-kernel 'security' extra"
            ) from exc
        self._cipher = AESGCM(key)

    @staticmethod
    def generate_key(bits: int = 256) -> bytes:
        if bits not in {128, 192, 256}:
            raise ValueError("bits must be one of 128, 192, 256")
        return os.urandom(bits // 8)

    def encrypt(self, plaintext: bytes, *, aad: bytes = b"") -> bytes:
        nonce = os.urandom(12)
        return self.PREFIX + nonce + self._cipher.encrypt(nonce, plaintext, aad)

    def decrypt(self, ciphertext: bytes, *, aad: bytes = b"") -> bytes:
        if not ciphertext.startswith(self.PREFIX):
            raise ValueError("Unsupported encrypted artifact envelope")
        offset = len(self.PREFIX)
        nonce = ciphertext[offset : offset + 12]
        payload = ciphertext[offset + 12 :]
        if len(nonce) != 12 or not payload:
            raise ValueError("Malformed encrypted artifact envelope")
        return self._cipher.decrypt(nonce, payload, aad)


class EncryptedArtifactStore:
    """Encrypt bytes before they cross the backing ArtifactStore boundary."""

    def __init__(self, backing: ArtifactStore, cipher: Cipher) -> None:
        self.backing = backing
        self.cipher = cipher

    def put(self, *, tenant: str, data: bytes, media_type: str) -> StoredArtifact:
        ciphertext = self.cipher.encrypt(data, aad=self._aad(tenant))
        stored = self.backing.put(
            tenant=tenant,
            data=ciphertext,
            media_type="application/vnd.eak.encrypted",
        )
        return StoredArtifact(
            ref=stored.ref,
            tenant=stored.tenant,
            digest=stored.digest,
            media_type=media_type,
            size=len(data),
        )

    def get(self, *, tenant: str, ref: str) -> bytes:
        ciphertext = self.backing.get(tenant=tenant, ref=ref)
        return self.cipher.decrypt(ciphertext, aad=self._aad(tenant))

    @staticmethod
    def _aad(tenant: str) -> bytes:
        if not tenant:
            raise ValueError("tenant is required")
        return f"eak-artifact:{tenant}".encode("utf-8")
