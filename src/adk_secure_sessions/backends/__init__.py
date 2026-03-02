"""Encryption backend implementations for adk-secure-sessions.

Attributes:
    FernetBackend: Fernet symmetric encryption backend.

Examples:
    Import the Fernet backend:

    ```python
    from adk_secure_sessions.backends.fernet import FernetBackend
    ```

See Also:
    [`adk_secure_sessions.backends.fernet`][adk_secure_sessions.backends.fernet]:
    Fernet symmetric encryption backend.
"""

from adk_secure_sessions.backends.fernet import FernetBackend

__all__ = ["FernetBackend"]
