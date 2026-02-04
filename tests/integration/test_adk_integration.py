"""Integration tests for EncryptedSessionService with ADK.

Tests verify:
- BaseSessionService interface conformance
- Round-trip session workflows
- Database encryption verification
- Protocol conformance with mock backends
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from adk_secure_sessions import (
    BACKEND_FERNET,
    EncryptedSessionService,
    FernetBackend,
)
from adk_secure_sessions.protocols import EncryptionBackend

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def backend() -> FernetBackend:
    """Create a FernetBackend for testing."""
    return FernetBackend("integration-test-passphrase")


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """Create a temporary database path."""
    return str(tmp_path / "integration_sessions.db")


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
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify all required abstract methods are implemented."""
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
        ) as service:
            # All these methods should exist and be callable
            assert callable(service.create_session)
            assert callable(service.get_session)
            assert callable(service.list_sessions)
            assert callable(service.delete_session)
            assert callable(service.append_event)

    async def test_returns_correct_types(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify methods return ADK-compatible types."""
        from google.adk.sessions.base_session_service import ListSessionsResponse
        from google.adk.sessions.session import Session

        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Test create -> append events -> get -> delete workflow."""
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify session state is encrypted in raw database."""
        import aiosqlite

        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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

        # Read raw database content
        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute("SELECT state FROM sessions")
            row = await cursor.fetchone()
            assert row is not None, "Expected session row to exist"
            raw_state = row[0]

            # Verify it's bytes (encrypted envelope)
            assert isinstance(raw_state, bytes)

            # Verify sensitive data is NOT in plaintext
            raw_str = raw_state.decode("latin-1")  # Safe for binary
            assert "sk-super-secret-key-12345" not in raw_str
            assert "123-45-6789" not in raw_str
            assert "hunter2" not in raw_str
            assert "api_key" not in raw_str

    async def test_events_are_encrypted_in_database(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify event data is encrypted in raw database."""
        import aiosqlite
        from google.adk.events.event import Event

        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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
        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute("SELECT event_data FROM events")
            row = await cursor.fetchone()
            assert row is not None, "Expected event row to exist"
            raw_event = row[0]

            # Verify it's bytes (encrypted envelope)
            assert isinstance(raw_event, bytes)

            # Verify event content is NOT in plaintext
            raw_str = raw_event.decode("latin-1")
            assert '"author"' not in raw_str
            assert '"invocation_id"' not in raw_str

    async def test_app_state_is_encrypted_in_database(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify app-level state is encrypted in raw database."""
        import aiosqlite
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions

        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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
        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute("SELECT state FROM app_states")
            row = await cursor.fetchone()
            assert row is not None, "Expected app_states row to exist"
            raw_state = row[0]

            # Verify sensitive data is NOT in plaintext
            raw_str = raw_state.decode("latin-1")
            assert "top-secret-value" not in raw_str
            assert "global_secret" not in raw_str


class TestProtocolConformance:
    """T048: Tests with mock EncryptionBackend to verify protocol."""

    async def test_works_with_custom_backend(self, temp_db_path: str) -> None:
        """Verify service works with any EncryptionBackend-conformant object."""

        class MockBackend:
            """Simple mock backend that does XOR 'encryption'."""

            async def encrypt(self, plaintext: bytes) -> bytes:
                """XOR with 0x42 (not real encryption, just for testing)."""
                return bytes(b ^ 0x42 for b in plaintext)

            async def decrypt(self, ciphertext: bytes) -> bytes:
                """XOR with 0x42 to reverse."""
                return bytes(b ^ 0x42 for b in ciphertext)

        # Verify mock conforms to protocol at runtime
        assert isinstance(MockBackend(), EncryptionBackend)

        # Use mock backend with service
        mock_backend = MockBackend()
        mock_backend_id = 0xFF  # Hypothetical backend ID

        # Note: This will fail on envelope parsing since our backend ID
        # isn't registered, but we can test the protocol conformance works
        # by using a registered backend ID
        from adk_secure_sessions.serialization import BACKEND_REGISTRY

        # Temporarily register our mock backend
        BACKEND_REGISTRY[mock_backend_id] = "MockXOR"

        try:
            async with EncryptedSessionService(
                db_path=temp_db_path,
                backend=mock_backend,
                backend_id=mock_backend_id,
            ) as service:
                # Create session
                session = await service.create_session(
                    app_name="test",
                    user_id="user",
                    state={"key": "value"},
                )

                # Retrieve session
                retrieved = await service.get_session(
                    app_name="test",
                    user_id="user",
                    session_id=session.id,
                )

                assert retrieved is not None
                assert retrieved.state == {"key": "value"}
        finally:
            # Cleanup registry
            del BACKEND_REGISTRY[mock_backend_id]

    async def test_backend_protocol_is_runtime_checkable(self) -> None:
        """Verify EncryptionBackend protocol is runtime checkable."""
        # FernetBackend should pass isinstance check
        backend = FernetBackend("test")
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
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify list_sessions returns all sessions across users."""
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify list_sessions correctly filters by user_id."""
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify delete_session removes associated events."""
        import aiosqlite
        from google.adk.events.event import Event

        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
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
        async with aiosqlite.connect(temp_db_path) as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM events")
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 0

    async def test_delete_nonexistent_session_is_safe(
        self, temp_db_path: str, backend: FernetBackend
    ) -> None:
        """Verify deleting a non-existent session doesn't raise."""
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend,
            backend_id=BACKEND_FERNET,
        ) as service:
            # Should not raise
            await service.delete_session(
                app_name="my-agent",
                user_id="user-1",
                session_id="does-not-exist",
            )


class TestWrongKeyIntegration:
    """Integration tests for wrong encryption key scenarios."""

    async def test_wrong_key_raises_decryption_error_on_get(
        self, temp_db_path: str
    ) -> None:
        """Verify wrong key raises DecryptionError when retrieving session."""
        from adk_secure_sessions import DecryptionError

        # Create session with key1
        backend1 = FernetBackend("secret-key-one")
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend1,
            backend_id=BACKEND_FERNET,
        ) as service:
            session = await service.create_session(
                app_name="my-agent",
                user_id="user-1",
                state={"secret": "classified-data"},
            )
            session_id = session.id

        # Try to read with key2
        backend2 = FernetBackend("different-key-two")
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend2,
            backend_id=BACKEND_FERNET,
        ) as service:
            import pytest

            with pytest.raises(DecryptionError):
                await service.get_session(
                    app_name="my-agent",
                    user_id="user-1",
                    session_id=session_id,
                )

    async def test_wrong_key_raises_decryption_error_on_list(
        self, temp_db_path: str
    ) -> None:
        """Verify wrong key raises DecryptionError when listing sessions."""
        from adk_secure_sessions import DecryptionError

        # Create session with key1
        backend1 = FernetBackend("secret-key-one")
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend1,
            backend_id=BACKEND_FERNET,
        ) as service:
            await service.create_session(
                app_name="my-agent",
                user_id="user-1",
                state={"secret": "classified-data"},
            )

        # Try to list with key2
        backend2 = FernetBackend("different-key-two")
        async with EncryptedSessionService(
            db_path=temp_db_path,
            backend=backend2,
            backend_id=BACKEND_FERNET,
        ) as service:
            import pytest

            with pytest.raises(DecryptionError):
                await service.list_sessions(app_name="my-agent")
