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
from sqlalchemy import JSON

from adk_secure_sessions import (
    EncryptedSessionService,
    FernetBackend,
)
from adk_secure_sessions.protocols import EncryptionBackend
from adk_secure_sessions.services.models import create_encrypted_models

pytestmark = pytest.mark.integration

APP_NAME = "test"
"""Default app name for conformance tests."""

USER_ID = "user"
"""Default user ID for conformance tests."""

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
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Verify all required abstract methods are implemented."""
        # All these methods should exist and be callable
        assert callable(encrypted_service.create_session)
        assert callable(encrypted_service.get_session)
        assert callable(encrypted_service.list_sessions)
        assert callable(encrypted_service.delete_session)
        assert callable(encrypted_service.append_event)

    async def test_returns_correct_types(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Verify methods return ADK-compatible types."""
        from google.adk.sessions.base_session_service import ListSessionsResponse
        from google.adk.sessions.session import Session

        service = encrypted_service

        # create_session returns Session
        session = await service.create_session(app_name=APP_NAME, user_id=USER_ID)
        assert isinstance(session, Session)

        # get_session returns Session or None
        result = await service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session.id
        )
        assert isinstance(result, Session)

        # list_sessions returns ListSessionsResponse
        list_result = await service.list_sessions(app_name=APP_NAME)
        assert isinstance(list_result, ListSessionsResponse)


# =============================================================================
# EncryptionBackend Protocol Conformance
# =============================================================================


# =============================================================================
# StorageSession Method Parity (Sentinel)
# =============================================================================


class TestStorageSessionMethodParity:
    """Sentinel tests: EncryptedStorageSession duck-types ADK's StorageSession."""

    def test_all_public_methods_present(self) -> None:
        """AC6: All public methods on ADK StorageSession exist on ours."""
        from google.adk.sessions.schemas.v1 import StorageSession

        _, schema = create_encrypted_models(JSON())

        upstream_methods = {
            name
            for name in dir(StorageSession)
            if not name.startswith("_") and callable(getattr(StorageSession, name))
        }
        upstream_properties = {
            name
            for name in dir(StorageSession)
            if not name.startswith("_")
            and isinstance(getattr(StorageSession, name, None), property)
        }
        upstream_public = upstream_methods | upstream_properties

        # Exclude SQLAlchemy ORM internals that don't apply to duck-typing
        orm_internals = {"metadata", "registry"}
        upstream_public -= orm_internals

        encrypted_cls = schema.StorageSession
        missing = {name for name in upstream_public if not hasattr(encrypted_cls, name)}

        assert not missing, (
            f"EncryptedStorageSession is missing public members from "
            f"StorageSession: {sorted(missing)}"
        )

    async def test_create_session_roundtrip_sets_storage_update_marker(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """AC5: _storage_update_marker is set after create_session() round-trip."""
        session = await encrypted_service.create_session(
            app_name=APP_NAME, user_id=USER_ID
        )

        assert hasattr(session, "_storage_update_marker")
        assert session._storage_update_marker is not None
        assert isinstance(session._storage_update_marker, str)

    async def test_get_session_roundtrip_sets_storage_update_marker(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """AC5: _storage_update_marker persists through get_session() round-trip."""
        created = await encrypted_service.create_session(
            app_name=APP_NAME, user_id=USER_ID
        )

        retrieved = await encrypted_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=created.id
        )

        assert retrieved is not None
        assert hasattr(retrieved, "_storage_update_marker")
        assert retrieved._storage_update_marker is not None
        assert isinstance(retrieved._storage_update_marker, str)


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
