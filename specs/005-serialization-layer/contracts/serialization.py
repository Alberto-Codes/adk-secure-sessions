"""Contract: Serialization Layer Public API.

This file defines the public function signatures and constants
for the serialization module. It is a design artifact, not runnable code.
"""

# --- Constants ---

ENVELOPE_VERSION_1: int = 0x01
BACKEND_FERNET: int = 0x01

BACKEND_REGISTRY: dict[int, str] = {
    BACKEND_FERNET: "Fernet",
}

# --- Public Functions ---


async def encrypt_session(
    data: dict,
    backend: "EncryptionBackend",
    backend_id: int,
) -> bytes:
    """Serialize a session state dict to an encrypted envelope.

    Args:
        data: JSON-serializable Python dictionary.
        backend: Any EncryptionBackend-conformant object.
        backend_id: Integer identifying the backend (from BACKEND_REGISTRY).

    Returns:
        Encrypted envelope bytes: [version][backend_id][ciphertext].

    Raises:
        SerializationError: If data cannot be serialized to JSON.
        EncryptionError: If the backend fails to encrypt.
    """
    ...


async def decrypt_session(
    envelope: bytes,
    backend: "EncryptionBackend",
) -> dict:
    """Decrypt an encrypted envelope back to a session state dict.

    Args:
        envelope: Encrypted envelope bytes (>= 3 bytes).
        backend: Any EncryptionBackend-conformant object.

    Returns:
        Original Python dictionary.

    Raises:
        DecryptionError: If envelope is invalid, tampered, or backend fails.
        SerializationError: If decrypted bytes are not valid JSON.
    """
    ...


async def encrypt_json(
    json_str: str,
    backend: "EncryptionBackend",
    backend_id: int,
) -> bytes:
    """Encrypt a pre-serialized JSON string into an encrypted envelope.

    Args:
        json_str: Valid JSON string (e.g., from model_dump_json()).
        backend: Any EncryptionBackend-conformant object.
        backend_id: Integer identifying the backend.

    Returns:
        Encrypted envelope bytes: [version][backend_id][ciphertext].

    Raises:
        EncryptionError: If the backend fails to encrypt.
    """
    ...


async def decrypt_json(
    envelope: bytes,
    backend: "EncryptionBackend",
) -> str:
    """Decrypt an encrypted envelope back to a JSON string.

    Args:
        envelope: Encrypted envelope bytes (>= 3 bytes).
        backend: Any EncryptionBackend-conformant object.

    Returns:
        Original JSON string.

    Raises:
        DecryptionError: If envelope is invalid, tampered, or backend fails.
    """
    ...
