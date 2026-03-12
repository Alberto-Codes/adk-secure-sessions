"""Integration tests for zero-downtime key rotation.

Exercises the full rotation lifecycle using real FernetBackend instances
and a real SQLite database. Covers session, event, app-state, and
user-state table rotation and verifies the read-with-new / fail-with-old
behavior required by the key rotation contract.
"""

from __future__ import annotations

import sqlite3
from collections.abc import AsyncGenerator

import pytest
from cryptography.fernet import Fernet
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions

from adk_secure_sessions import (
    DecryptionError,
    EncryptedSessionService,
    FernetBackend,
)
from adk_secure_sessions.rotation import RotationResult, rotate_encryption_keys

pytestmark = pytest.mark.integration

# Pre-generated keys bypass PBKDF2 for test speed; two distinct keys for
# same-backend passphrase rotation scenario.
_KEY_OLD: bytes = Fernet.generate_key()
_KEY_NEW: bytes = Fernet.generate_key()

APP_NAME = "rotation-app"
"""App name used for all key rotation integration tests."""

USER_ID = "rotation-user"
"""User ID used for all key rotation integration tests."""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def old_backend() -> FernetBackend:
    """FernetBackend with the old (pre-rotation) key."""
    return FernetBackend(key=_KEY_OLD)


@pytest.fixture
def new_backend() -> FernetBackend:
    """FernetBackend with the new (post-rotation) key."""
    return FernetBackend(key=_KEY_NEW)


@pytest.fixture
async def populated_old_key_db(
    db_url: str,
    old_backend: FernetBackend,
) -> AsyncGenerator[dict[str, str], None]:
    """Populate DB with sessions/events/app-state/user-state via old_backend.

    Creates:
    - 1 session with state (sessions table)
    - 2 regular events (events table, non-NULL event_data)
    - 1 event with ``app:`` state_delta (app_states table)
    - 1 event with ``user:`` state_delta (user_states table)

    Closes the service before yielding so the DB is ready for rotation.

    Yields:
        Dict with ``session_id``, ``app_name``, ``user_id`` keys.
    """
    svc = EncryptedSessionService(db_url=db_url, backend=old_backend)
    session = await svc.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state={"rotation_test_key": "rotation-test-value"},
    )

    # Regular events — populate events table with non-NULL event_data
    for i in range(2):
        evt = Event(id=f"evt-{i}", author="user", invocation_id=f"inv-{i}")
        await svc.append_event(session, evt)

    # App-level state delta → populates app_states table
    await svc.append_event(
        session,
        Event(
            id="evt-app",
            author="agent",
            invocation_id="inv-app",
            actions=EventActions(
                state_delta={"app:rotation_config": "app-secret-value"}
            ),
        ),
    )

    # User-level state delta → populates user_states table
    await svc.append_event(
        session,
        Event(
            id="evt-user",
            author="agent",
            invocation_id="inv-user",
            actions=EventActions(
                state_delta={"user:rotation_pref": "user-secret-value"}
            ),
        ),
    )

    await svc.close()

    yield {
        "session_id": session.id,
        "app_name": APP_NAME,
        "user_id": USER_ID,
    }


# ---------------------------------------------------------------------------
# US6: Full rotation lifecycle
# ---------------------------------------------------------------------------


class TestFullRotationLifecycle:
    """AC-6: Full lifecycle: old key → rotate → read with new key → fail with old."""

    async def test_rotate_returns_positive_rotated_count(
        self,
        populated_old_key_db: dict[str, str],
        db_url: str,
        old_backend: FernetBackend,
        new_backend: FernetBackend,
    ) -> None:
        """T010: rotate_encryption_keys returns rotated > 0, skipped == 0."""
        result = await rotate_encryption_keys(
            db_url=db_url,
            old_backend=old_backend,
            new_backend=new_backend,
        )

        assert isinstance(result, RotationResult)
        assert result.rotated > 0
        assert result.skipped == 0

    async def test_new_backend_reads_succeed_after_rotation(
        self,
        populated_old_key_db: dict[str, str],
        db_url: str,
        old_backend: FernetBackend,
        new_backend: FernetBackend,
    ) -> None:
        """T011: Sessions are readable using new_backend after rotation."""
        await rotate_encryption_keys(
            db_url=db_url, old_backend=old_backend, new_backend=new_backend
        )

        svc = EncryptedSessionService(db_url=db_url, backend=new_backend)
        try:
            session = await svc.get_session(
                app_name=populated_old_key_db["app_name"],
                user_id=populated_old_key_db["user_id"],
                session_id=populated_old_key_db["session_id"],
            )
            assert session is not None
            assert session.id == populated_old_key_db["session_id"]
        finally:
            await svc.close()

    async def test_old_backend_alone_raises_decryption_error(
        self,
        populated_old_key_db: dict[str, str],
        db_url: str,
        old_backend: FernetBackend,
        new_backend: FernetBackend,
    ) -> None:
        """T012: Service with only old_backend raises DecryptionError post-rotation."""
        await rotate_encryption_keys(
            db_url=db_url, old_backend=old_backend, new_backend=new_backend
        )

        # Service configured with ONLY old_backend — cannot read new_backend data
        svc = EncryptedSessionService(db_url=db_url, backend=old_backend)
        try:
            with pytest.raises(DecryptionError):
                await svc.get_session(
                    app_name=populated_old_key_db["app_name"],
                    user_id=populated_old_key_db["user_id"],
                    session_id=populated_old_key_db["session_id"],
                )
        finally:
            await svc.close()

    async def test_all_four_tables_covered_by_rotation(
        self,
        populated_old_key_db: dict[str, str],
        db_url: str,
        db_path: str,
        old_backend: FernetBackend,
        new_backend: FernetBackend,
    ) -> None:
        """T013: All 4 tables (sessions, events, app_states, user_states) are rotated.

        Counts rows in each encrypted table before rotation and verifies the
        total rotated count matches the sum of non-NULL encrypted rows.
        """
        conn = sqlite3.connect(db_path)
        try:
            sessions_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            events_count = conn.execute(
                "SELECT COUNT(*) FROM events WHERE event_data IS NOT NULL"
            ).fetchone()[0]
            app_count = conn.execute("SELECT COUNT(*) FROM app_states").fetchone()[0]
            user_count = conn.execute("SELECT COUNT(*) FROM user_states").fetchone()[0]
        finally:
            conn.close()

        expected_rotated = sessions_count + events_count + app_count + user_count

        result = await rotate_encryption_keys(
            db_url=db_url, old_backend=old_backend, new_backend=new_backend
        )

        assert result.rotated == expected_rotated
        assert result.skipped == 0

    async def test_can_rotate_back_between_fernet_backends(
        self,
        populated_old_key_db: dict[str, str],
        db_url: str,
        old_backend: FernetBackend,
        new_backend: FernetBackend,
    ) -> None:
        """T014: Rotation is reversible — rotating back (new→old) succeeds.

        Verifies that after rotating old→new, a subsequent rotation in the
        reverse direction (new→old) successfully re-encrypts all records back.
        This confirms the utility works in both directions between same-backend
        instances with different keys, which is useful for recovery scenarios.

        Note: For same-backend rotation, re-running with the original
        old_backend after completing a rotation would attempt to decrypt
        new-key ciphertext with the old key and raise DecryptionError. The
        correct recovery path is reverse rotation (new→old), not re-run.
        """
        # First pass: rotate old key → new key
        result1 = await rotate_encryption_keys(
            db_url=db_url, old_backend=old_backend, new_backend=new_backend
        )
        assert result1.rotated > 0

        # Reverse pass: rotate new key → old key (recovery / rollback scenario)
        result2 = await rotate_encryption_keys(
            db_url=db_url, old_backend=new_backend, new_backend=old_backend
        )
        assert result2.rotated > 0
        assert result2.skipped == 0

    async def test_session_state_preserved_through_rotation(
        self,
        populated_old_key_db: dict[str, str],
        db_url: str,
        old_backend: FernetBackend,
        new_backend: FernetBackend,
    ) -> None:
        """T015: Session state is intact after rotation (decrypt→re-encrypt preserves data)."""
        await rotate_encryption_keys(
            db_url=db_url, old_backend=old_backend, new_backend=new_backend
        )

        svc = EncryptedSessionService(db_url=db_url, backend=new_backend)
        try:
            session = await svc.get_session(
                app_name=populated_old_key_db["app_name"],
                user_id=populated_old_key_db["user_id"],
                session_id=populated_old_key_db["session_id"],
            )
            assert session is not None
            # State written at creation time is preserved through rotation
            assert session.state.get("rotation_test_key") == "rotation-test-value"
        finally:
            await svc.close()
