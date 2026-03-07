"""Fernet symmetric encryption backend.

Implements the ``EncryptionBackend`` protocol using
``cryptography.fernet.Fernet`` for authenticated symmetric encryption
(AES-128-CBC + HMAC-SHA256). Provides both async and synchronous
encrypt/decrypt methods plus a ``backend_id`` property for envelope
identification.

Keys can be provided as strings, bytes, or valid Fernet keys. Arbitrary
input is derived into a valid Fernet key via a two-phase key derivation
scheme:

1. **Extract (init time)**: PBKDF2-HMAC-SHA256 with 600,000 iterations
   stretches the passphrase into a 32-byte master key.
2. **Expand (per operation)**: HKDF-SHA256 with a fresh 16-byte random
   salt derives a unique per-operation Fernet key from the master key.

This ensures identical passphrases produce different ciphertexts on
every encryption, hardening against precomputation attacks.

Pre-generated Fernet keys (via ``Fernet.generate_key()``) bypass
derivation entirely and are used directly — no salt marker, no format
change.

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
import binascii
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from adk_secure_sessions.exceptions import ConfigurationError, DecryptionError
from adk_secure_sessions.serialization import BACKEND_FERNET

_PBKDF2_ITERATIONS = 600_000
_PBKDF2_ITERATIONS_LEGACY = 480_000
_PBKDF2_SALT = b"adk-secure-sessions-fernet-v1"

_SALT_MARKER = b"\x01"
_SALT_LENGTH = 16
_HKDF_INFO = b"adk-fernet-v2"
# Marker (1) + salt (16) + minimum base64-encoded Fernet token (~100 bytes).
_MIN_SALTED_LENGTH = 1 + _SALT_LENGTH + 100


class FernetBackend:
    """Fernet encryption backend conforming to ``EncryptionBackend``.

    Accepts a key as ``str`` or ``bytes``. If the key is a valid
    base64url-encoded 32-byte Fernet key, it is used directly (no
    derivation, no salt marker). Otherwise, a two-phase key derivation
    scheme is used:

    - **Init**: PBKDF2-HMAC-SHA256 (600,000 iterations) derives a master
      key from the passphrase.
    - **Per-operation**: HKDF-SHA256 with a fresh random salt expands
      the master key into a unique per-operation Fernet key.

    Backward compatibility: data encrypted with pre-3.2 fixed-salt
    derivation (480,000 iterations) is detected via marker byte and
    decrypted transparently.

    Attributes:
        _passphrase_key (bytes | None): Master key from PBKDF2 at 600k
            iterations (passphrase mode only, ``None`` in direct-key mode).
        _legacy_fernet (Fernet): Fernet instance for direct-key mode or
            legacy (480k iterations) backward-compatible decryption.
        _is_passphrase_mode (bool): Whether the backend was initialized
            with a passphrase (True) or a pre-generated Fernet key (False).

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
                two-phase PBKDF2 + HKDF.

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

        if self._is_valid_fernet_key(key):
            self._passphrase_key: bytes | None = None
            self._legacy_fernet = Fernet(key)
            self._is_passphrase_mode = False
        else:
            self._passphrase_key = self._derive_master_key(key, _PBKDF2_ITERATIONS)
            legacy_raw = self._derive_master_key(key, _PBKDF2_ITERATIONS_LEGACY)
            self._legacy_fernet = Fernet(base64.urlsafe_b64encode(legacy_raw))
            self._is_passphrase_mode = True

    @property
    def backend_id(self) -> int:
        """Unique backend identifier for the envelope header.

        Returns:
            ``BACKEND_FERNET`` (``0x01``).
        """
        return BACKEND_FERNET

    def sync_encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes synchronously.

        In passphrase mode, generates a fresh 16-byte random salt,
        derives a per-operation Fernet key via HKDF, and returns
        ``SALT_MARKER || salt || fernet_token``. In direct-key mode,
        returns a standard Fernet token.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted ciphertext as bytes.

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

        if not self._is_passphrase_mode:
            return self._legacy_fernet.encrypt(plaintext)

        salt = os.urandom(_SALT_LENGTH)
        per_op_key = self._derive_per_op_key(salt)
        token = Fernet(per_op_key).encrypt(plaintext)
        return _SALT_MARKER + salt + token

    def sync_decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes synchronously.

        Detects the ciphertext format via the first byte:

        - ``0x01``: new salted format — extract salt, derive per-op key
          via HKDF, decrypt the Fernet token.
        - ``>= 0x2B``: legacy Fernet token — decrypt with the legacy
          Fernet instance.
        - Otherwise: raise ``DecryptionError``.

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

        if not ciphertext:
            msg = "Decryption failed: invalid token or wrong key"
            raise DecryptionError(msg)

        if ciphertext[0:1] == _SALT_MARKER and len(ciphertext) >= _MIN_SALTED_LENGTH:
            return self._decrypt_salted(ciphertext)

        if ciphertext[0] >= 0x2B:
            return self._decrypt_legacy(ciphertext)

        msg = "Decryption failed: invalid ciphertext format"
        raise DecryptionError(msg)

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes asynchronously.

        Delegates to ``sync_encrypt`` via ``asyncio.to_thread()``.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted ciphertext as bytes.

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

    def _derive_per_op_key(self, salt: bytes) -> bytes:
        """Derive a per-operation Fernet key via HKDF-SHA256.

        Args:
            salt: Random salt for HKDF domain separation.

        Returns:
            A valid base64url-encoded 32-byte Fernet key.
        """
        raw = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=_HKDF_INFO,
        ).derive(self._passphrase_key)  # type: ignore[arg-type]
        return base64.urlsafe_b64encode(raw)

    def _decrypt_salted(self, ciphertext: bytes) -> bytes:
        """Decrypt new-format salted ciphertext.

        Args:
            ciphertext: Full ciphertext including marker and salt.

        Returns:
            Decrypted plaintext.

        Raises:
            DecryptionError: If decryption fails.
        """
        salt = ciphertext[1 : 1 + _SALT_LENGTH]
        token = ciphertext[1 + _SALT_LENGTH :]

        if self._passphrase_key is None:
            msg = "Decryption failed: invalid token or wrong key"
            raise DecryptionError(msg)

        per_op_key = self._derive_per_op_key(salt)
        try:
            return Fernet(per_op_key).decrypt(token)
        except InvalidToken:
            msg = "Decryption failed: invalid token or wrong key"
            raise DecryptionError(msg) from None

    def _decrypt_legacy(self, ciphertext: bytes) -> bytes:
        """Decrypt legacy Fernet token (pre-3.2 or direct-key mode).

        Args:
            ciphertext: Legacy Fernet token bytes.

        Returns:
            Decrypted plaintext.

        Raises:
            DecryptionError: If decryption fails.
        """
        try:
            return self._legacy_fernet.decrypt(ciphertext)
        except InvalidToken:
            msg = "Decryption failed: invalid token or wrong key"
            raise DecryptionError(msg) from None

    @staticmethod
    def _is_valid_fernet_key(key_bytes: bytes) -> bool:
        """Check whether key_bytes is a valid Fernet key.

        Attempts to construct a ``Fernet`` instance. Returns ``False``
        on ``ValueError`` (wrong key length) or ``binascii.Error``
        (non-base64 input).

        Args:
            key_bytes: Raw key material.

        Returns:
            True if the bytes are a valid Fernet key.
        """
        try:
            Fernet(key_bytes)
            return True
        except (ValueError, binascii.Error):
            return False

    @staticmethod
    def _derive_master_key(passphrase: bytes, iterations: int) -> bytes:
        """Derive a 32-byte master key via PBKDF2-HMAC-SHA256.

        Args:
            passphrase: Raw passphrase bytes.
            iterations: Number of PBKDF2 iterations.

        Returns:
            32-byte raw derived key.
        """
        return hashlib.pbkdf2_hmac(
            "sha256",
            passphrase,
            _PBKDF2_SALT,
            iterations,
        )
