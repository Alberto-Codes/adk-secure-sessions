"""Session service implementations for adk-secure-sessions.

This module provides encrypted session storage services that implement
ADK's ``BaseSessionService`` interface with transparent field-level
encryption.

Attributes:
    EncryptedSessionService: Drop-in replacement for ADK's
        ``DatabaseSessionService`` with transparent encryption.

Examples:
    Import the encrypted service:

    ```python
    from adk_secure_sessions.services import EncryptedSessionService
    ```

See Also:
    [`adk_secure_sessions.services.encrypted_session`][adk_secure_sessions.services.encrypted_session]:
    Full service implementation with lifecycle examples.
"""

from adk_secure_sessions.services.encrypted_session import EncryptedSessionService

__all__ = ["EncryptedSessionService"]
