"""Encrypted session service implementation.

Provides a drop-in replacement for ADK's ``DatabaseSessionService`` with
transparent field-level encryption for session state and event data.

Examples:
    Basic usage with FernetBackend:

    ```python
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
        retrieved = await service.get_session(
            app_name="my-agent",
            user_id="user-123",
            session_id=session.id,
        )
    ```

See Also:
    [`adk_secure_sessions.backends.fernet`][]: Fernet encryption backend.
    [`adk_secure_sessions.protocols`][]: EncryptionBackend protocol definition.
"""

from __future__ import annotations

import sqlite3
import time
import uuid
from typing import TYPE_CHECKING, Any

import aiosqlite
from google.adk.events.event import Event
from google.adk.sessions.base_session_service import (
    BaseSessionService,
    GetSessionConfig,
    ListSessionsResponse,
)
from google.adk.sessions.session import Session

from adk_secure_sessions.exceptions import ConfigurationError
from adk_secure_sessions.protocols import EncryptionBackend
from adk_secure_sessions.serialization import (
    decrypt_json,
    decrypt_session,
    encrypt_json,
    encrypt_session,
)

if TYPE_CHECKING:
    from types import TracebackType

# SQL schema for encrypted session storage
_SCHEMA = """
-- App-level state
CREATE TABLE IF NOT EXISTS app_states (
    app_name TEXT PRIMARY KEY,
    state BLOB NOT NULL,
    update_time REAL NOT NULL,
    version INTEGER DEFAULT 1
);

-- User-level state
CREATE TABLE IF NOT EXISTS user_states (
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    state BLOB NOT NULL,
    update_time REAL NOT NULL,
    version INTEGER DEFAULT 1,
    PRIMARY KEY (app_name, user_id)
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    id TEXT NOT NULL,
    state BLOB NOT NULL,
    create_time REAL NOT NULL,
    update_time REAL NOT NULL,
    version INTEGER DEFAULT 1,
    PRIMARY KEY (app_name, user_id, id)
);

-- Events
CREATE TABLE IF NOT EXISTS events (
    id TEXT NOT NULL,
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    invocation_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    event_data BLOB NOT NULL,
    PRIMARY KEY (app_name, user_id, session_id, id),
    FOREIGN KEY (app_name, user_id, session_id)
        REFERENCES sessions(app_name, user_id, id) ON DELETE CASCADE
);

-- Index for efficient event queries by timestamp
CREATE INDEX IF NOT EXISTS idx_events_timestamp
    ON events(app_name, user_id, session_id, timestamp);

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;
"""


class EncryptedSessionService(BaseSessionService):
    """Encrypted session service implementing BaseSessionService.

    Provides transparent field-level encryption for session state and
    event data. Drop-in replacement for ADK's ``DatabaseSessionService``.

    Attributes:
        db_path (str): Path to the SQLite database file (read-only after init).
        backend (EncryptionBackend): Encryption backend instance (read-only after init).
        backend_id (int): Integer backend identifier for the envelope format (read-only after init).

    Examples:
        Basic usage with FernetBackend:

        ```python
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
            retrieved = await service.get_session(
                app_name="my-agent",
                user_id="user-123",
                session_id=session.id,
            )
        ```
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

        Raises:
            ConfigurationError: If *db_path* is not a non-empty string,
                *backend* does not conform to ``EncryptionBackend``,
                *backend_id* is not an ``int``, or *backend_id* is
                outside the valid byte range (0–255).
        """
        if not isinstance(db_path, str) or not db_path:
            msg = "db_path must be a non-empty string"
            raise ConfigurationError(msg)
        if not isinstance(backend, EncryptionBackend):
            msg = (
                f"backend must conform to EncryptionBackend protocol, "
                f"got {type(backend).__name__}"
            )
            raise ConfigurationError(msg)
        if not isinstance(backend_id, int):
            msg = f"backend_id must be an int, got {type(backend_id).__name__}"
            raise ConfigurationError(msg)
        if not (0 <= backend_id <= 255):
            msg = (
                f"backend_id must be in range 0–255, got {backend_id}. "
                f"Use BACKEND_FERNET (0x01) for Fernet encryption."
            )
            raise ConfigurationError(msg)

        self._db_path = db_path
        self._backend = backend
        self._backend_id = backend_id
        self._connection: aiosqlite.Connection | None = None

    async def _init_db(self) -> aiosqlite.Connection:
        """Initialize the database connection and create tables if needed.

        Returns:
            The database connection.

        Raises:
            ConfigurationError: If the database connection fails.
        """
        if self._connection is None:
            try:
                self._connection = await aiosqlite.connect(self._db_path)
            except (OSError, sqlite3.OperationalError) as exc:
                msg = (
                    f"Failed to connect to database at "
                    f"'{self._db_path}': {exc}. "
                    f"Check that the path exists and is writable."
                )
                raise ConfigurationError(msg) from exc
            await self._connection.executescript(_SCHEMA)
            await self._connection.commit()
        return self._connection

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get the database connection, initializing if needed.

        Returns:
            The database connection.
        """
        if self._connection is None:
            return await self._init_db()
        return self._connection

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

        Examples:
            Create a session with initial state:

            ```python
            session = await service.create_session(
                app_name="my-agent",
                user_id="user-123",
                state={"preference": "dark-mode"},
            )
            ```
        """
        from google.adk.errors.already_exists_error import AlreadyExistsError

        conn = await self._get_connection()
        session_id = session_id or str(uuid.uuid4())
        state = state or {}
        now = time.time()

        # Encrypt the state
        encrypted_state = await encrypt_session(state, self._backend, self._backend_id)

        # Check for duplicate session ID
        cursor = await conn.execute(
            "SELECT 1 FROM sessions WHERE app_name = ? AND user_id = ? AND id = ?",
            (app_name, user_id, session_id),
        )
        if await cursor.fetchone():
            msg = f"Session {session_id} already exists"
            raise AlreadyExistsError(msg)

        # Insert the session
        await conn.execute(
            """
            INSERT INTO sessions (app_name, user_id, id, state, create_time, update_time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (app_name, user_id, session_id, encrypted_state, now, now),
        )
        await conn.commit()

        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state,
            events=[],
            last_update_time=now,
        )

    async def _get_app_state(self, app_name: str) -> dict[str, Any]:
        """Get the app-level state for an application.

        Args:
            app_name: Application name.

        Returns:
            App-level state dictionary (empty if not found).
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "SELECT state FROM app_states WHERE app_name = ?",
            (app_name,),
        )
        row = await cursor.fetchone()
        if row is None:
            return {}
        return await decrypt_session(row[0], self._backend)

    async def _get_user_state(self, app_name: str, user_id: str) -> dict[str, Any]:
        """Get the user-level state for an application and user.

        Args:
            app_name: Application name.
            user_id: User identifier.

        Returns:
            User-level state dictionary (empty if not found).
        """
        conn = await self._get_connection()
        cursor = await conn.execute(
            "SELECT state FROM user_states WHERE app_name = ? AND user_id = ?",
            (app_name, user_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return {}
        return await decrypt_session(row[0], self._backend)

    async def _get_events(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        config: GetSessionConfig | None = None,
    ) -> list[Event]:
        """Get events for a session with optional filtering.

        Args:
            app_name: Application name.
            user_id: User identifier.
            session_id: Session ID.
            config: Optional filtering configuration.

        Returns:
            List of decrypted Event objects.
        """
        conn = await self._get_connection()

        # Build query based on config
        query = """
            SELECT event_data FROM events
            WHERE app_name = ? AND user_id = ? AND session_id = ?
        """
        params: list[Any] = [app_name, user_id, session_id]

        if config and config.after_timestamp is not None:
            query += " AND timestamp > ?"
            params.append(config.after_timestamp)

        query += " ORDER BY timestamp ASC"

        if config and config.num_recent_events is not None:
            # For recent events, we need to reverse the order and limit
            query = f"""
                SELECT event_data FROM (
                    SELECT event_data, timestamp FROM events
                    WHERE app_name = ? AND user_id = ? AND session_id = ?
                    {"AND timestamp > ?" if config.after_timestamp is not None else ""}
                    ORDER BY timestamp DESC
                    LIMIT ?
                ) ORDER BY timestamp ASC
            """
            params = [app_name, user_id, session_id]
            if config.after_timestamp is not None:
                params.append(config.after_timestamp)
            params.append(config.num_recent_events)

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        events = []
        for row in rows:
            event_json = await decrypt_json(row[0], self._backend)
            events.append(Event.model_validate_json(event_json))
        return events

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

        Returns:
            Session object with decrypted state and events, or None if not found.

        Raises:
            DecryptionError: If state or event decryption fails.
            SerializationError: If decrypted data is not valid JSON.

        Examples:
            Retrieve a session by ID:

            ```python
            session = await service.get_session(
                app_name="my-agent",
                user_id="user-123",
                session_id="abc-def-ghi",
            )
            if session is None:
                print("Session not found")
            ```
        """
        conn = await self._get_connection()

        # Get session
        cursor = await conn.execute(
            """
            SELECT state, update_time FROM sessions
            WHERE app_name = ? AND user_id = ? AND id = ?
            """,
            (app_name, user_id, session_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        # Decrypt session state
        session_state = await decrypt_session(row[0], self._backend)
        update_time = row[1]

        # Get and merge app state
        app_state = await self._get_app_state(app_name)

        # Get and merge user state
        user_state = await self._get_user_state(app_name, user_id)

        # Merge states: session state takes precedence
        merged_state = {**app_state, **user_state, **session_state}

        # Get events
        events = await self._get_events(app_name, user_id, session_id, config)

        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=merged_state,
            events=events,
            last_update_time=update_time,
        )

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

        Examples:
            List all sessions for a user:

            ```python
            response = await service.list_sessions(
                app_name="my-agent",
                user_id="user-123",
            )
            for session in response.sessions:
                print(session.id)
            ```
        """
        conn = await self._get_connection()

        if user_id is not None:
            cursor = await conn.execute(
                """
                SELECT id, user_id, state, update_time FROM sessions
                WHERE app_name = ? AND user_id = ?
                """,
                (app_name, user_id),
            )
        else:
            cursor = await conn.execute(
                """
                SELECT id, user_id, state, update_time FROM sessions
                WHERE app_name = ?
                """,
                (app_name,),
            )

        rows = await cursor.fetchall()
        sessions = []

        for row in rows:
            session_id, session_user_id, encrypted_state, update_time = row
            state = await decrypt_session(encrypted_state, self._backend)

            sessions.append(
                Session(
                    id=session_id,
                    app_name=app_name,
                    user_id=session_user_id,
                    state=state,
                    events=[],  # list_sessions doesn't include events
                    last_update_time=update_time,
                )
            )

        return ListSessionsResponse(sessions=sessions)

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

        Examples:
            Delete a session by ID:

            ```python
            await service.delete_session(
                app_name="my-agent",
                user_id="user-123",
                session_id="abc-def-ghi",
            )
            ```
        """
        conn = await self._get_connection()
        await conn.execute(
            "DELETE FROM sessions WHERE app_name = ? AND user_id = ? AND id = ?",
            (app_name, user_id, session_id),
        )
        await conn.commit()

    async def _upsert_app_state(
        self,
        app_name: str,
        state_delta: dict[str, Any],
    ) -> None:
        """Upsert app-level state with the given delta.

        Args:
            app_name: Application name.
            state_delta: State changes to merge (without app: prefix).
        """
        if not state_delta:
            return

        conn = await self._get_connection()
        now = time.time()

        # Get existing state
        existing = await self._get_app_state(app_name)

        # Merge delta
        merged = {**existing, **state_delta}

        # Encrypt and upsert
        encrypted = await encrypt_session(merged, self._backend, self._backend_id)
        await conn.execute(
            """
            INSERT INTO app_states (app_name, state, update_time)
            VALUES (?, ?, ?)
            ON CONFLICT(app_name) DO UPDATE SET state = ?, update_time = ?
            """,
            (app_name, encrypted, now, encrypted, now),
        )
        await conn.commit()

    async def _upsert_user_state(
        self,
        app_name: str,
        user_id: str,
        state_delta: dict[str, Any],
    ) -> None:
        """Upsert user-level state with the given delta.

        Args:
            app_name: Application name.
            user_id: User identifier.
            state_delta: State changes to merge (without user: prefix).
        """
        if not state_delta:
            return

        conn = await self._get_connection()
        now = time.time()

        # Get existing state
        existing = await self._get_user_state(app_name, user_id)

        # Merge delta
        merged = {**existing, **state_delta}

        # Encrypt and upsert
        encrypted = await encrypt_session(merged, self._backend, self._backend_id)
        await conn.execute(
            """
            INSERT INTO user_states (app_name, user_id, state, update_time)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(app_name, user_id) DO UPDATE SET state = ?, update_time = ?
            """,
            (app_name, user_id, encrypted, now, encrypted, now),
        )
        await conn.commit()

    async def _update_session_state_in_db(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        state_delta: dict[str, Any],
    ) -> None:
        """Update session state in database with the given delta.

        Args:
            app_name: Application name.
            user_id: User identifier.
            session_id: Session ID.
            state_delta: State changes to merge.
        """
        if not state_delta:
            return

        conn = await self._get_connection()
        now = time.time()

        # Get existing session state
        cursor = await conn.execute(
            "SELECT state FROM sessions WHERE app_name = ? AND user_id = ? AND id = ?",
            (app_name, user_id, session_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return

        existing = await decrypt_session(row[0], self._backend)

        # Merge delta
        merged = {**existing, **state_delta}

        # Encrypt and update
        encrypted = await encrypt_session(merged, self._backend, self._backend_id)
        await conn.execute(
            """
            UPDATE sessions SET state = ?, update_time = ?
            WHERE app_name = ? AND user_id = ? AND id = ?
            """,
            (encrypted, now, app_name, user_id, session_id),
        )
        await conn.commit()

    async def _extract_and_persist_state_delta(
        self,
        session: Session,
        event: Event,
    ) -> None:
        """Extract and persist state deltas from an event.

        Handles app:, user:, and session state. Discards temp: prefixed keys.

        Args:
            session: The session the event belongs to.
            event: The event containing state deltas.
        """
        if not event.actions or not event.actions.state_delta:
            return

        app_delta: dict[str, Any] = {}
        user_delta: dict[str, Any] = {}
        session_delta: dict[str, Any] = {}

        for key, value in event.actions.state_delta.items():
            if key.startswith("temp:"):
                # Discard temp keys
                continue
            elif key.startswith("app:"):
                # Strip prefix for app state
                app_delta[key[4:]] = value
            elif key.startswith("user:"):
                # Strip prefix for user state
                user_delta[key[5:]] = value
            else:
                # Session state
                session_delta[key] = value

        # Persist each type
        await self._upsert_app_state(session.app_name, app_delta)
        await self._upsert_user_state(session.app_name, session.user_id, user_delta)
        await self._update_session_state_in_db(
            session.app_name, session.user_id, session.id, session_delta
        )

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

        Examples:
            Append an event to a session:

            ```python
            from google.adk.events.event import Event

            event = Event(
                invocation_id="inv-001",
                author="agent",
            )
            stored_event = await service.append_event(session, event)
            ```
        """
        # Check for partial event - don't persist
        if event.partial:
            return event

        # Call base class methods for state trimming and updating
        event = self._trim_temp_delta_state(event)
        self._update_session_state(session, event)

        # Persist state deltas
        await self._extract_and_persist_state_delta(session, event)

        # Generate event ID if not set (ADK Event auto-generates, but keep as fallback)
        # Must happen before serialization so ID is included in encrypted payload
        if not event.id:  # pragma: no cover
            event.id = str(uuid.uuid4())

        # Encrypt and persist the event
        conn = await self._get_connection()
        event_json = event.model_dump_json(exclude_none=True)
        encrypted_event = await encrypt_json(
            event_json, self._backend, self._backend_id
        )

        await conn.execute(
            """
            INSERT INTO events (id, app_name, user_id, session_id, invocation_id,
                               timestamp, event_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                session.app_name,
                session.user_id,
                session.id,
                event.invocation_id,
                event.timestamp,
                encrypted_event,
            ),
        )
        await conn.commit()

        # Add event to in-memory session
        session.events.append(event)

        return event

    async def close(self) -> None:
        """Close the database connection.

        Should be called when the service is no longer needed.
        Automatically called when using the async context manager.
        """
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self) -> EncryptedSessionService:
        """Enter the async context manager.

        Returns:
            The service instance.
        """
        await self._init_db()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context manager and close the connection.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        await self.close()
