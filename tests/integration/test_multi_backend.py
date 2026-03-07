"""Integration tests for multi-backend session lifecycle.

Verifies that sessions encrypted with different backends coexist in
the same database and decrypt correctly when the service is configured
with the appropriate dispatch map.

Typical usage::

    uv run pytest tests/integration/test_multi_backend.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]:
    The encrypted session service under test.
"""

from __future__ import annotations

import sqlite3

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from adk_secure_sessions import (
    AesGcmBackend,
    EncryptedSessionService,
    FernetBackend,
)

pytestmark = pytest.mark.integration


# --- Fixtures ---


@pytest.fixture
def aes_gcm_backend() -> AesGcmBackend:
    """An AesGcmBackend with a freshly generated key."""
    return AesGcmBackend(key=AESGCM.generate_key(bit_length=256))


# --- Story 3.3: Mixed-Backend Session Lifecycle ---


class TestMixedBackendLifecycle:
    """Integration tests for multi-backend session coexistence."""

    async def test_fernet_sessions_readable_after_primary_switch_to_aes_gcm(
        self,
        db_path: str,
        db_url: str,
        fernet_backend: FernetBackend,
        aes_gcm_backend: AesGcmBackend,
    ) -> None:
        """T: Sessions created with Fernet remain readable when AES-GCM is primary."""
        # Phase 1: Create sessions with Fernet primary
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as svc_fernet:
            s1 = await svc_fernet.create_session(
                app_name="app",
                user_id="user-1",
                state={"source": "fernet", "secret": "fernet-data"},
            )
            s1_id = s1.id

        # Phase 2: Switch to AES-GCM primary + Fernet additional
        async with EncryptedSessionService(
            db_url=db_url,
            backend=aes_gcm_backend,
            additional_backends=[fernet_backend],
        ) as svc_multi:
            # Fernet session should be readable
            retrieved = await svc_multi.get_session(
                app_name="app", user_id="user-1", session_id=s1_id
            )
            assert retrieved is not None
            assert retrieved.state["source"] == "fernet"
            assert retrieved.state["secret"] == "fernet-data"

    async def test_list_sessions_decrypts_mixed_backend_sessions(
        self,
        db_path: str,
        db_url: str,
        fernet_backend: FernetBackend,
        aes_gcm_backend: AesGcmBackend,
    ) -> None:
        """T: list_sessions returns all sessions from mixed-backend DB."""
        # Phase 1: Create Fernet sessions
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as svc_fernet:
            await svc_fernet.create_session(
                app_name="app",
                user_id="user-1",
                state={"backend": "fernet"},
            )

        # Phase 2: Add AES-GCM sessions with multi-backend service
        async with EncryptedSessionService(
            db_url=db_url,
            backend=aes_gcm_backend,
            additional_backends=[fernet_backend],
        ) as svc_multi:
            await svc_multi.create_session(
                app_name="app",
                user_id="user-1",
                state={"backend": "aes-gcm"},
            )

            # list_sessions should return both
            result = await svc_multi.list_sessions(app_name="app", user_id="user-1")
            assert len(result.sessions) == 2
            backends_found = {s.state["backend"] for s in result.sessions}
            assert backends_found == {"fernet", "aes-gcm"}

    async def test_new_sessions_use_primary_backend(
        self,
        db_path: str,
        db_url: str,
        fernet_backend: FernetBackend,
        aes_gcm_backend: AesGcmBackend,
    ) -> None:
        """T: New sessions are encrypted with the primary backend's envelope."""
        from adk_secure_sessions.serialization import BACKEND_AES_GCM

        async with EncryptedSessionService(
            db_url=db_url,
            backend=aes_gcm_backend,
            additional_backends=[fernet_backend],
        ) as svc_multi:
            await svc_multi.create_session(
                app_name="app",
                user_id="user-1",
                state={"key": "value"},
            )

        # Read raw DB to check envelope header
        import base64

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT state FROM sessions").fetchone()
        conn.close()

        assert row is not None
        envelope = base64.b64decode(row[0])
        assert envelope[1] == BACKEND_AES_GCM

    async def test_reverse_primary_reads_both_backends(
        self,
        db_path: str,
        db_url: str,
        fernet_backend: FernetBackend,
        aes_gcm_backend: AesGcmBackend,
    ) -> None:
        """T: Fernet primary + AES-GCM additional reads sessions from both."""
        # Phase 1: Create with AES-GCM primary
        async with EncryptedSessionService(
            db_url=db_url, backend=aes_gcm_backend
        ) as svc_aes:
            await svc_aes.create_session(
                app_name="app",
                user_id="user-1",
                state={"from": "aes-gcm"},
            )

        # Phase 2: Fernet primary + AES-GCM additional
        async with EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
            additional_backends=[aes_gcm_backend],
        ) as svc_reverse:
            await svc_reverse.create_session(
                app_name="app",
                user_id="user-1",
                state={"from": "fernet"},
            )

            result = await svc_reverse.list_sessions(app_name="app", user_id="user-1")
            assert len(result.sessions) == 2
            sources = {s.state["from"] for s in result.sessions}
            assert sources == {"aes-gcm", "fernet"}

    async def test_raw_db_rows_are_encrypted_for_both_backends(
        self,
        db_path: str,
        db_url: str,
        fernet_backend: FernetBackend,
        aes_gcm_backend: AesGcmBackend,
    ) -> None:
        """T: Raw DB rows are encrypted (not plaintext) for both backends."""
        # Create Fernet session
        async with EncryptedSessionService(
            db_url=db_url, backend=fernet_backend
        ) as svc_fernet:
            await svc_fernet.create_session(
                app_name="app",
                user_id="user-1",
                state={"secret": "fernet-classified"},
            )

        # Create AES-GCM session
        async with EncryptedSessionService(
            db_url=db_url,
            backend=aes_gcm_backend,
            additional_backends=[fernet_backend],
        ) as svc_multi:
            await svc_multi.create_session(
                app_name="app",
                user_id="user-1",
                state={"secret": "aes-classified"},
            )

        # Verify raw rows don't contain plaintext
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT state FROM sessions").fetchall()
        conn.close()

        assert len(rows) == 2
        for row in rows:
            raw_value = row[0]
            assert isinstance(raw_value, str)
            assert "classified" not in raw_value
            assert "secret" not in raw_value
