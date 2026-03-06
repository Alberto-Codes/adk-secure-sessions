"""Session service implementations for adk-secure-sessions.

This module provides encrypted session storage services that wrap
ADK's ``DatabaseSessionService`` with transparent field-level
encryption via SQLAlchemy TypeDecorator column encryption.

Attributes:
    EncryptedSessionService: Encrypted wrapper around ADK's
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
