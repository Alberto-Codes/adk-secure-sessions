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
)
from adk_secure_sessions.protocols import EncryptionBackend

__all__ = [
    "DecryptionError",
    "EncryptionBackend",
    "EncryptionError",
    "FernetBackend",
    "SecureSessionError",
]
