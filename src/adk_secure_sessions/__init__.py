"""Encrypted session storage for Google ADK.

Provides field-level encryption for ADK session data via pluggable
encryption backends that conform to the ``EncryptionBackend`` protocol.

Attributes:
    EncryptionBackend (Protocol): Protocol defining the encrypt/decrypt
        contract.
    FernetBackend: Fernet symmetric encryption backend.
    SecureSessionError: Base exception for all library errors.
    EncryptionError: Raised when encryption fails.
    DecryptionError: Raised when decryption fails.

Examples:
    Import and use the protocol for runtime validation::

        from adk_secure_sessions import EncryptionBackend

        assert isinstance(my_backend, EncryptionBackend)

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

__all__ = [
    "BACKEND_FERNET",
    "DecryptionError",
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
