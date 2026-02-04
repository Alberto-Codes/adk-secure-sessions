"""Unit tests for EncryptedSessionService.

Tests cover:
- Session creation with encryption
- Session retrieval with decryption
- Event appending with state delta handling
- Session listing and deletion
- Async context manager lifecycle
- Edge cases (wrong key, corrupted data, empty state)
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest

from adk_secure_sessions import (
    BACKEND_FERNET,
    DecryptionError,
    EncryptedSessionService,
    FernetBackend,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def backend() -> FernetBackend:
    """Create a FernetBackend for testing."""
    return FernetBackend("test-passphrase-for-unit-tests")


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Create a temporary database path."""
    return str(tmp_path / "test_sessions.db")


@pytest.fixture
async def service(
    temp_db_path: str, backend: FernetBackend
) -> AsyncGenerator[EncryptedSessionService, None]:
    """Create an EncryptedSessionService for testing."""
    svc = EncryptedSessionService(
        db_path=temp_db_path,
        backend=backend,
        backend_id=BACKEND_FERNET,
    )
    await svc._init_db()
    yield svc
    await svc.close()


# =============================================================================
# Phase 3: User Story 2 - Create and Retrieve Encrypted Sessions
# =============================================================================


class TestCreateSession:
    """Tests for create_session method."""

    async def test_create_session_encrypts_state(
        self, service: EncryptedSessionService, temp_db_path: str
    ) -> None:
        """T009: create_session encrypts state in database."""
        state = {"secret": "sensitive-value", "api_key": "sk-12345"}

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        # Verify returned session has plaintext state
        assert session.state == state

        # Verify database contains encrypted data (not plaintext)
        import aiosqlite

        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute(
                "SELECT state FROM sessions WHERE id = ?", (session.id,)
            )
            row = await cursor.fetchone()
            assert row is not None
            encrypted_state = row[0]

            # Should be bytes, not plaintext JSON
            assert isinstance(encrypted_state, bytes)
            # Should not contain plaintext secrets
            assert b"sensitive-value" not in encrypted_state
            assert b"sk-12345" not in encrypted_state

    async def test_create_session_generates_uuid_when_not_provided(
        self, service: EncryptedSessionService
    ) -> None:
        """T010: create_session generates UUID when session_id not provided."""
        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        # Should have a valid UUID
        assert session.id is not None
        uuid.UUID(session.id)  # Raises if invalid

    async def test_create_session_raises_already_exists_error_for_duplicate(
        self, service: EncryptedSessionService
    ) -> None:
        """T011: create_session raises AlreadyExistsError for duplicate ID."""
        from google.adk.errors.already_exists_error import AlreadyExistsError

        session_id = "fixed-session-id"

        # Create first session
        await service.create_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session_id,
        )

        # Attempt to create duplicate
        with pytest.raises(AlreadyExistsError):
            await service.create_session(
                app_name="test-app",
                user_id="user-1",
                session_id=session_id,
            )


class TestGetSession:
    """Tests for get_session method."""

    async def test_get_session_returns_decrypted_state(
        self, service: EncryptedSessionService
    ) -> None:
        """T012: get_session returns decrypted state."""
        state = {"secret": "value", "nested": {"key": "data"}}

        created = await service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        retrieved = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=created.id,
        )

        assert retrieved is not None
        assert retrieved.state == state

    async def test_get_session_returns_none_for_nonexistent(
        self, service: EncryptedSessionService
    ) -> None:
        """T013: get_session returns None for non-existent session."""
        result = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id="nonexistent-id",
        )

        assert result is None

    async def test_get_session_filters_events_by_config(
        self, service: EncryptedSessionService
    ) -> None:
        """T014: get_session with GetSessionConfig filters events."""
        from google.adk.events.event import Event
        from google.adk.sessions.base_session_service import GetSessionConfig

        # Create session
        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        # Add multiple events with different timestamps
        base_time = time.time()
        for i in range(5):
            event = Event(
                id=f"event-{i}",
                author="user",
                invocation_id="inv-1",
                timestamp=base_time + i,
            )
            await service.append_event(session, event)

        # Get with num_recent_events
        config = GetSessionConfig(num_recent_events=2)
        result = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
            config=config,
        )

        assert result is not None
        assert len(result.events) == 2


# =============================================================================
# Phase 4: User Story 3 - Append Events with Encrypted Data
# =============================================================================


class TestAppendEvent:
    """Tests for append_event method."""

    async def test_append_event_encrypts_event_data(
        self, service: EncryptedSessionService, temp_db_path: str
    ) -> None:
        """T020: append_event encrypts event data in database."""
        from google.adk.events.event import Event

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="event-1",
            author="user",
            invocation_id="inv-1",
        )
        await service.append_event(session, event)

        # Check database contains encrypted event
        import aiosqlite

        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute(
                "SELECT event_data FROM events WHERE id = ?", ("event-1",)
            )
            row = await cursor.fetchone()
            assert row is not None
            encrypted_event = row[0]

            # Should be bytes, not plaintext
            assert isinstance(encrypted_event, bytes)
            assert b'"author"' not in encrypted_event

    async def test_append_event_extracts_app_state_delta(
        self, service: EncryptedSessionService
    ) -> None:
        """T021: append_event extracts and persists app state delta."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="event-1",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"app:shared_key": "shared_value"}),
        )
        await service.append_event(session, event)

        # Verify app state was saved
        app_state = await service._get_app_state("test-app")
        assert app_state.get("shared_key") == "shared_value"

    async def test_append_event_extracts_user_state_delta(
        self, service: EncryptedSessionService
    ) -> None:
        """T022: append_event extracts and persists user state delta."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="event-1",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"user:preference": "dark_mode"}),
        )
        await service.append_event(session, event)

        # Verify user state was saved
        user_state = await service._get_user_state("test-app", "user-1")
        assert user_state.get("preference") == "dark_mode"

    async def test_append_event_updates_session_state(
        self, service: EncryptedSessionService
    ) -> None:
        """T023: append_event updates session state."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
            state={"existing": "value"},
        )

        event = Event(
            id="event-1",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"new_key": "new_value"}),
        )
        await service.append_event(session, event)

        # Verify session state was updated in database
        retrieved = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert retrieved.state.get("new_key") == "new_value"
        assert retrieved.state.get("existing") == "value"

    async def test_append_event_skips_persistence_for_partial_events(
        self, service: EncryptedSessionService, temp_db_path: str
    ) -> None:
        """T024: append_event skips persistence for partial events."""
        from google.adk.events.event import Event

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="partial-event",
            author="user",
            invocation_id="inv-1",
            partial=True,
        )
        await service.append_event(session, event)

        # Check event was not persisted
        import aiosqlite

        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id = ?",
                (session.id,),
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 0

    async def test_append_event_discards_temp_prefixed_keys(
        self, service: EncryptedSessionService
    ) -> None:
        """T025: append_event discards temp: prefixed keys."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="event-1",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(
                state_delta={
                    "temp:scratch": "ignored",
                    "persistent": "saved",
                }
            ),
        )
        await service.append_event(session, event)

        # Verify temp key was not saved
        retrieved = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert "temp:scratch" not in retrieved.state
        assert "scratch" not in retrieved.state
        assert retrieved.state.get("persistent") == "saved"


# =============================================================================
# Phase 5: User Story 4 - List and Delete Sessions
# =============================================================================


class TestListSessions:
    """Tests for list_sessions method."""

    async def test_list_sessions_returns_all_sessions_for_app(
        self, service: EncryptedSessionService
    ) -> None:
        """T031: list_sessions returns all sessions for app."""
        # Create sessions for different users
        await service.create_session(app_name="test-app", user_id="user-1")
        await service.create_session(app_name="test-app", user_id="user-2")
        await service.create_session(app_name="other-app", user_id="user-1")

        result = await service.list_sessions(app_name="test-app")

        assert len(result.sessions) == 2

    async def test_list_sessions_filters_by_user_id(
        self, service: EncryptedSessionService
    ) -> None:
        """T032: list_sessions filters by user_id when provided."""
        await service.create_session(app_name="test-app", user_id="user-1")
        await service.create_session(app_name="test-app", user_id="user-1")
        await service.create_session(app_name="test-app", user_id="user-2")

        result = await service.list_sessions(app_name="test-app", user_id="user-1")

        assert len(result.sessions) == 2
        assert all(s.user_id == "user-1" for s in result.sessions)

    async def test_list_sessions_returns_decrypted_state(
        self, service: EncryptedSessionService
    ) -> None:
        """T033: list_sessions returns decrypted state."""
        state = {"secret": "value"}
        await service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        result = await service.list_sessions(app_name="test-app")

        assert len(result.sessions) == 1
        assert result.sessions[0].state == state


class TestDeleteSession:
    """Tests for delete_session method."""

    async def test_delete_session_removes_session_and_events(
        self, service: EncryptedSessionService, temp_db_path: str
    ) -> None:
        """T034: delete_session removes session and events."""
        from google.adk.events.event import Event

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        # Add events
        for i in range(3):
            event = Event(id=f"event-{i}", author="user", invocation_id="inv")
            await service.append_event(session, event)

        # Delete session
        await service.delete_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )

        # Verify session is gone
        result = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert result is None

        # Verify events are gone (cascade)
        import aiosqlite

        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id = ?",
                (session.id,),
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 0

    async def test_delete_session_is_idempotent(
        self, service: EncryptedSessionService
    ) -> None:
        """T035: delete_session is idempotent (no error if not exists)."""
        # Should not raise
        await service.delete_session(
            app_name="test-app",
            user_id="user-1",
            session_id="nonexistent",
        )


# =============================================================================
# Phase 6: User Story 5 - Async Context Manager
# =============================================================================


class TestAsyncContextManager:
    """Tests for async context manager methods."""

    async def test_aenter_returns_service_instance(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """T038: __aenter__ returns service instance."""
        service = EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
        )

        async with service as svc:
            assert svc is service

    async def test_aexit_calls_close(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """T039: __aexit__ calls close."""
        service = EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
        )

        async with service:
            assert service._connection is not None

        # After context, connection should be closed
        assert service._connection is None

    async def test_close_properly_closes_connection(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """T040: close properly closes database connection."""
        service = EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
        )
        await service._init_db()
        assert service._connection is not None

        await service.close()

        assert service._connection is None

    async def test_close_is_idempotent(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """T041: close is idempotent (no error if called twice)."""
        service = EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
        )
        await service._init_db()

        await service.close()
        await service.close()  # Should not raise


# =============================================================================
# Phase 8: Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Edge case tests for error handling."""

    async def test_wrong_encryption_key_raises_decryption_error(
        self, temp_db_path: str
    ) -> None:
        """T051: Wrong encryption key raises DecryptionError."""
        # Create session with one key
        backend1 = FernetBackend("key-one")
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend1,
            backend_id=BACKEND_FERNET,
        ) as service1:
            session = await service1.create_session(
                app_name="test-app",
                user_id="user-1",
                state={"secret": "data"},
            )
            session_id = session.id

        # Try to read with different key
        backend2 = FernetBackend("key-two")
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend2,
            backend_id=BACKEND_FERNET,
        ) as service2:
            with pytest.raises(DecryptionError):
                await service2.get_session(
                    app_name="test-app",
                    user_id="user-1",
                    session_id=session_id,
                )

    async def test_corrupted_data_raises_decryption_error(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """T052: Corrupted encrypted data raises DecryptionError."""
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
        ) as service:
            session = await service.create_session(
                app_name="test-app",
                user_id="user-1",
                state={"key": "value"},
            )

            # Corrupt the database directly
            import aiosqlite

            async with aiosqlite.connect(temp_db_path) as conn:
                await conn.execute(
                    "UPDATE sessions SET state = ? WHERE id = ?",
                    (b"corrupted-data-not-valid-envelope", session.id),
                )
                await conn.commit()

            with pytest.raises(DecryptionError):
                await service.get_session(
                    app_name="test-app",
                    user_id="user-1",
                    session_id=session.id,
                )

    async def test_empty_state_dictionary(
        self, service: EncryptedSessionService
    ) -> None:
        """T053: Empty state dictionary works correctly."""
        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
            state={},
        )

        retrieved = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )

        assert retrieved is not None
        assert retrieved.state == {}

    async def test_database_connection_errors_propagate(
        self, backend: FernetBackend
    ) -> None:
        """T054: Database connection errors propagate as aiosqlite exceptions."""
        # Use an invalid path that will fail
        service = EncryptedSessionService(
            db_path="/nonexistent/path/to/db.sqlite",
            backend=backend,
            backend_id=BACKEND_FERNET,
        )

        with pytest.raises(Exception):  # aiosqlite.OperationalError
            await service._init_db()

    async def test_large_state_objects(self, service: EncryptedSessionService) -> None:
        """T056: Large state objects are handled correctly."""
        # Create a reasonably large state (1MB of data)
        large_value = "x" * (1024 * 1024)
        state = {"large_key": large_value}

        session = await service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        retrieved = await service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )

        assert retrieved is not None
        assert retrieved.state["large_key"] == large_value
