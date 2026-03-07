"""AES-256-GCM authenticated encryption backend.

Implements the ``EncryptionBackend`` protocol using
``cryptography.hazmat.primitives.ciphers.aead.AESGCM`` for authenticated
encryption with associated data (AEAD) per NIST SP 800-38D.

Keys must be exactly 32 bytes (256 bits). No key derivation is performed;
use ``AESGCM.generate_key(bit_length=256)`` to generate a suitable key.

Each encryption generates a fresh 12-byte (96-bit) random nonce via
``os.urandom(12)``. The ciphertext format is
``nonce (12 bytes) || ciphertext + tag``.

Examples:
    Basic usage:

    ```python
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    from adk_secure_sessions.backends.aes_gcm import AesGcmBackend

    key = AESGCM.generate_key(bit_length=256)
    backend = AesGcmBackend(key=key)
    ciphertext = await backend.encrypt(b"hello")
    plaintext = await backend.decrypt(ciphertext)
    ```

See Also:
    [`adk_secure_sessions.protocols`][]: EncryptionBackend protocol definition.
"""

from __future__ import annotations

import asyncio
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from adk_secure_sessions.exceptions import ConfigurationError, DecryptionError
from adk_secure_sessions.serialization import BACKEND_AES_GCM

_NONCE_LENGTH = 12
_KEY_LENGTH = 32
_MIN_CIPHERTEXT_LENGTH = _NONCE_LENGTH + 16  # nonce + 128-bit tag


class AesGcmBackend:
    """AES-256-GCM encryption backend conforming to ``EncryptionBackend``.

    Accepts a key as exactly 32 bytes (256 bits). Use
    ``AESGCM.generate_key(bit_length=256)`` to generate a valid key.

    Attributes:
        _aesgcm (AESGCM): Internal AESGCM instance for encrypt/decrypt
            operations.

    Examples:
        Initialize with a generated key:

        ```python
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = AESGCM.generate_key(bit_length=256)
        backend = AesGcmBackend(key=key)
        ```
    """

    def __init__(self, key: bytes) -> None:
        """Initialize AesGcmBackend with the given key.

        Args:
            key: Encryption key as exactly 32 bytes (256 bits).

        Raises:
            ConfigurationError: If *key* is not ``bytes`` or is not
                exactly 32 bytes long.
        """
        if not isinstance(key, bytes):
            msg = f"key must be bytes, got {type(key).__name__}"
            raise ConfigurationError(msg)

        if len(key) != _KEY_LENGTH:
            msg = f"key must be exactly {_KEY_LENGTH} bytes, got {len(key)}"
            raise ConfigurationError(msg)

        self._aesgcm = AESGCM(key)

    @property
    def backend_id(self) -> int:
        """Unique backend identifier for the envelope header.

        Returns:
            ``BACKEND_AES_GCM`` (``0x02``).
        """
        return BACKEND_AES_GCM

    def sync_encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes synchronously.

        Generates a fresh 12-byte random nonce per call. Returns
        ``nonce || ciphertext + tag``.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted bytes as ``nonce (12) || ciphertext + tag``.

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

        nonce = os.urandom(_NONCE_LENGTH)
        ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext_and_tag

    def sync_decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes synchronously.

        Expects ``nonce (12 bytes) || ciphertext + tag``.

        Args:
            ciphertext: Encrypted bytes to decrypt.

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

        if len(ciphertext) < _MIN_CIPHERTEXT_LENGTH:
            msg = "Decryption failed: ciphertext too short"
            raise DecryptionError(msg)

        nonce = ciphertext[:_NONCE_LENGTH]
        ct_and_tag = ciphertext[_NONCE_LENGTH:]

        try:
            return self._aesgcm.decrypt(nonce, ct_and_tag, None)
        except InvalidTag:
            msg = "Decryption failed: invalid tag or wrong key"
            raise DecryptionError(msg) from None

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes asynchronously.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted bytes as ``nonce (12) || ciphertext + tag``.

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

        Args:
            ciphertext: Encrypted bytes to decrypt.

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
