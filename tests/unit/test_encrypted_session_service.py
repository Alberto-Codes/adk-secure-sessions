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

import pytest

from adk_secure_sessions import (
    BACKEND_FERNET,
    DecryptionError,
    EncryptedSessionService,
    FernetBackend,
)

pytestmark = pytest.mark.unit

# =============================================================================
# Phase 3: User Story 2 - Create and Retrieve Encrypted Sessions
# =============================================================================


class TestCreateSession:
    """Tests for create_session method."""

    async def test_create_session_encrypts_state(
        self, encrypted_service: EncryptedSessionService, db_path: str
    ) -> None:
        """T009: create_session encrypts state in database."""
        state = {"secret": "sensitive-value", "api_key": "sk-12345"}

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        # Verify returned session has plaintext state
        assert session.state == state

        # Verify database contains encrypted data (not plaintext)
        import aiosqlite

        async with aiosqlite.connect(db_path) as conn:
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
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T010: create_session generates UUID when session_id not provided."""
        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        # Should have a valid UUID
        assert session.id is not None
        uuid.UUID(session.id)  # Raises if invalid

    async def test_create_session_raises_already_exists_error_for_duplicate(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T011: create_session raises AlreadyExistsError for duplicate ID."""
        from google.adk.errors.already_exists_error import AlreadyExistsError

        session_id = "fixed-session-id"

        # Create first session
        await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session_id,
        )

        # Attempt to create duplicate
        with pytest.raises(AlreadyExistsError):
            await encrypted_service.create_session(
                app_name="test-app",
                user_id="user-1",
                session_id=session_id,
            )


class TestGetSession:
    """Tests for get_session method."""

    async def test_get_session_returns_decrypted_state(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T012: get_session returns decrypted state."""
        state = {"secret": "value", "nested": {"key": "data"}}

        created = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=created.id,
        )

        assert retrieved is not None
        assert retrieved.state == state

    async def test_get_session_returns_none_for_nonexistent(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T013: get_session returns None for non-existent session."""
        result = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id="nonexistent-id",
        )

        assert result is None

    async def test_get_session_filters_events_by_config(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T014: get_session with GetSessionConfig filters events."""
        from google.adk.events.event import Event
        from google.adk.sessions.base_session_service import GetSessionConfig

        # Create session
        session = await encrypted_service.create_session(
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
            await encrypted_service.append_event(session, event)

        # Get with num_recent_events
        config = GetSessionConfig(num_recent_events=2)
        result = await encrypted_service.get_session(
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
        self, encrypted_service: EncryptedSessionService, db_path: str
    ) -> None:
        """T020: append_event encrypts event data in database."""
        from google.adk.events.event import Event

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="event-1",
            author="user",
            invocation_id="inv-1",
        )
        await encrypted_service.append_event(session, event)

        # Check database contains encrypted event
        import aiosqlite

        async with aiosqlite.connect(db_path) as conn:
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
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T021: append_event extracts and persists app state delta."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="event-1",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"app:shared_key": "shared_value"}),
        )
        await encrypted_service.append_event(session, event)

        # Verify app state was saved
        app_state = await encrypted_service._get_app_state("test-app")
        assert app_state.get("shared_key") == "shared_value"

    async def test_append_event_extracts_user_state_delta(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T022: append_event extracts and persists user state delta."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="event-1",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"user:preference": "dark_mode"}),
        )
        await encrypted_service.append_event(session, event)

        # Verify user state was saved
        user_state = await encrypted_service._get_user_state("test-app", "user-1")
        assert user_state.get("preference") == "dark_mode"

    async def test_append_event_updates_session_state(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T023: append_event updates session state."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await encrypted_service.create_session(
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
        await encrypted_service.append_event(session, event)

        # Verify session state was updated in database
        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert retrieved.state.get("new_key") == "new_value"
        assert retrieved.state.get("existing") == "value"

    async def test_append_event_skips_persistence_for_partial_events(
        self, encrypted_service: EncryptedSessionService, db_path: str
    ) -> None:
        """T024: append_event skips persistence for partial events."""
        from google.adk.events.event import Event

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        event = Event(
            id="partial-event",
            author="user",
            invocation_id="inv-1",
            partial=True,
        )
        await encrypted_service.append_event(session, event)

        # Check event was not persisted
        import aiosqlite

        async with aiosqlite.connect(db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id = ?",
                (session.id,),
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 0

    async def test_append_event_discards_temp_prefixed_keys(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T025: append_event discards temp: prefixed keys."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await encrypted_service.create_session(
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
        await encrypted_service.append_event(session, event)

        # Verify temp key was not saved
        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert "temp:scratch" not in retrieved.state
        assert "scratch" not in retrieved.state
        assert retrieved.state.get("persistent") == "saved"

    async def test_append_event_discards_only_temp_keys(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Test event with only temp: keys results in no state changes."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state={"original": "value"},
        )

        # Event with ONLY temp keys
        event = Event(
            id="event-temp-only",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(
                state_delta={
                    "temp:key1": "ignored1",
                    "temp:key2": "ignored2",
                    "temp:key3": "ignored3",
                }
            ),
        )
        await encrypted_service.append_event(session, event)

        # Verify no temp keys were saved
        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert retrieved.state == {"original": "value"}
        assert "temp:key1" not in retrieved.state
        assert "key1" not in retrieved.state


# =============================================================================
# Phase 5: User Story 4 - List and Delete Sessions
# =============================================================================


class TestListSessions:
    """Tests for list_sessions method."""

    async def test_list_sessions_returns_all_sessions_for_app(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T031: list_sessions returns all sessions for app."""
        # Create sessions for different users
        await encrypted_service.create_session(app_name="test-app", user_id="user-1")
        await encrypted_service.create_session(app_name="test-app", user_id="user-2")
        await encrypted_service.create_session(app_name="other-app", user_id="user-1")

        result = await encrypted_service.list_sessions(app_name="test-app")

        assert len(result.sessions) == 2

    async def test_list_sessions_filters_by_user_id(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T032: list_sessions filters by user_id when provided."""
        await encrypted_service.create_session(app_name="test-app", user_id="user-1")
        await encrypted_service.create_session(app_name="test-app", user_id="user-1")
        await encrypted_service.create_session(app_name="test-app", user_id="user-2")

        result = await encrypted_service.list_sessions(
            app_name="test-app", user_id="user-1"
        )

        assert len(result.sessions) == 2
        assert all(s.user_id == "user-1" for s in result.sessions)

    async def test_list_sessions_returns_decrypted_state(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T033: list_sessions returns decrypted state."""
        state = {"secret": "value"}
        await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        result = await encrypted_service.list_sessions(app_name="test-app")

        assert len(result.sessions) == 1
        assert result.sessions[0].state == state


class TestDeleteSession:
    """Tests for delete_session method."""

    async def test_delete_session_removes_session_and_events(
        self, encrypted_service: EncryptedSessionService, db_path: str
    ) -> None:
        """T034: delete_session removes session and events."""
        from google.adk.events.event import Event

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        # Add events
        for i in range(3):
            event = Event(id=f"event-{i}", author="user", invocation_id="inv")
            await encrypted_service.append_event(session, event)

        # Delete session
        await encrypted_service.delete_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )

        # Verify session is gone
        result = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert result is None

        # Verify events are gone (cascade)
        import aiosqlite

        async with aiosqlite.connect(db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM events WHERE session_id = ?",
                (session.id,),
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 0

    async def test_delete_session_is_idempotent(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T035: delete_session is idempotent (no error if not exists)."""
        # Should not raise
        await encrypted_service.delete_session(
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
        self, db_path: str, fernet_backend: FernetBackend
    ) -> None:
        """T038: __aenter__ returns service instance."""
        service = EncryptedSessionService(
            db_path=db_path,
            backend=fernet_backend,
            backend_id=BACKEND_FERNET,
        )

        async with service as svc:
            assert svc is service

    async def test_aexit_calls_close(
        self, db_path: str, fernet_backend: FernetBackend
    ) -> None:
        """T039: __aexit__ calls close."""
        service = EncryptedSessionService(
            db_path=db_path,
            backend=fernet_backend,
            backend_id=BACKEND_FERNET,
        )

        async with service:
            assert service._connection is not None

        # After context, connection should be closed
        assert service._connection is None

    async def test_close_properly_closes_connection(
        self, db_path: str, fernet_backend: FernetBackend
    ) -> None:
        """T040: close properly closes database connection."""
        service = EncryptedSessionService(
            db_path=db_path,
            backend=fernet_backend,
            backend_id=BACKEND_FERNET,
        )
        await service._init_db()
        assert service._connection is not None

        await service.close()

        assert service._connection is None

    async def test_close_is_idempotent(
        self, db_path: str, fernet_backend: FernetBackend
    ) -> None:
        """T041: close is idempotent (no error if called twice)."""
        service = EncryptedSessionService(
            db_path=db_path,
            backend=fernet_backend,
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
        self, db_path: str
    ) -> None:
        """T051: Wrong encryption key raises DecryptionError."""
        # Create session with one key
        backend1 = FernetBackend("key-one")
        async with EncryptedSessionService(
            db_path=db_path,
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
            db_path=db_path,
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
        self, db_path: str, fernet_backend: FernetBackend
    ) -> None:
        """T052: Corrupted encrypted data raises DecryptionError."""
        async with EncryptedSessionService(
            db_path=db_path,
            backend=fernet_backend,
            backend_id=BACKEND_FERNET,
        ) as service:
            session = await service.create_session(
                app_name="test-app",
                user_id="user-1",
                state={"key": "value"},
            )

            # Corrupt the database directly
            import aiosqlite

            async with aiosqlite.connect(db_path) as conn:
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
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T053: Empty state dictionary works correctly."""
        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state={},
        )

        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )

        assert retrieved is not None
        assert retrieved.state == {}

    async def test_database_connection_errors_propagate(
        self, fernet_backend: FernetBackend
    ) -> None:
        """T054: Database connection errors propagate as aiosqlite exceptions."""
        # Use an invalid path that will fail
        service = EncryptedSessionService(
            db_path="/nonexistent/path/to/db.sqlite",
            backend=fernet_backend,
            backend_id=BACKEND_FERNET,
        )

        with pytest.raises(Exception):  # aiosqlite.OperationalError
            await service._init_db()

    async def test_large_state_objects(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T056: Large state objects are handled correctly."""
        # Create a reasonably large state (1MB of data)
        large_value = "x" * (1024 * 1024)
        state = {"large_key": large_value}

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=state,
        )

        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )

        assert retrieved is not None
        assert retrieved.state["large_key"] == large_value


# =============================================================================
# Additional Coverage Tests
# =============================================================================


class TestGetSessionConfigFiltering:
    """Tests for GetSessionConfig event filtering options."""

    async def test_get_session_filters_by_after_timestamp(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Test after_timestamp config filters events correctly."""
        from google.adk.events.event import Event
        from google.adk.sessions.base_session_service import GetSessionConfig

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        # Add events with specific timestamps
        base_time = 1000.0
        for i in range(5):
            event = Event(
                id=f"event-{i}",
                author="user",
                invocation_id="inv-1",
                timestamp=base_time + i,
            )
            await encrypted_service.append_event(session, event)

        # Get events after timestamp 1002 (should get events 3 and 4)
        config = GetSessionConfig(after_timestamp=base_time + 2)
        result = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
            config=config,
        )

        assert result is not None
        assert len(result.events) == 2
        assert result.events[0].id == "event-3"
        assert result.events[1].id == "event-4"

    async def test_get_session_combines_after_timestamp_and_num_recent(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Test after_timestamp combined with num_recent_events."""
        from google.adk.events.event import Event
        from google.adk.sessions.base_session_service import GetSessionConfig

        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        # Add 10 events
        base_time = 1000.0
        for i in range(10):
            event = Event(
                id=f"event-{i}",
                author="user",
                invocation_id="inv-1",
                timestamp=base_time + i,
            )
            await encrypted_service.append_event(session, event)

        # Get last 2 events after timestamp 1005
        # Events after 1005: 6, 7, 8, 9 (4 events)
        # Last 2 of those: 8, 9
        config = GetSessionConfig(after_timestamp=base_time + 5, num_recent_events=2)
        result = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
            config=config,
        )

        assert result is not None
        assert len(result.events) == 2
        assert result.events[0].id == "event-8"
        assert result.events[1].id == "event-9"


class TestStateDeltaEdgeCases:
    """Tests for state delta handling edge cases."""

    async def test_update_session_state_on_nonexistent_session(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Test _update_session_state_in_db returns early for non-existent session."""
        # This should not raise - just return early
        await encrypted_service._update_session_state_in_db(
            app_name="test-app",
            user_id="user-1",
            session_id="nonexistent-session",
            state_delta={"key": "value"},
        )

        # Verify no session was created
        result = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id="nonexistent-session",
        )
        assert result is None

    async def test_event_id_is_auto_generated_by_adk(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Verify ADK Event model auto-generates IDs.

        Note: The Event model from google-adk auto-generates UUIDs,
        so the fallback ID generation branch in
        EncryptedSessionService.append_event is unreachable with the
        current ADK version. This test documents that behavior.
        """
        from google.adk.events.event import Event

        # Event auto-generates ID even without providing one
        event = Event(
            author="user",
            invocation_id="inv-1",
        )

        # ADK Event always has an ID
        assert event.id is not None
        uuid.UUID(event.id)  # Should be valid UUID

    async def test_get_connection_initializes_db_lazily(
        self, db_path: str, fernet_backend: FernetBackend
    ) -> None:
        """Test _get_connection initializes database when not yet connected."""
        service = EncryptedSessionService(
            db_path=db_path,
            backend=fernet_backend,
            backend_id=BACKEND_FERNET,
        )

        # Connection should be None initially
        assert service._connection is None

        # Call _get_connection directly (not through context manager)
        conn = await service._get_connection()

        # Should have initialized the connection
        assert conn is not None
        assert service._connection is not None

        await service.close()
