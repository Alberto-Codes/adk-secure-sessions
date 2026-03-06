"""CRUD and workflow integration tests for EncryptedSessionService.

Tests verify round-trip session workflows, list/delete operations,
cascade deletes, session recreation, and state merge precedence.

Typical usage::

    uv run pytest tests/integration/test_adk_crud.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]:
    The encrypted wrapper under test.
"""

from __future__ import annotations

import sqlite3

import pytest

from adk_secure_sessions import (
    EncryptedSessionService,
    FernetBackend,
)

pytestmark = pytest.mark.integration

# =============================================================================
# Round-Trip Workflow
# =============================================================================


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


# =============================================================================
# List Sessions
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


# =============================================================================
# Delete Sessions
# =============================================================================


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


# =============================================================================
# Session Recreate After Delete
# =============================================================================


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


# =============================================================================
# State Merge Precedence
# =============================================================================


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
