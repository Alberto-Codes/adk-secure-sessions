"""Fernet symmetric encryption backend.

Implements the ``EncryptionBackend`` protocol using
``cryptography.fernet.Fernet`` for authenticated symmetric encryption
(AES-128-CBC + HMAC-SHA256).

Keys can be provided as strings, bytes, or valid Fernet keys. Arbitrary
input is derived into a valid Fernet key via PBKDF2-HMAC-SHA256.

Examples:
    Basic usage::

        from adk_secure_sessions.backends.fernet import FernetBackend

        backend = FernetBackend(key="my-secret-passphrase")
        ciphertext = await backend.encrypt(b"hello")
        plaintext = await backend.decrypt(ciphertext)
"""

from __future__ import annotations

import asyncio
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from adk_secure_sessions.exceptions import DecryptionError

_PBKDF2_ITERATIONS = 480_000
_PBKDF2_SALT = b"adk-secure-sessions-fernet-v1"


class FernetBackend:
    """Fernet encryption backend conforming to ``EncryptionBackend``.

    Accepts a key as ``str`` or ``bytes``. If the key is a valid
    base64url-encoded 32-byte Fernet key, it is used directly.
    Otherwise, the key is derived via PBKDF2-HMAC-SHA256.

    Attributes:
        _fernet (Fernet): Internal Fernet instance for encrypt/decrypt
            operations.

    Examples:
        Initialize with a passphrase::

            backend = FernetBackend(key="my-secret")

        Initialize with a pre-generated Fernet key::

            from cryptography.fernet import Fernet

            key = Fernet.generate_key()
            backend = FernetBackend(key=key)
    """

    def __init__(self, key: str | bytes) -> None:
        """Initialize FernetBackend with the given key.

        Args:
            key: Encryption key as ``str`` or ``bytes``. A valid Fernet
                key is used directly; arbitrary input is derived via
                PBKDF2-HMAC-SHA256.

        Raises:
            TypeError: If *key* is not ``str`` or ``bytes``.
            ValueError: If *key* is empty.
        """
        if not isinstance(key, (str, bytes)):
            msg = f"key must be str or bytes, got {type(key).__name__}"
            raise TypeError(msg)

        if isinstance(key, str):
            key = key.encode()

        if not key:
            msg = "key must not be empty"
            raise ValueError(msg)

        fernet_key = self._resolve_key(key)
        self._fernet = Fernet(fernet_key)

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted ciphertext as bytes (Fernet token).

        Raises:
            TypeError: If *plaintext* is not ``bytes``.

        Examples:
            ```python
            ciphertext = await backend.encrypt(b"hello")
            ```
        """
        if not isinstance(plaintext, bytes):
            msg = f"plaintext must be bytes, got {type(plaintext).__name__}"
            raise TypeError(msg)

        return await asyncio.to_thread(self._fernet.encrypt, plaintext)

    async def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes.

        Args:
            ciphertext: Encrypted bytes (Fernet token) to decrypt.

        Returns:
            Decrypted plaintext as bytes.

        Raises:
            DecryptionError: If decryption fails due to wrong key,
                tampered ciphertext, or malformed input.

        Examples:
            ```python
            plaintext = await backend.decrypt(ciphertext)
            ```
        """
        try:
            return await asyncio.to_thread(self._fernet.decrypt, ciphertext)
        except InvalidToken:
            msg = "Decryption failed: invalid token or wrong key"
            raise DecryptionError(msg) from None

    @staticmethod
    def _resolve_key(key_bytes: bytes) -> bytes:
        """Resolve raw key bytes into a valid Fernet key.

        Attempts to use *key_bytes* directly as a Fernet key. If that
        fails, derives a key via PBKDF2-HMAC-SHA256.

        Args:
            key_bytes: Raw key material.

        Returns:
            A valid base64url-encoded 32-byte Fernet key.
        """
        try:
            Fernet(key_bytes)
            return key_bytes
        except (ValueError, Exception):  # noqa: BLE001
            derived = hashlib.pbkdf2_hmac(
                "sha256",
                key_bytes,
                _PBKDF2_SALT,
                _PBKDF2_ITERATIONS,
            )
            return base64.urlsafe_b64encode(derived)
