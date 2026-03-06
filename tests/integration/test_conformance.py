"""Conformance tests comparing EncryptedSessionService vs DatabaseSessionService.

Verifies that the wrapped ``EncryptedSessionService`` produces
behaviorally equivalent results to a raw ``DatabaseSessionService``
for identical inputs. Each service uses a separate database to
prevent interference.

Typical usage::

    uv run pytest tests/integration/test_conformance.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]:
    The encrypted wrapper under test.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.sessions.database_session_service import DatabaseSessionService

from adk_secure_sessions import (
    DecryptionError,
    EncryptedSessionService,
    FernetBackend,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def unencrypted_service(
    tmp_path: Path,
) -> AsyncGenerator[DatabaseSessionService, None]:
    """A raw DatabaseSessionService with its own database.

    Uses a separate database file from the encrypted service to prevent
    table/schema conflicts.
    """
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'plain.db'}"
    svc = DatabaseSessionService(db_url=db_url)
    yield svc
    await svc.close()


@pytest.fixture
async def enc_service(
    tmp_path: Path, fernet_backend: FernetBackend
) -> AsyncGenerator[EncryptedSessionService, None]:
    """An EncryptedSessionService with its own database for conformance tests."""
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'encrypted.db'}"
    svc = EncryptedSessionService(db_url=db_url, backend=fernet_backend)
    yield svc
    await svc.close()


@pytest.fixture
async def shared_db_encrypted_service(
    tmp_path: Path, fernet_backend: FernetBackend
) -> AsyncGenerator[tuple[DatabaseSessionService, EncryptedSessionService, Path], None]:
    """Both services pointing at the SAME database for unencrypted detection tests.

    Returns (unencrypted_service, encrypted_service, db_file_path).
    The unencrypted service writes first, then the encrypted service reads.
    """
    db_file = tmp_path / "shared.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    plain_svc = DatabaseSessionService(db_url=db_url)
    enc_svc = EncryptedSessionService(db_url=db_url, backend=fernet_backend)
    yield plain_svc, enc_svc, db_file
    await enc_svc.close()
    await plain_svc.close()


# ---------------------------------------------------------------------------
# AC-1: Conformance Testing - Core Operations
# ---------------------------------------------------------------------------


class TestCreateSessionConformance:
    """Conformance: create_session produces equivalent Session objects."""

    async def test_create_session_conformance(
        self,
        enc_service: EncryptedSessionService,
        unencrypted_service: DatabaseSessionService,
    ) -> None:
        """T: Identical inputs produce same Session structure (minus auto-generated IDs)."""
        state = {"key": "value", "nested": {"a": 1}}

        enc_session = await enc_service.create_session(
            app_name="app", user_id="user-1", state=state
        )
        plain_session = await unencrypted_service.create_session(
            app_name="app", user_id="user-1", state=state
        )

        # Structural equivalence — auto-generated fields differ
        assert enc_session.app_name == plain_session.app_name
        assert enc_session.user_id == plain_session.user_id
        assert enc_session.state == plain_session.state
        assert type(enc_session) is type(plain_session)


class TestGetSessionConformance:
    """Conformance: get_session retrieves equivalent data."""

    async def test_get_session_conformance(
        self,
        enc_service: EncryptedSessionService,
        unencrypted_service: DatabaseSessionService,
    ) -> None:
        """T: Create + get produces same Session fields on both services."""
        state = {"counter": 42, "items": ["a", "b", "c"]}

        enc_created = await enc_service.create_session(
            app_name="app", user_id="user-1", state=state
        )
        plain_created = await unencrypted_service.create_session(
            app_name="app", user_id="user-1", state=state
        )

        enc_retrieved = await enc_service.get_session(
            app_name="app", user_id="user-1", session_id=enc_created.id
        )
        plain_retrieved = await unencrypted_service.get_session(
            app_name="app", user_id="user-1", session_id=plain_created.id
        )

        assert enc_retrieved is not None
        assert plain_retrieved is not None
        assert enc_retrieved.app_name == plain_retrieved.app_name
        assert enc_retrieved.user_id == plain_retrieved.user_id
        assert enc_retrieved.state == plain_retrieved.state
        assert len(enc_retrieved.events) == len(plain_retrieved.events)


class TestListSessionsConformance:
    """Conformance: list_sessions returns equivalent response structure."""

    async def test_list_sessions_conformance(
        self,
        enc_service: EncryptedSessionService,
        unencrypted_service: DatabaseSessionService,
    ) -> None:
        """T: Multiple sessions listed with same structure on both services."""
        for i in range(3):
            await enc_service.create_session(
                app_name="app", user_id=f"user-{i}", state={"i": i}
            )
            await unencrypted_service.create_session(
                app_name="app", user_id=f"user-{i}", state={"i": i}
            )

        enc_result = await enc_service.list_sessions(app_name="app")
        plain_result = await unencrypted_service.list_sessions(app_name="app")

        assert len(enc_result.sessions) == len(plain_result.sessions)
        assert len(enc_result.sessions) == 3

        # Both return sessions with correct state (order may differ)
        enc_states = sorted(s.state.get("i", -1) for s in enc_result.sessions)
        plain_states = sorted(s.state.get("i", -1) for s in plain_result.sessions)
        assert enc_states == plain_states


class TestDeleteSessionConformance:
    """Conformance: delete_session has same effect on both services."""

    async def test_delete_session_conformance(
        self,
        enc_service: EncryptedSessionService,
        unencrypted_service: DatabaseSessionService,
    ) -> None:
        """T: Create + delete + get returns None on both services."""
        enc_session = await enc_service.create_session(
            app_name="app", user_id="user-1", state={"x": 1}
        )
        plain_session = await unencrypted_service.create_session(
            app_name="app", user_id="user-1", state={"x": 1}
        )

        await enc_service.delete_session(
            app_name="app", user_id="user-1", session_id=enc_session.id
        )
        await unencrypted_service.delete_session(
            app_name="app", user_id="user-1", session_id=plain_session.id
        )

        enc_result = await enc_service.get_session(
            app_name="app", user_id="user-1", session_id=enc_session.id
        )
        plain_result = await unencrypted_service.get_session(
            app_name="app", user_id="user-1", session_id=plain_session.id
        )

        assert enc_result is None
        assert plain_result is None


class TestAppendEventConformance:
    """Conformance: append_event produces equivalent Event objects."""

    async def test_append_event_conformance(
        self,
        enc_service: EncryptedSessionService,
        unencrypted_service: DatabaseSessionService,
    ) -> None:
        """T: Appended events have same content dict on both services."""
        enc_session = await enc_service.create_session(app_name="app", user_id="user-1")
        plain_session = await unencrypted_service.create_session(
            app_name="app", user_id="user-1"
        )

        event = Event(
            id="evt-1",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"response": "hello"}),
        )

        await enc_service.append_event(enc_session, event)
        await unencrypted_service.append_event(plain_session, event)

        enc_retrieved = await enc_service.get_session(
            app_name="app", user_id="user-1", session_id=enc_session.id
        )
        plain_retrieved = await unencrypted_service.get_session(
            app_name="app", user_id="user-1", session_id=plain_session.id
        )

        assert enc_retrieved is not None
        assert plain_retrieved is not None
        assert len(enc_retrieved.events) == 1
        assert len(plain_retrieved.events) == 1

        enc_event = enc_retrieved.events[0]
        plain_event = plain_retrieved.events[0]

        # Event content and action equality
        assert enc_event.author == plain_event.author
        assert enc_event.invocation_id == plain_event.invocation_id
        assert enc_event.actions == plain_event.actions


class TestStateMergeConformance:
    """Conformance: state merge via events produces same result."""

    async def test_state_merge_conformance(
        self,
        enc_service: EncryptedSessionService,
        unencrypted_service: DatabaseSessionService,
    ) -> None:
        """T: State A + delta B produces same merged state on both services."""
        initial_state = {"theme": "dark", "count": 0}

        enc_session = await enc_service.create_session(
            app_name="app", user_id="user-1", state=initial_state
        )
        plain_session = await unencrypted_service.create_session(
            app_name="app", user_id="user-1", state=initial_state
        )

        # Apply state delta via event
        delta_event = Event(
            id="evt-merge",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"count": 5, "new_key": "added"}),
        )

        await enc_service.append_event(enc_session, delta_event)
        await unencrypted_service.append_event(plain_session, delta_event)

        enc_retrieved = await enc_service.get_session(
            app_name="app", user_id="user-1", session_id=enc_session.id
        )
        plain_retrieved = await unencrypted_service.get_session(
            app_name="app", user_id="user-1", session_id=plain_session.id
        )

        assert enc_retrieved is not None
        assert plain_retrieved is not None
        assert enc_retrieved.state == plain_retrieved.state
        assert enc_retrieved.state["count"] == 5
        assert enc_retrieved.state["new_key"] == "added"
        assert enc_retrieved.state["theme"] == "dark"


# ---------------------------------------------------------------------------
# AC-4: Unencrypted Data Detection
# ---------------------------------------------------------------------------


class TestUnencryptedDataDetection:
    """Verify EncryptedSessionService detects unencrypted data."""

    async def test_unencrypted_data_raises_clear_error(
        self,
        shared_db_encrypted_service: tuple[
            DatabaseSessionService, EncryptedSessionService, Path
        ],
    ) -> None:
        """T: Plaintext data from raw DatabaseSessionService raises error on encrypted read."""
        plain_svc, enc_svc, _db_file = shared_db_encrypted_service

        # Create session with raw DatabaseSessionService (plaintext)
        plain_session = await plain_svc.create_session(
            app_name="app", user_id="user-1", state={"secret": "plaintext-value"}
        )

        # Attempt to read with EncryptedSessionService on same DB
        # Error may be "does not appear to be encrypted" (base64 decode failure)
        # or "Unsupported envelope version" (partial base64 decode succeeds
        # but envelope header is invalid)
        with pytest.raises(DecryptionError) as exc_info:
            await enc_svc.get_session(
                app_name="app",
                user_id="user-1",
                session_id=plain_session.id,
            )
        # AC-4: message must indicate unencrypted data, not wrong key
        assert "wrong key" not in str(exc_info.value)

    async def test_unencrypted_event_data_detected(
        self,
        shared_db_encrypted_service: tuple[
            DatabaseSessionService, EncryptedSessionService, Path
        ],
    ) -> None:
        """T: Plaintext event data from raw service raises error on encrypted read."""
        plain_svc, enc_svc, _db_file = shared_db_encrypted_service

        plain_session = await plain_svc.create_session(
            app_name="evtapp", user_id="user-1"
        )

        event = Event(
            id="evt-plain",
            author="agent",
            invocation_id="inv-1",
            actions=EventActions(state_delta={"private": "data"}),
        )
        await plain_svc.append_event(plain_session, event)

        # Reading the session should fail because event/state data is unencrypted
        with pytest.raises(DecryptionError) as exc_info:
            await enc_svc.get_session(
                app_name="evtapp",
                user_id="user-1",
                session_id=plain_session.id,
            )
        # AC-4: message must indicate unencrypted data, not wrong key
        assert "wrong key" not in str(exc_info.value)
