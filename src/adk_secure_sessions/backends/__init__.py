"""Encryption backend implementations for adk-secure-sessions.

Attributes:
    AesGcmBackend: AES-256-GCM authenticated encryption backend.
    FernetBackend: Fernet symmetric encryption backend.

Examples:
    Import the Fernet backend:

    ```python
    from adk_secure_sessions.backends.fernet import FernetBackend
    ```

    Import the AES-GCM backend:

    ```python
    from adk_secure_sessions.backends.aes_gcm import AesGcmBackend
    ```

See Also:
    [`adk_secure_sessions.backends.fernet`][adk_secure_sessions.backends.fernet]:
    Fernet symmetric encryption backend.

    [`adk_secure_sessions.backends.aes_gcm`][adk_secure_sessions.backends.aes_gcm]:
    AES-256-GCM authenticated encryption backend.
"""

from adk_secure_sessions.backends.aes_gcm import AesGcmBackend
from adk_secure_sessions.backends.fernet import FernetBackend

__all__ = ["AesGcmBackend", "FernetBackend"]
