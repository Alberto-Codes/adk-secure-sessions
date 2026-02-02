"""Serialization layer for encrypting session state and event data.

Converts Python dictionaries and JSON strings into self-describing
encrypted envelopes using any ``EncryptionBackend``-conformant backend.
Each envelope carries a version byte and backend identifier prefix to
support future backend migrations.

The layer is stateless — four async module-level functions, no classes.
The encryption backend is passed per call.

Examples:
    Encrypt and decrypt a session state dictionary::

        from adk_secure_sessions.serialization import (
            encrypt_session,
            decrypt_session,
            BACKEND_FERNET,
        )

        envelope = await encrypt_session(state, backend, BACKEND_FERNET)
        restored = await decrypt_session(envelope, backend)
"""

from __future__ import annotations

import json

from adk_secure_sessions.exceptions import DecryptionError, SerializationError
from adk_secure_sessions.protocols import EncryptionBackend

ENVELOPE_VERSION_1: int = 0x01
"""Current envelope format version byte."""

BACKEND_FERNET: int = 0x01
"""Backend identifier for Fernet encryption."""

BACKEND_REGISTRY: dict[int, str] = {
    BACKEND_FERNET: "Fernet",
}
"""Mapping of backend IDs to human-readable names (error messages only)."""

_MIN_ENVELOPE_LENGTH: int = 3
"""Minimum envelope size: 1 version byte + 1 backend ID byte + 1+ ciphertext bytes."""


def _build_envelope(version: int, backend_id: int, ciphertext: bytes) -> bytes:
    """Build a self-describing encrypted envelope.

    Args:
        version: Envelope format version byte.
        backend_id: Integer identifying the encryption backend.
        ciphertext: Encrypted payload from the backend.

    Returns:
        Envelope bytes: ``[version][backend_id][ciphertext]``.
    """
    return bytes([version, backend_id]) + ciphertext


def _parse_envelope(envelope: bytes) -> tuple[int, int, bytes]:
    """Parse and validate an encrypted envelope.

    Args:
        envelope: Raw envelope bytes to parse.

    Returns:
        Tuple of (version, backend_id, ciphertext).

    Raises:
        DecryptionError: If the envelope is too short, has an
            unrecognized version, or unrecognized backend ID.
    """
    if len(envelope) < _MIN_ENVELOPE_LENGTH:
        msg = "Envelope too short: expected at least 3 bytes"
        raise DecryptionError(msg)

    version = envelope[0]
    backend_id = envelope[1]
    ciphertext = envelope[2:]

    if version != ENVELOPE_VERSION_1:
        msg = f"Unsupported envelope version: {version}"
        raise DecryptionError(msg)

    if backend_id not in BACKEND_REGISTRY:
        msg = f"Unsupported encryption backend: {backend_id}"
        raise DecryptionError(msg)

    return version, backend_id, ciphertext


async def encrypt_session(
    data: dict,
    backend: EncryptionBackend,
    backend_id: int,
) -> bytes:
    """Serialize a session state dict to an encrypted envelope.

    Args:
        data: JSON-serializable Python dictionary.
        backend: Any ``EncryptionBackend``-conformant object.
        backend_id: Integer identifying the backend.

    Returns:
        Encrypted envelope bytes: ``[version][backend_id][ciphertext]``.

    Raises:
        SerializationError: If *data* cannot be serialized to JSON.

    Examples:
        ```python
        envelope = await encrypt_session(
            {"ssn": "123-45-6789"}, backend, BACKEND_FERNET
        )
        ```
    """
    try:
        plaintext = json.dumps(data).encode()
    except (TypeError, ValueError) as exc:
        msg = "Failed to serialize session data to JSON"
        raise SerializationError(msg) from exc
    ciphertext = await backend.encrypt(plaintext)
    return _build_envelope(ENVELOPE_VERSION_1, backend_id, ciphertext)


async def decrypt_session(
    envelope: bytes,
    backend: EncryptionBackend,
) -> dict:
    """Decrypt an encrypted envelope back to a session state dict.

    Args:
        envelope: Encrypted envelope bytes (>= 3 bytes).
        backend: Any ``EncryptionBackend``-conformant object.

    Returns:
        Original Python dictionary.

    Raises:
        DecryptionError: If envelope is invalid, tampered, or backend fails.
        SerializationError: If decrypted bytes are not valid JSON.

    Examples:
        ```python
        state = await decrypt_session(envelope, backend)
        ```
    """
    _version, _backend_id, ciphertext = _parse_envelope(envelope)
    plaintext = await backend.decrypt(ciphertext)
    try:
        data = json.loads(plaintext)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        msg = "Failed to deserialize decrypted data from JSON"
        raise SerializationError(msg) from exc
    return data


async def encrypt_json(
    json_str: str,
    backend: EncryptionBackend,
    backend_id: int,
) -> bytes:
    """Encrypt a pre-serialized JSON string into an encrypted envelope.

    Args:
        json_str: Valid JSON string (e.g., from ``model_dump_json()``).
        backend: Any ``EncryptionBackend``-conformant object.
        backend_id: Integer identifying the backend.

    Returns:
        Encrypted envelope bytes: ``[version][backend_id][ciphertext]``.

    Examples:
        ```python
        envelope = await encrypt_json(event.model_dump_json(), backend, BACKEND_FERNET)
        ```
    """
    plaintext = json_str.encode("utf-8")
    ciphertext = await backend.encrypt(plaintext)
    return _build_envelope(ENVELOPE_VERSION_1, backend_id, ciphertext)


async def decrypt_json(
    envelope: bytes,
    backend: EncryptionBackend,
) -> str:
    """Decrypt an encrypted envelope back to a JSON string.

    Args:
        envelope: Encrypted envelope bytes (>= 3 bytes).
        backend: Any ``EncryptionBackend``-conformant object.

    Returns:
        Original JSON string.

    Raises:
        DecryptionError: If envelope is invalid, tampered, backend fails,
            or decrypted bytes are not valid UTF-8.

    Examples:
        ```python
        json_str = await decrypt_json(envelope, backend)
        ```
    """
    _version, _backend_id, ciphertext = _parse_envelope(envelope)
    plaintext = await backend.decrypt(ciphertext)
    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        msg = "Failed to decode decrypted data as UTF-8"
        raise DecryptionError(msg) from exc
