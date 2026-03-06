"""Integration tests for EncryptedSessionService with ADK.

Tests verify:
- BaseSessionService interface conformance
- Round-trip session workflows
- Database encryption verification
- Protocol conformance with mock backends
"""

from __future__ import annotations

import sqlite3

import pytest
from cryptography.fernet import Fernet

from adk_secure_sessions import (
    DecryptionError,
    EncryptedSessionService,
    FernetBackend,
)
from adk_secure_sessions.protocols import EncryptionBackend

# Pre-generated Fernet keys — skip PBKDF2 in wrong-key tests that validate
# decryption isolation, not passphrase derivation.
_KEY_A = Fernet.generate_key()
_KEY_B = Fernet.generate_key()

pytestmark = pytest.mark.integration

# =============================================================================
# Phase 7: User Story 1 - Drop-in Replacement Integration
# =============================================================================


class TestBaseSessionServiceInterface:
    """T045: Tests for BaseSessionService interface conformance."""

    async def test_inherits_from_base_session_service(self) -> None:
        """Verify EncryptedSessionService inherits from BaseSessionService."""
        from google.adk.sessions.base_session_service import BaseSessionService

        assert issubclass(EncryptedSessionService, BaseSessionService)

    async def test_has_required_abstract_methods(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify all required abstract methods are implemented."""
        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # All these methods should exist and be callable
            assert callable(service.create_session)
            assert callable(service.get_session)
            assert callable(service.list_sessions)
            assert callable(service.delete_session)
            assert callable(service.append_event)

    async def test_returns_correct_types(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify methods return ADK-compatible types."""
        from google.adk.sessions.base_session_service import ListSessionsResponse
        from google.adk.sessions.session import Session

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # create_session returns Session
            session = await service.create_session(app_name="test", user_id="user")
            assert isinstance(session, Session)

            # get_session returns Session or None
            result = await service.get_session(
                app_name="test", user_id="user", session_id=session.id
            )
            assert isinstance(result, Session)

            # list_sessions returns ListSessionsResponse
            list_result = await service.list_sessions(app_name="test")
            assert isinstance(list_result, ListSessionsResponse)


class TestRoundTripWorkflow:
    """T046: Tests for complete session workflow."""

    async def test_full_session_lifecycle(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Test create -> append events -> get -> delete workflow."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # 1. Create session with initial state
            session = await service.create_session(
                app_name="my-agent",
                user_id="user-123",
                state={"conversation_id": "conv-1", "preferences": {}},
            )
            session_id = session.id

            # 2. Append multiple events (simulating agent conversation)
            events_data: list[dict[str, str | dict[str, str]]] = [
                {"author": "user", "content": "Hello"},
                {"author": "agent", "content": "Hi there!"},
                {"author": "user", "content": "What's the weather?"},
                {
                    "author": "agent",
                    "content": "It's sunny!",
                    "state_delta": {"last_query": "weather"},
                },
            ]

            for i, data in enumerate(events_data):
                state_delta_raw = data.get("state_delta")
                state_delta: dict[str, object] = (
                    dict(state_delta_raw) if isinstance(state_delta_raw, dict) else {}
                )
                actions = EventActions(state_delta=state_delta)

                author = data["author"]
                event = Event(
                    id=f"event-{i}",
                    author=str(author),
                    invocation_id=f"inv-{i // 2}",
                    actions=actions,
                )
                await service.append_event(session, event)

            # 3. Get session and verify all data
            retrieved = await service.get_session(
                app_name="my-agent",
                user_id="user-123",
                session_id=session_id,
            )

            assert retrieved is not None
            assert retrieved.id == session_id
            assert len(retrieved.events) == 4
            assert retrieved.state.get("last_query") == "weather"
            assert retrieved.state.get("conversation_id") == "conv-1"

            # 4. List sessions
            list_result = await service.list_sessions(app_name="my-agent")
            assert len(list_result.sessions) == 1
            assert list_result.sessions[0].id == session_id

            # 5. Delete session
            await service.delete_session(
                app_name="my-agent",
                user_id="user-123",
                session_id=session_id,
            )

            # 6. Verify deletion
            deleted = await service.get_session(
                app_name="my-agent",
                user_id="user-123",
                session_id=session_id,
            )
            assert deleted is None


class TestDatabaseEncryption:
    """T047: Tests verifying database contains only encrypted data."""

    async def test_state_is_encrypted_in_database(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify session state is encrypted in raw database."""
        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # Create session with sensitive data
            await service.create_session(
                app_name="secure-app",
                user_id="user-secret",
                state={
                    "api_key": "sk-super-secret-key-12345",
                    "ssn": "123-45-6789",
                    "password": "hunter2",
                },
            )

        # Read raw database content (TEXT column, base64-encoded envelope)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT state FROM sessions")
        row = cursor.fetchone()
        conn.close()
        assert row is not None, "Expected session row to exist"
        raw_state = row[0]

        # State is now TEXT (base64-encoded encrypted envelope)
        assert isinstance(raw_state, str)

        # Verify sensitive data is NOT in plaintext
        assert "sk-super-secret-key-12345" not in raw_state
        assert "123-45-6789" not in raw_state
        assert "hunter2" not in raw_state
        assert "api_key" not in raw_state

    async def test_events_are_encrypted_in_database(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify event data is encrypted in raw database."""
        from google.adk.events.event import Event

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            session = await service.create_session(
                app_name="secure-app",
                user_id="user-1",
            )

            event = Event(
                id="secret-event",
                author="agent",
                invocation_id="inv-1",
            )
            await service.append_event(session, event)

        # Read raw database content
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT event_data FROM events")
        row = cursor.fetchone()
        conn.close()
        assert row is not None, "Expected event row to exist"
        raw_event = row[0]

        # Event data is now TEXT (base64-encoded encrypted envelope)
        assert isinstance(raw_event, str)

        # Verify event content is NOT in plaintext
        assert '"author"' not in raw_event
        assert '"invocation_id"' not in raw_event

    async def test_app_state_is_encrypted_in_database(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify app-level state is encrypted in raw database."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            session = await service.create_session(
                app_name="secure-app",
                user_id="user-1",
            )

            event = Event(
                id="event-1",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(
                    state_delta={"app:global_secret": "top-secret-value"}
                ),
            )
            await service.append_event(session, event)

        # Read raw database content
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT state FROM app_states")
        row = cursor.fetchone()
        conn.close()
        assert row is not None, "Expected app_states row to exist"
        raw_state = row[0]

        # Verify sensitive data is NOT in plaintext
        assert isinstance(raw_state, str)
        assert "top-secret-value" not in raw_state
        assert "global_secret" not in raw_state


class TestProtocolConformance:
    """T048: Tests with mock EncryptionBackend to verify protocol."""

    async def test_backend_protocol_is_runtime_checkable(self) -> None:
        """Verify EncryptionBackend protocol is runtime checkable."""
        # FernetBackend should pass isinstance check
        backend = FernetBackend(_KEY_A)
        assert isinstance(backend, EncryptionBackend)

        # Non-conforming object should fail
        class NotABackend:
            pass

        assert not isinstance(NotABackend(), EncryptionBackend)


# =============================================================================
# Additional Integration Tests for Issue #7 Completeness
# =============================================================================


class TestListSessionsIntegration:
    """Integration tests for list_sessions functionality."""

    async def test_list_sessions_with_multiple_users(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify list_sessions returns all sessions across users."""
        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # Create sessions for multiple users
            await service.create_session(
                app_name="my-agent",
                user_id="alice",
                state={"name": "Alice"},
            )
            await service.create_session(
                app_name="my-agent",
                user_id="bob",
                state={"name": "Bob"},
            )
            await service.create_session(
                app_name="other-agent",
                user_id="alice",
                state={"name": "Other Alice"},
            )

            # List all sessions for my-agent
            result = await service.list_sessions(app_name="my-agent")
            assert len(result.sessions) == 2

            # Verify state is decrypted correctly
            names = {s.state.get("name") for s in result.sessions}
            assert names == {"Alice", "Bob"}

    async def test_list_sessions_filters_by_user(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify list_sessions correctly filters by user_id."""
        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # Create multiple sessions for same user
            for i in range(3):
                await service.create_session(
                    app_name="my-agent",
                    user_id="alice",
                    state={"session_num": i},
                )

            await service.create_session(
                app_name="my-agent",
                user_id="bob",
                state={"session_num": 99},
            )

            # List only Alice's sessions
            result = await service.list_sessions(
                app_name="my-agent",
                user_id="alice",
            )
            assert len(result.sessions) == 3
            assert all(s.user_id == "alice" for s in result.sessions)


class TestDeleteSessionIntegration:
    """Integration tests for delete_session functionality."""

    async def test_delete_session_cascades_to_events(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify delete_session removes associated events."""
        from google.adk.events.event import Event

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            session = await service.create_session(
                app_name="my-agent",
                user_id="user-1",
            )

            # Add events
            for i in range(5):
                event = Event(
                    id=f"evt-{i}",
                    author="agent",
                    invocation_id=f"inv-{i}",
                )
                await service.append_event(session, event)

            # Delete session
            await service.delete_session(
                app_name="my-agent",
                user_id="user-1",
                session_id=session.id,
            )

        # Verify events are gone from database
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM events")
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        assert row[0] == 0

    async def test_delete_nonexistent_session_is_safe(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify deleting a non-existent session doesn't raise."""
        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # Should not raise
            await service.delete_session(
                app_name="my-agent",
                user_id="user-1",
                session_id="does-not-exist",
            )


class TestSessionRecreateAfterDelete:
    """Cross-cutting: recreating a session after deletion returns fresh data."""

    async def test_recreate_session_after_delete_has_no_stale_events(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify a new session shares no events with a deleted session."""
        from google.adk.events.event import Event

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            # Create session and add events
            session = await service.create_session(
                app_name="my-agent",
                user_id="user-1",
                state={"counter": 1},
            )
            original_id = session.id

            event = Event(
                id="evt-old",
                author="agent",
                invocation_id="inv-1",
            )
            await service.append_event(session, event)

            # Delete the session
            await service.delete_session(
                app_name="my-agent",
                user_id="user-1",
                session_id=original_id,
            )

            # Recreate with fresh state
            new_session = await service.create_session(
                app_name="my-agent",
                user_id="user-1",
                state={"counter": 99},
            )

            # Retrieve and verify fresh data
            retrieved = await service.get_session(
                app_name="my-agent",
                user_id="user-1",
                session_id=new_session.id,
            )
            assert retrieved is not None
            assert retrieved.state["counter"] == 99
            assert len(retrieved.events) == 0

            # Original session should be gone
            gone = await service.get_session(
                app_name="my-agent",
                user_id="user-1",
                session_id=original_id,
            )
            assert gone is None


class TestWrongKeyIntegration:
    """Integration tests for wrong encryption key scenarios."""

    async def test_wrong_key_raises_decryption_error_on_get(self, db_url: str) -> None:
        """Verify wrong key raises DecryptionError when retrieving session."""
        # Create session with key1
        backend1 = FernetBackend(_KEY_A)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend1,
        ) as service:
            session = await service.create_session(
                app_name="my-agent",
                user_id="user-1",
                state={"secret": "classified-data"},
            )
            session_id = session.id

        # Try to read with key2
        backend2 = FernetBackend(_KEY_B)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend2,
        ) as service:
            with pytest.raises(DecryptionError):
                await service.get_session(
                    app_name="my-agent",
                    user_id="user-1",
                    session_id=session_id,
                )

    async def test_wrong_key_raises_decryption_error_on_list(self, db_url: str) -> None:
        """Verify wrong key raises DecryptionError when listing sessions."""
        # Create session with key1
        backend1 = FernetBackend(_KEY_A)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend1,
        ) as service:
            await service.create_session(
                app_name="my-agent",
                user_id="user-1",
                state={"secret": "classified-data"},
            )

        # Try to list with key2
        backend2 = FernetBackend(_KEY_B)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend2,
        ) as service:
            with pytest.raises(DecryptionError):
                await service.list_sessions(app_name="my-agent")


# =============================================================================
# Coverage Expansion Tests (TEA Automate — P1)
# =============================================================================


class TestUserStateEncryption:
    """[P1] Verify user-level state is encrypted in raw database."""

    async def test_user_state_is_encrypted_in_database(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Verify user_states table contains only encrypted data."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            session = await service.create_session(
                app_name="secure-app",
                user_id="user-1",
            )

            event = Event(
                id="event-1",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(
                    state_delta={"user:personal_secret": "my-ssn-123-45-6789"}
                ),
            )
            await service.append_event(session, event)

        # Read raw database content
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT state FROM user_states")
        row = cursor.fetchone()
        conn.close()
        assert row is not None, "Expected user_states row to exist"
        raw_state = row[0]

        # Verify sensitive data is NOT in plaintext
        assert isinstance(raw_state, str)
        assert "my-ssn-123-45-6789" not in raw_state
        assert "personal_secret" not in raw_state


class TestStateMergePrecedence:
    """[P1] Verify state merge uses ADK's merge convention (prefixed keys)."""

    async def test_session_state_preserved_alongside_app_and_user(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Session, app, and user state coexist with proper prefixes."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            session = await service.create_session(
                app_name="test-app",
                user_id="user-1",
                state={"theme": "session-dark"},
            )

            # Set app-level and user-level state
            event = Event(
                id="event-1",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(
                    state_delta={
                        "app:theme": "app-light",
                        "user:theme": "user-blue",
                    }
                ),
            )
            await service.append_event(session, event)

            # Retrieve session — ADK merges with prefixes
            retrieved = await service.get_session(
                app_name="test-app",
                user_id="user-1",
                session_id=session.id,
            )

            assert retrieved is not None
            # Session state key (no prefix)
            assert retrieved.state["theme"] == "session-dark"
            # App and user state preserved with prefixes
            assert retrieved.state["app:theme"] == "app-light"
            assert retrieved.state["user:theme"] == "user-blue"

    async def test_app_and_user_state_available_with_prefixes(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """App and user state accessible via prefixed keys in merged state."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        ) as service:
            session = await service.create_session(
                app_name="test-app",
                user_id="user-1",
                state={"unrelated": "data"},
            )

            event = Event(
                id="event-1",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(
                    state_delta={
                        "app:color": "app-red",
                        "user:color": "user-green",
                    }
                ),
            )
            await service.append_event(session, event)

            retrieved = await service.get_session(
                app_name="test-app",
                user_id="user-1",
                session_id=session.id,
            )

            assert retrieved is not None
            # ADK stores app/user state with prefixed keys in merged result
            assert retrieved.state["app:color"] == "app-red"
            assert retrieved.state["user:color"] == "user-green"


class TestWrongKeyOnStateTables:
    """[P1] Wrong key raises DecryptionError on app/user state paths."""

    async def test_wrong_key_raises_on_get_with_app_state(self, db_url: str) -> None:
        """Wrong key raises DecryptionError when app_states has data."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        # Create session and app state with key1
        backend1 = FernetBackend(_KEY_A)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend1,
        ) as service:
            session = await service.create_session(
                app_name="test-app",
                user_id="user-1",
                state={"session": "data"},
            )
            session_id = session.id

            # Add app-level state
            event = Event(
                id="evt-1",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(state_delta={"app:secret": "classified"}),
            )
            await service.append_event(session, event)

        # Try to read with key2 — should fail on app_state decryption
        backend2 = FernetBackend(_KEY_B)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend2,
        ) as service:
            with pytest.raises(DecryptionError):
                await service.get_session(
                    app_name="test-app",
                    user_id="user-1",
                    session_id=session_id,
                )

    async def test_wrong_key_raises_on_get_with_user_state(self, db_url: str) -> None:
        """Wrong key raises DecryptionError when user_states has data."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        # Create session and user state with key1
        backend1 = FernetBackend(_KEY_A)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend1,
        ) as service:
            session = await service.create_session(
                app_name="test-app",
                user_id="user-1",
                state={"session": "data"},
            )
            session_id = session.id

            # Add user-level state
            event = Event(
                id="evt-1",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(state_delta={"user:secret": "classified"}),
            )
            await service.append_event(session, event)

        # Try to read with key2 — should fail on user_state decryption
        backend2 = FernetBackend(_KEY_B)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend2,
        ) as service:
            with pytest.raises(DecryptionError):
                await service.get_session(
                    app_name="test-app",
                    user_id="user-1",
                    session_id=session_id,
                )
