"""Encrypted session storage for Google ADK.

Provides field-level encryption for ADK session data via pluggable
encryption backends that conform to the ``EncryptionBackend`` protocol.

Attributes:
    AesGcmBackend: AES-256-GCM authenticated encryption backend.
    BACKEND_AES_GCM: Backend identifier for AES-256-GCM encryption.
    BACKEND_FERNET: Backend identifier for Fernet encryption.
    ConfigurationError: Raised when the service is misconfigured at startup.
    DecryptionError: Raised when decryption fails.
    ENVELOPE_VERSION_1: Current envelope format version byte.
    EncryptedSessionService: Encrypted session service wrapping
        ``DatabaseSessionService`` with transparent encryption.
    EncryptionBackend (Protocol): Protocol defining the encrypt/decrypt
        contract.
    EncryptionError: Raised when encryption fails.
    FernetBackend: Fernet symmetric encryption backend.
    RotationResult: Result dataclass for key rotation operations.
    SecureSessionError: Base exception for all library errors.
    SerializationError: Raised when data cannot be serialized to JSON.
    decrypt_json: Decrypt an envelope back to a JSON string.
    decrypt_session: Decrypt an envelope back to a dict.
    encrypt_json: Encrypt a JSON string into an envelope.
    encrypt_session: Serialize a dict to an encrypted envelope.
    rotate_encryption_keys: Re-encrypt all session data to a new backend.

Examples:
    Encrypt and decrypt session state:

    ```python
    from adk_secure_sessions import (
        FernetBackend,
        encrypt_session,
        decrypt_session,
        BACKEND_FERNET,
    )

    backend = FernetBackend("my-secret-passphrase")
    envelope = await encrypt_session({"ssn": "123-45-6789"}, backend, BACKEND_FERNET)
    state = await decrypt_session(envelope, backend)
    ```

See Also:
    [`adk_secure_sessions.protocols`][adk_secure_sessions.protocols]:
    Full protocol definition and known limitations.
"""

from adk_secure_sessions.backends.aes_gcm import AesGcmBackend
from adk_secure_sessions.backends.fernet import FernetBackend
from adk_secure_sessions.exceptions import (
    ConfigurationError,
    DecryptionError,
    EncryptionError,
    SecureSessionError,
    SerializationError,
)
from adk_secure_sessions.protocols import EncryptionBackend
from adk_secure_sessions.rotation import RotationResult, rotate_encryption_keys
from adk_secure_sessions.serialization import (
    BACKEND_AES_GCM,
    BACKEND_FERNET,
    ENVELOPE_VERSION_1,
    decrypt_json,
    decrypt_session,
    encrypt_json,
    encrypt_session,
)
from adk_secure_sessions.services.encrypted_session import EncryptedSessionService

__all__ = [
    "AesGcmBackend",
    "BACKEND_AES_GCM",
    "BACKEND_FERNET",
    "ConfigurationError",
    "DecryptionError",
    "ENVELOPE_VERSION_1",
    "EncryptedSessionService",
    "EncryptionBackend",
    "EncryptionError",
    "FernetBackend",
    "RotationResult",
    "SecureSessionError",
    "SerializationError",
    "decrypt_json",
    "decrypt_session",
    "encrypt_json",
    "encrypt_session",
    "rotate_encryption_keys",
]
