"""Integration tests for concurrent write safety in EncryptedSessionService.

Verifies that ``EncryptedSessionService`` handles 50 simultaneous async
coroutines writing different sessions without data corruption, silent
data loss, or ciphertext mix-ups. This is the definitive NFR25
verification.

Typical usage::

    uv run pytest tests/integration/test_concurrent_writes.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]
"""

from __future__ import annotations

import asyncio

import aiosqlite
import pytest
from google.adk.events.event import Event
from google.genai import types

from adk_secure_sessions import (
    BACKEND_FERNET,
    ENVELOPE_VERSION_1,
    EncryptedSessionService,
)

pytestmark = pytest.mark.integration

APP_NAME = "test_concurrent"
"""Shared constant for app_name across all concurrent write tests."""

USER_ID = "user_concurrent"
"""Shared constant for user_id across all concurrent write tests."""

NUM_COROUTINES = 50
"""Number of concurrent coroutines — matches NFR25 specification."""


async def _create_one(
    service: EncryptedSessionService, app_name: str, user_id: str, index: int
) -> tuple[str, int]:
    """Create a session with unique state. Return (session_id, index)."""
    state = {"index": index, "sentinel": f"coroutine-{index}"}
    session = await service.create_session(
        app_name=app_name, user_id=user_id, state=state
    )
    return (session.id, index)


# --- Story 1.6b: Concurrent Write Safety Verification ---


class TestConcurrentSessionCreation:
    """NFR25: 50 concurrent coroutines writing different sessions."""

    async def test_fifty_concurrent_creates_all_recoverable(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T063: All 50 sessions recoverable with correct state after concurrent creation."""
        # Launch 50 coroutines concurrently
        tasks = [
            _create_one(encrypted_service, APP_NAME, USER_ID, i)
            for i in range(NUM_COROUTINES)
        ]
        results = await asyncio.gather(*tasks)

        # AC #1: All 50 sessions created (no silent drops)
        assert len(results) == NUM_COROUTINES

        # AC #2, #3: Each session recoverable with correct state, no DecryptionError
        for session_id, expected_index in results:
            retrieved = await encrypted_service.get_session(
                app_name=APP_NAME, user_id=USER_ID, session_id=session_id
            )
            assert retrieved is not None, (
                f"Session {session_id} (index {expected_index}) not found"
            )
            assert retrieved.state["index"] == expected_index, (
                f"Session {session_id} (expected index {expected_index}) "
                f"returned index {retrieved.state.get('index')}"
            )
            assert retrieved.state["sentinel"] == f"coroutine-{expected_index}", (
                f"Session {session_id} (expected sentinel 'coroutine-{expected_index}') "
                f"returned sentinel {retrieved.state.get('sentinel')!r}"
            )

    async def test_concurrent_writes_are_encrypted_in_database(
        self, encrypted_service: EncryptedSessionService, db_path: str
    ) -> None:
        """T064: Raw DB contains ciphertext, not plaintext, after concurrent writes."""
        # Create 50 sessions concurrently
        tasks = [
            _create_one(encrypted_service, APP_NAME, USER_ID, i)
            for i in range(NUM_COROUTINES)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == NUM_COROUTINES

        # Spot-check 3 sessions at the raw DB level
        spot_check_indices = [0, 24, 49]
        spot_check_ids = [
            session_id for session_id, index in results if index in spot_check_indices
        ]

        async with aiosqlite.connect(db_path) as raw_conn:
            for session_id in spot_check_ids:
                cursor = await raw_conn.execute(
                    "SELECT state FROM sessions WHERE id = ?", (session_id,)
                )
                row = await cursor.fetchone()
                assert row is not None, (
                    f"Session {session_id} not found in raw database"
                )
                raw_state = row[0]
                assert isinstance(raw_state, bytes)

                # Verify encrypted — no plaintext sentinel strings
                raw_str = raw_state.decode("latin-1")
                assert "coroutine-" not in raw_str
                assert "index" not in raw_str
                assert "sentinel" not in raw_str

                # Verify envelope header bytes (version + backend ID)
                assert raw_state[0:1] == bytes([ENVELOPE_VERSION_1])
                assert raw_state[1:2] == bytes([BACKEND_FERNET])

    async def test_list_sessions_returns_all_fifty(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T065: list_sessions returns exactly 50 after concurrent creation."""
        # Create 50 sessions concurrently
        tasks = [
            _create_one(encrypted_service, APP_NAME, USER_ID, i)
            for i in range(NUM_COROUTINES)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == NUM_COROUTINES

        # list_sessions returns ListSessionsResponse — access .sessions
        result = await encrypted_service.list_sessions(
            app_name=APP_NAME, user_id=USER_ID
        )
        assert len(result.sessions) == NUM_COROUTINES


class TestConcurrentEventAppends:
    """Bonus: concurrent append_event on a single session."""

    async def test_fifty_concurrent_event_appends(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T066: 50 concurrent append_event calls all persist correctly."""
        # Create a single session to append events to
        session = await encrypted_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, state={"base": True}
        )

        # Re-fetch session for a clean in-memory state
        session = await encrypted_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session.id
        )
        assert session is not None

        async def _append_one(index: int) -> Event:
            """Append a single event with distinct content."""
            event = Event(
                invocation_id=f"inv-{index}",
                author=f"test-agent-{index}",
                content=types.Content(
                    parts=[types.Part(text=f"Event from coroutine {index}")]
                ),
            )
            return await encrypted_service.append_event(session, event)

        # Launch 50 concurrent append_event calls
        tasks = [_append_one(i) for i in range(NUM_COROUTINES)]
        appended_events = await asyncio.gather(*tasks)
        assert len(appended_events) == NUM_COROUTINES

        # Verify all 50 events persisted by re-fetching the session
        retrieved = await encrypted_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session.id
        )
        assert retrieved is not None
        assert len(retrieved.events) == NUM_COROUTINES

        # Verify each event has distinct content and author
        event_texts = set()
        event_authors = set()
        for event in retrieved.events:
            event_authors.add(event.author)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        event_texts.add(part.text)
        assert len(event_texts) == NUM_COROUTINES
        assert len(event_authors) == NUM_COROUTINES
