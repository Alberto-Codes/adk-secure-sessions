"""Encryption boundary verification tests.

Gold-standard tests that verify ciphertext at rest by reading raw
database rows directly via synchronous SQLAlchemy, bypassing the
service layer entirely. Also verifies metadata remains plaintext
and edge cases (empty state, complex nested structures) round-trip
correctly through the encryption boundary.

Typical usage::

    uv run pytest tests/integration/test_encryption_boundary.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]:
    The encrypted session service under test.
"""

from __future__ import annotations

import sqlite3

import pytest
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions

from adk_secure_sessions import (
    EncryptedSessionService,
    FernetBackend,
)

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# AC-2: Round-Trip Encryption — Boundary Verification
# ---------------------------------------------------------------------------


class TestStateCiphertextAtRest:
    """Verify session state is stored as ciphertext in the database."""

    async def test_state_stored_as_ciphertext(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: Raw DB row for sessions.state is not JSON-parseable plaintext."""
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            await service.create_session(
                app_name="app", user_id="user-1", state={"secret": "classified"}
            )

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT state FROM sessions").fetchone()
        conn.close()

        assert row is not None
        raw_value = row[0]
        assert isinstance(raw_value, str)

        # Raw value must not contain plaintext — it's base64-encoded ciphertext
        assert "classified" not in raw_value
        assert "secret" not in raw_value


class TestEventCiphertextAtRest:
    """Verify event data is stored as ciphertext in the database."""

    async def test_event_data_stored_as_ciphertext(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: Raw DB row for events.event_data is not JSON-parseable plaintext."""
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            session = await service.create_session(app_name="app", user_id="user-1")
            event = Event(
                id="evt-secret",
                author="agent",
                invocation_id="inv-1",
            )
            await service.append_event(session, event)

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT event_data FROM events").fetchone()
        conn.close()

        assert row is not None
        raw_value = row[0]
        assert isinstance(raw_value, str)

        # Must not contain plaintext event fields
        assert '"author"' not in raw_value
        assert '"invocation_id"' not in raw_value


class TestAppStateCiphertextAtRest:
    """Verify app_states.state is stored as ciphertext."""

    async def test_app_state_stored_as_ciphertext(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: App-level state written via state_delta is ciphertext at rest."""
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            session = await service.create_session(app_name="app", user_id="user-1")
            event = Event(
                id="evt-app",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(
                    state_delta={"app:global_key": "app-secret-value"}
                ),
            )
            await service.append_event(session, event)

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT state FROM app_states").fetchone()
        conn.close()

        if row is None:
            pytest.skip("ADK did not populate app_states for this operation")

        raw_value = row[0]
        assert isinstance(raw_value, str)
        assert "app-secret-value" not in raw_value
        assert "global_key" not in raw_value


class TestUserStateCiphertextAtRest:
    """Verify user_states.state is stored as ciphertext."""

    async def test_user_state_stored_as_ciphertext(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: User-level state written via state_delta is ciphertext at rest."""
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            session = await service.create_session(app_name="app", user_id="user-1")
            event = Event(
                id="evt-user",
                author="agent",
                invocation_id="inv-1",
                actions=EventActions(
                    state_delta={"user:personal_data": "user-secret-value"}
                ),
            )
            await service.append_event(session, event)

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT state FROM user_states").fetchone()
        conn.close()

        if row is None:
            pytest.skip("ADK did not populate user_states for this operation")

        raw_value = row[0]
        assert isinstance(raw_value, str)
        assert "user-secret-value" not in raw_value
        assert "personal_data" not in raw_value


class TestMetadataStoredPlaintext:
    """Verify metadata fields remain queryable plaintext."""

    async def test_metadata_stored_plaintext(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: session_id, app_name, user_id are readable plaintext in raw DB."""
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            session = await service.create_session(
                app_name="my-agent", user_id="alice", state={"key": "val"}
            )
            session_id = session.id

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT app_name, user_id, id FROM sessions").fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "my-agent"
        assert row[1] == "alice"
        assert row[2] == session_id


class TestEmptyStateRoundTrip:
    """Verify empty state round-trips through encryption boundary."""

    async def test_empty_state_round_trip_with_boundary_check(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: Empty {} state encrypts, stores as ciphertext, decrypts back to {}."""
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            session = await service.create_session(
                app_name="app", user_id="user-1", state={}
            )

            # Verify raw DB has ciphertext (not empty string or null)
            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT state FROM sessions").fetchone()
            conn.close()
            assert row is not None
            raw_value = row[0]
            assert raw_value is not None
            assert len(raw_value) > 0  # Envelope exists even for empty dict

            # Verify round-trip produces empty dict
            retrieved = await service.get_session(
                app_name="app", user_id="user-1", session_id=session.id
            )
            assert retrieved is not None
            assert retrieved.state == {}
            assert len(retrieved.events) == 0


class TestComplexNestedStateRoundTrip:
    """Verify deeply nested structures survive the encryption boundary."""

    async def test_complex_nested_state_round_trip(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: Nested dict with lists, numbers, strings, booleans, nulls round-trips."""
        complex_state = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean_true": True,
            "boolean_false": False,
            "null_value": None,
            "list": [1, "two", 3.0, None, True],
            "nested": {
                "level2": {
                    "level3": {"deep": "value"},
                    "array": [{"a": 1}, {"b": 2}],
                }
            },
            "empty_dict": {},
            "empty_list": [],
        }

        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            session = await service.create_session(
                app_name="app", user_id="user-1", state=complex_state
            )
            retrieved = await service.get_session(
                app_name="app", user_id="user-1", session_id=session.id
            )

        assert retrieved is not None
        assert retrieved.state["string"] == "hello"
        assert retrieved.state["integer"] == 42
        assert retrieved.state["float"] == 3.14
        assert retrieved.state["boolean_true"] is True
        assert retrieved.state["boolean_false"] is False
        assert retrieved.state["null_value"] is None
        assert retrieved.state["list"] == [1, "two", 3.0, None, True]
        assert retrieved.state["nested"]["level2"]["level3"]["deep"] == "value"
        assert retrieved.state["nested"]["level2"]["array"] == [{"a": 1}, {"b": 2}]
        assert retrieved.state["empty_dict"] == {}
        assert retrieved.state["empty_list"] == []


# ---------------------------------------------------------------------------
# Cross-Cutting: Tampered Ciphertext Detection at Rest
# ---------------------------------------------------------------------------


class TestTamperedCiphertextAtRest:
    """Verify service detects tampered database rows (security boundary)."""

    async def test_tampered_state_raises_decryption_error(
        self, db_path: str, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: Modifying raw DB state causes DecryptionError on read."""
        from adk_secure_sessions import DecryptionError

        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            session = await service.create_session(
                app_name="app", user_id="user-1", state={"key": "value"}
            )
            session_id = session.id

        # Tamper with the raw ciphertext in the database
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT state FROM sessions").fetchone()
        assert row is not None
        tampered = row[0][:-4] + "XXXX"  # Corrupt the base64 tail
        conn.execute("UPDATE sessions SET state = ?", (tampered,))
        conn.commit()
        conn.close()

        # Reading the tampered session should raise DecryptionError
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as service:
            with pytest.raises(DecryptionError):
                await service.get_session(
                    app_name="app", user_id="user-1", session_id=session_id
                )
