"""Encryption service for at-rest data protection.

Implements AES-256-GCM for encrypting sensitive personal information (PII)
stored in the database, such as:
- Refresh tokens
- Guardian contact details
- Parent information
- Student addresses
- Emergency contacts

Uses a key derived from the ENCRYPTION_KEY setting via HKDF.
Each encryption operation uses a unique nonce (12 bytes).
"""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from backend.src.core.settings import settings
from backend.src.core.exceptions import EncryptionError


class EncryptionService:
    """Encryption service using AES-256-GCM.

    Provides encrypt/decrypt operations for sensitive data at rest.
    The encryption key is derived from the configured ENCRYPTION_KEY
    using HKDF with a fixed salt.
    """

    def __init__(self, encryption_key: Optional[str] = None) -> None:
        key_material = encryption_key or settings.ENCRYPTION_KEY
        if not key_material:
            # Development fallback - generates a deterministic key
            # WARNING: This is NOT secure for production!
            key_material = "teacher-os-dev-encryption-key-change-in-production"

        self._key = self._derive_key(key_material.encode())
        self._algorithm = settings.ENCRYPTION_ALGORITHM

    def _derive_key(self, key_material: bytes) -> bytes:
        """Derive a 256-bit AES key from key material using HKDF."""
        salt = b"teacher-os-encryption-salt-32bytes"  # Fixed salt for deterministic derivation
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"teacher-os-aes-256-gcm-key",
        )
        return hkdf.derive(key_material)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded ciphertext with prepended nonce.
            Format: base64(nonce + ciphertext + tag)

        Raises:
            EncryptionError: If encryption fails.
        """
        if not plaintext:
            return ""

        try:
            aesgcm = AESGCM(self._key)
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
            # Prepend nonce to ciphertext for storage
            result = base64.b64encode(nonce + ciphertext).decode("utf-8")
            return result
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string.

        Args:
            encrypted_data: Base64-encoded ciphertext with prepended nonce.

        Returns:
            The original plaintext string.

        Raises:
            EncryptionError: If decryption fails.
        """
        if not encrypted_data:
            return ""

        try:
            raw = base64.b64decode(encrypted_data)
            nonce = raw[:12]
            ciphertext = raw[12:]
            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}")

    def encrypt_field(self, value: Optional[str]) -> Optional[str]:
        """Encrypt a potentially None field value.

        Returns None if value is None or empty.
        """
        if not value:
            return value
        return self.encrypt(value)

    def decrypt_field(self, value: Optional[str]) -> Optional[str]:
        """Decrypt a potentially None encrypted field value.

        Returns None if value is None or empty.
        """
        if not value:
            return value
        return self.decrypt(value)

    def re_encrypt(self, encrypted_data: str, new_key: Optional[str] = None) -> str:
        """Re-encrypt data with a new key.

        Useful for key rotation scenarios.
        """
        plaintext = self.decrypt(encrypted_data)
        if new_key:
            old_key = self._key
            self._key = self._derive_key(new_key.encode())
            result = self.encrypt(plaintext)
            self._key = old_key
            return result
        return self.encrypt(plaintext)