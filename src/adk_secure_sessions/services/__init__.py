"""Session service implementations for adk-secure-sessions.

This module provides encrypted session storage services that implement
ADK's ``BaseSessionService`` interface with transparent field-level
encryption.

Attributes:
    EncryptedSessionService: Drop-in replacement for ADK's
        ``DatabaseSessionService`` with transparent encryption.
"""

from adk_secure_sessions.services.encrypted_session import EncryptedSessionService

__all__ = ["EncryptedSessionService"]
