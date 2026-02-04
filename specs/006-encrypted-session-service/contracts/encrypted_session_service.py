"""Contract definition for EncryptedSessionService.

This file defines the public API contract that EncryptedSessionService
must implement. It serves as both documentation and a type-checking
reference for the implementation.

Note: This is a contract specification, not the actual implementation.
The implementation will live in src/adk_secure_sessions/services/.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from google.adk.events.event import Event
    from google.adk.sessions.base_session_service import (
        GetSessionConfig,
        ListSessionsResponse,
    )
    from google.adk.sessions.session import Session

    from adk_secure_sessions.protocols import EncryptionBackend


class EncryptedSessionServiceContract:
    """Contract for EncryptedSessionService.

    Implements BaseSessionService with transparent field-level encryption
    for session state and event data. Drop-in replacement for ADK's
    DatabaseSessionService.

    Attributes:
        db_path: Path to the SQLite database file.
        backend: Encryption backend conforming to EncryptionBackend protocol.
        backend_id: Integer identifier for the backend (for envelope format).

    Examples:
        Basic usage with FernetBackend::

            from adk_secure_sessions import FernetBackend, BACKEND_FERNET
            from adk_secure_sessions.services import EncryptedSessionService

            backend = FernetBackend("my-secret-passphrase")
            async with EncryptedSessionService(
                db_path="sessions.db",
                backend=backend,
                backend_id=BACKEND_FERNET,
            ) as service:
                session = await service.create_session(
                    app_name="my-agent",
                    user_id="user-123",
                    state={"secret": "sensitive-data"},
                )
    """

    def __init__(
        self,
        db_path: str,
        backend: EncryptionBackend,
        backend_id: int,
    ) -> None:
        """Initialize the encrypted session service.

        Args:
            db_path: Path to the SQLite database file. Created if not exists.
            backend: Any object conforming to EncryptionBackend protocol.
            backend_id: Integer identifier for the backend (e.g., BACKEND_FERNET).
        """
        ...

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> Session:
        """Create a new session with encrypted state.

        Args:
            app_name: Application name for the session.
            user_id: User identifier for the session.
            state: Optional initial state dictionary. Encrypted before storage.
            session_id: Optional session ID. Generated if not provided.

        Returns:
            Session object with the created session data.

        Raises:
            AlreadyExistsError: If a session with the given ID already exists.
            EncryptionError: If state encryption fails.
            SerializationError: If state contains non-JSON-serializable values.
        """
        ...

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: GetSessionConfig | None = None,
    ) -> Session | None:
        """Retrieve a session with decrypted state and events.

        Args:
            app_name: Application name for the session.
            user_id: User identifier for the session.
            session_id: Session ID to retrieve.
            config: Optional configuration for event filtering.
                - num_recent_events: Limit events to N most recent.
                - after_timestamp: Only include events after this timestamp.

        Returns:
            Session object with decrypted state and events, or None if not found.

        Raises:
            DecryptionError: If state or event decryption fails.
            SerializationError: If decrypted data is not valid JSON.
        """
        ...

    async def list_sessions(
        self,
        *,
        app_name: str,
        user_id: str | None = None,
    ) -> ListSessionsResponse:
        """List sessions for an application with decrypted state.

        Args:
            app_name: Application name to filter by.
            user_id: Optional user ID to filter by. If None, returns all users.

        Returns:
            ListSessionsResponse containing list of Session objects.

        Raises:
            DecryptionError: If state decryption fails for any session.
        """
        ...

    async def delete_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> None:
        """Delete a session and its associated events.

        Args:
            app_name: Application name for the session.
            user_id: User identifier for the session.
            session_id: Session ID to delete.

        Note:
            This operation cascades to delete all events for the session.
            No error is raised if the session does not exist.
        """
        ...

    async def append_event(
        self,
        session: Session,
        event: Event,
    ) -> Event:
        """Append an event to a session with encrypted storage.

        This method overrides the base class to add database persistence.
        The event data is encrypted before storage. State deltas are
        extracted and applied to app/user/session state as appropriate.

        Args:
            session: Session object to append the event to.
            event: Event object to append.

        Returns:
            The appended Event (possibly modified by state trimming).

        Raises:
            EncryptionError: If event encryption fails.
            SerializationError: If event contains non-serializable values.

        Note:
            Events with event.partial=True are not persisted to the database.
            The session's in-memory state is updated via the base class methods.
        """
        ...

    async def close(self) -> None:
        """Close the database connection.

        Should be called when the service is no longer needed.
        Automatically called when using the async context manager.
        """
        ...

    async def __aenter__(self) -> EncryptedSessionServiceContract:
        """Enter the async context manager.

        Returns:
            The service instance.
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the async context manager and close the connection.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        ...
