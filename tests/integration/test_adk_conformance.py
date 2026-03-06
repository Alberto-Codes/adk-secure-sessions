"""Interface and protocol conformance tests for EncryptedSessionService.

Verifies that ``EncryptedSessionService`` correctly implements ADK's
``BaseSessionService`` interface and that ``EncryptionBackend`` protocol
conformance works at runtime.

Typical usage::

    uv run pytest tests/integration/test_adk_conformance.py -v

See Also:
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]:
    The encrypted wrapper under test.
"""

from __future__ import annotations

import pytest

from adk_secure_sessions import (
    EncryptedSessionService,
    FernetBackend,
)
from adk_secure_sessions.protocols import EncryptionBackend

pytestmark = pytest.mark.integration

# =============================================================================
# BaseSessionService Interface Conformance
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


# =============================================================================
# EncryptionBackend Protocol Conformance
# =============================================================================


class TestProtocolConformance:
    """T048: Tests with mock EncryptionBackend to verify protocol."""

    async def test_backend_protocol_is_runtime_checkable(self) -> None:
        """Verify EncryptionBackend protocol is runtime checkable."""
        from cryptography.fernet import Fernet

        # FernetBackend should pass isinstance check
        backend = FernetBackend(Fernet.generate_key())
        assert isinstance(backend, EncryptionBackend)

        # Non-conforming object should fail
        class NotABackend:
            pass

        assert not isinstance(NotABackend(), EncryptionBackend)
