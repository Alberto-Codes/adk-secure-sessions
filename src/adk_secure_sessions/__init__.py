"""Encrypted session storage for Google ADK.

Provides field-level encryption for ADK session data via pluggable
encryption backends that conform to the ``EncryptionBackend`` protocol.

Attributes:
    EncryptionBackend (Protocol): Protocol defining the encrypt/decrypt
        contract.
    FernetBackend: Fernet symmetric encryption backend.
    EncryptedSessionService: Drop-in replacement for ADK's
        ``DatabaseSessionService`` with transparent encryption.
    SecureSessionError: Base exception for all library errors.
    EncryptionError: Raised when encryption fails.
    DecryptionError: Raised when decryption fails.
    SerializationError: Raised when data cannot be serialized to JSON.
    encrypt_session: Serialize a dict to an encrypted envelope.
    decrypt_session: Decrypt an envelope back to a dict.
    encrypt_json: Encrypt a JSON string into an envelope.
    decrypt_json: Decrypt an envelope back to a JSON string.
    BACKEND_FERNET: Backend identifier for Fernet encryption.
    ENVELOPE_VERSION_1: Current envelope format version byte.

Examples:
    Encrypt and decrypt session state::

        from adk_secure_sessions import (
            FernetBackend,
            encrypt_session,
            decrypt_session,
            BACKEND_FERNET,
        )

        backend = FernetBackend("my-secret-passphrase")
        envelope = await encrypt_session(
            {"ssn": "123-45-6789"}, backend, BACKEND_FERNET
        )
        state = await decrypt_session(envelope, backend)

See Also:
    [`adk_secure_sessions.protocols`][adk_secure_sessions.protocols]:
    Full protocol definition and known limitations.
"""

from adk_secure_sessions.backends.fernet import FernetBackend
from adk_secure_sessions.exceptions import (
    DecryptionError,
    EncryptionError,
    SecureSessionError,
    SerializationError,
)
from adk_secure_sessions.protocols import EncryptionBackend
from adk_secure_sessions.serialization import (
    BACKEND_FERNET,
    ENVELOPE_VERSION_1,
    decrypt_json,
    decrypt_session,
    encrypt_json,
    encrypt_session,
)
from adk_secure_sessions.services.encrypted_session import EncryptedSessionService

__all__ = [
    "BACKEND_FERNET",
    "DecryptionError",
    "EncryptedSessionService",
    "ENVELOPE_VERSION_1",
    "EncryptionBackend",
    "EncryptionError",
    "FernetBackend",
    "SecureSessionError",
    "SerializationError",
    "decrypt_json",
    "decrypt_session",
    "encrypt_json",
    "encrypt_session",
]
