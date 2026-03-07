"""Database encryption verification tests for EncryptedSessionService.

Verifies that session state, event data, app state, and user state are
encrypted in the raw database, and that wrong-key decryption raises
``DecryptionError`` on all data paths.

Typical usage::

    uv run pytest tests/integration/test_adk_encryption.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]:
    The encrypted wrapper under test.
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

# Pre-generated Fernet keys — skip PBKDF2 in wrong-key tests that validate
# decryption isolation, not passphrase derivation.
_KEY_A = Fernet.generate_key()
_KEY_B = Fernet.generate_key()

APP_NAME = "secure-app"
"""Default app name for encryption verification tests."""

APP_NAME_WRONG_KEY = "my-agent"
"""App name for wrong-key decryption tests."""

APP_NAME_STATE = "test-app"
"""App name for app/user state encryption tests."""

USER_ID = "user-1"
"""Default user ID for encryption integration tests."""

USER_ID_SECRET = "user-secret"
"""User ID for initial state encryption test."""

pytestmark = pytest.mark.integration

# =============================================================================
# Database Encryption Verification
# =============================================================================


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
                app_name=APP_NAME,
                user_id=USER_ID_SECRET,
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
                app_name=APP_NAME,
                user_id=USER_ID,
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
                app_name=APP_NAME,
                user_id=USER_ID,
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
                app_name=APP_NAME,
                user_id=USER_ID,
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


# =============================================================================
# Wrong Key Tests
# =============================================================================


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
                app_name=APP_NAME_WRONG_KEY,
                user_id=USER_ID,
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
                    app_name=APP_NAME_WRONG_KEY,
                    user_id=USER_ID,
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
                app_name=APP_NAME_WRONG_KEY,
                user_id=USER_ID,
                state={"secret": "classified-data"},
            )

        # Try to list with key2
        backend2 = FernetBackend(_KEY_B)
        async with EncryptedSessionService(
            db_url=db_url,
            backend=backend2,
        ) as service:
            with pytest.raises(DecryptionError):
                await service.list_sessions(app_name=APP_NAME_WRONG_KEY)


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
                app_name=APP_NAME_STATE,
                user_id=USER_ID,
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
                    app_name=APP_NAME_STATE,
                    user_id=USER_ID,
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
                app_name=APP_NAME_STATE,
                user_id=USER_ID,
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
                    app_name=APP_NAME_STATE,
                    user_id=USER_ID,
                    session_id=session_id,
                )
