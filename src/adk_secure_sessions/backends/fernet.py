"""Fernet symmetric encryption backend.

Implements the ``EncryptionBackend`` protocol using
``cryptography.fernet.Fernet`` for authenticated symmetric encryption
(AES-128-CBC + HMAC-SHA256). Provides both async and synchronous
encrypt/decrypt methods plus a ``backend_id`` property.

Keys can be provided as strings, bytes, or valid Fernet keys. Arbitrary
input is derived into a valid Fernet key via PBKDF2-HMAC-SHA256.

!!! warning "Fixed Salt"
    Passphrase-based key derivation uses a fixed, application-scoped salt.
    This means identical passphrases will always produce the same Fernet
    key across all `FernetBackend` instances. For production use, prefer
    unique passphrases per application/context or use pre-generated Fernet
    keys via `cryptography.fernet.Fernet.generate_key()`.

Examples:
    Basic usage:

    ```python
    from adk_secure_sessions.backends.fernet import FernetBackend

    backend = FernetBackend(key="my-secret-passphrase")
    ciphertext = await backend.encrypt(b"hello")
    plaintext = await backend.decrypt(ciphertext)
    ```

See Also:
    [`adk_secure_sessions.protocols`][]: EncryptionBackend protocol definition.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from adk_secure_sessions.exceptions import ConfigurationError, DecryptionError
from adk_secure_sessions.serialization import BACKEND_FERNET

_PBKDF2_ITERATIONS = 480_000
_PBKDF2_SALT = b"adk-secure-sessions-fernet-v1"


class FernetBackend:
    """Fernet encryption backend conforming to ``EncryptionBackend``.

    Accepts a key as ``str`` or ``bytes``. If the key is a valid
    base64url-encoded 32-byte Fernet key, it is used directly.
    Otherwise, the key is derived via PBKDF2-HMAC-SHA256.

    Provides ``sync_encrypt``/``sync_decrypt`` for synchronous contexts
    (e.g., SQLAlchemy TypeDecorators) and ``encrypt``/``decrypt`` async
    wrappers. The ``backend_id`` property returns ``BACKEND_FERNET``
    (``0x01``).

    Attributes:
        _fernet (Fernet): Internal Fernet instance for encrypt/decrypt
            operations.

    Examples:
        Initialize with a passphrase:

        ```python
        backend = FernetBackend(key="my-secret")
        ```

        Initialize with a pre-generated Fernet key:

        ```python
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()
        backend = FernetBackend(key=key)
        ```
    """

    def __init__(self, key: str | bytes) -> None:
        """Initialize FernetBackend with the given key.

        Args:
            key: Encryption key as ``str`` or ``bytes``. A valid Fernet
                key is used directly; arbitrary input is derived via
                PBKDF2-HMAC-SHA256.

        Raises:
            ConfigurationError: If *key* is not ``str`` or ``bytes``,
                or if *key* is empty.
        """
        if not isinstance(key, (str, bytes)):
            msg = f"key must be str or bytes, got {type(key).__name__}"
            raise ConfigurationError(msg)

        if isinstance(key, str):
            key = key.encode()

        if not key:
            msg = "key must not be empty"
            raise ConfigurationError(msg)

        fernet_key = self._resolve_key(key)
        self._fernet = Fernet(fernet_key)

    @property
    def backend_id(self) -> int:
        """Unique backend identifier for the envelope header.

        Returns:
            ``BACKEND_FERNET`` (``0x01``).
        """
        return BACKEND_FERNET

    def sync_encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes synchronously.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted ciphertext as bytes (Fernet token).

        Raises:
            TypeError: If *plaintext* is not ``bytes``.

        Examples:
            ```python
            ciphertext = backend.sync_encrypt(b"hello")
            ```
        """
        if not isinstance(plaintext, bytes):
            msg = f"plaintext must be bytes, got {type(plaintext).__name__}"
            raise TypeError(msg)

        return self._fernet.encrypt(plaintext)

    def sync_decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes synchronously.

        Args:
            ciphertext: Encrypted bytes (Fernet token) to decrypt.

        Returns:
            Decrypted plaintext as bytes.

        Raises:
            TypeError: If *ciphertext* is not ``bytes``.
            DecryptionError: If decryption fails due to wrong key,
                tampered ciphertext, or malformed input.

        Examples:
            ```python
            plaintext = backend.sync_decrypt(ciphertext)
            ```
        """
        if not isinstance(ciphertext, bytes):
            msg = f"ciphertext must be bytes, got {type(ciphertext).__name__}"
            raise TypeError(msg)

        try:
            return self._fernet.decrypt(ciphertext)
        except InvalidToken:
            msg = "Decryption failed: invalid token or wrong key"
            raise DecryptionError(msg) from None

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes asynchronously.

        Delegates to ``sync_encrypt`` via ``asyncio.to_thread()``.

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

        return await asyncio.to_thread(self.sync_encrypt, plaintext)

    async def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes asynchronously.

        Delegates to ``sync_decrypt`` via ``asyncio.to_thread()``.

        Args:
            ciphertext: Encrypted bytes (Fernet token) to decrypt.

        Returns:
            Decrypted plaintext as bytes.

        Raises:
            TypeError: If *ciphertext* is not ``bytes``.
            DecryptionError: If decryption fails due to wrong key,
                tampered ciphertext, or malformed input.

        Examples:
            ```python
            plaintext = await backend.decrypt(ciphertext)
            ```
        """
        if not isinstance(ciphertext, bytes):
            msg = f"ciphertext must be bytes, got {type(ciphertext).__name__}"
            raise TypeError(msg)

        return await asyncio.to_thread(self.sync_decrypt, ciphertext)

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
        except ValueError:
            derived = hashlib.pbkdf2_hmac(
                "sha256",
                key_bytes,
                _PBKDF2_SALT,
                _PBKDF2_ITERATIONS,
            )
            return base64.urlsafe_b64encode(derived)
