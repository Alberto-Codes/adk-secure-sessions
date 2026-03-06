"""Unit tests for EncryptedSessionService.

Tests cover:
- Constructor validation (backend protocol check)
- Session CRUD operations with encryption
- Wrong-key decryption raises DecryptionError
- Empty state round-trip
- Sentinel tests for ADK compatibility
"""

from __future__ import annotations

import inspect

import pytest
from google.adk.sessions.database_session_service import DatabaseSessionService

from adk_secure_sessions import (
    ConfigurationError,
    DecryptionError,
    EncryptedSessionService,
    FernetBackend,
)

pytestmark = pytest.mark.unit

# =============================================================================
# Story 7.3: Constructor Validation
# =============================================================================


class TestConstructorValidation:
    """Tests for EncryptedSessionService.__init__ parameter validation."""

    def test_invalid_backend_raises_configuration_error(self, db_url: str) -> None:
        """Non-EncryptionBackend backend raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="EncryptionBackend protocol"):
            EncryptedSessionService(
                db_url=db_url,
                backend="not-a-backend",  # type: ignore[arg-type]
            )

    def test_valid_construction_does_not_raise(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """Valid parameters do not raise any error."""
        service = EncryptedSessionService(
            db_url=db_url,
            backend=fernet_backend,
        )
        assert service is not None

    def test_subclasses_database_session_service(self) -> None:
        """EncryptedSessionService subclasses DatabaseSessionService."""
        assert issubclass(EncryptedSessionService, DatabaseSessionService)


# =============================================================================
# Story 7.3: CRUD Round-Trip
# =============================================================================


class TestSessionCRUD:
    """Tests for session CRUD operations with encryption."""

    async def test_create_and_get_session_round_trip(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Create a session and retrieve it with correct state."""
        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state={"secret": "sensitive", "count": 42},
        )
        assert session.id is not None

        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert retrieved.state["secret"] == "sensitive"
        assert retrieved.state["count"] == 42

    async def test_list_sessions(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """List sessions returns created sessions."""
        await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state={"key": "value"},
        )

        result = await encrypted_service.list_sessions(
            app_name="test-app",
            user_id="user-1",
        )
        assert len(result.sessions) >= 1

    async def test_delete_session(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Delete a session makes it unretrievable."""
        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
        )

        await encrypted_service.delete_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )

        gone = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert gone is None

    async def test_get_nonexistent_session_returns_none(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """Getting a non-existent session returns None."""
        result = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id="does-not-exist",
        )
        assert result is None


# =============================================================================
# Story 7.3: Encryption Verification
# =============================================================================


class TestEncryptionRoundTrip:
    """Tests for encryption round-trip correctness."""

    async def test_encrypted_state_round_trip(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T: Plaintext -> encrypted in DB -> decrypted -> matches original."""
        original_state = {
            "api_key": "sk-super-secret",
            "ssn": "123-45-6789",
            "nested": {"deep": {"value": [1, 2, 3]}},
        }
        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state=original_state,
        )

        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert retrieved.state["api_key"] == "sk-super-secret"
        assert retrieved.state["ssn"] == "123-45-6789"
        assert retrieved.state["nested"]["deep"]["value"] == [1, 2, 3]

    async def test_empty_state_round_trip(
        self, encrypted_service: EncryptedSessionService
    ) -> None:
        """T: Empty state dict survives round-trip."""
        session = await encrypted_service.create_session(
            app_name="test-app",
            user_id="user-1",
            state={},
        )

        retrieved = await encrypted_service.get_session(
            app_name="test-app",
            user_id="user-1",
            session_id=session.id,
        )
        assert retrieved is not None
        assert isinstance(retrieved.state, dict)


class TestWrongKeyDecryption:
    """Tests for wrong-key error handling."""

    async def test_wrong_key_raises_decryption_error(self, db_url: str) -> None:
        """T: Decrypting with wrong key raises DecryptionError, not StatementError."""
        from cryptography.fernet import Fernet

        key_a = Fernet.generate_key()
        key_b = Fernet.generate_key()

        backend_a = FernetBackend(key_a)
        service_a = EncryptedSessionService(db_url=db_url, backend=backend_a)

        session = await service_a.create_session(
            app_name="test-app",
            user_id="user-1",
            state={"secret": "classified"},
        )
        session_id = session.id
        await service_a.close()

        backend_b = FernetBackend(key_b)
        service_b = EncryptedSessionService(db_url=db_url, backend=backend_b)

        with pytest.raises(DecryptionError):
            await service_b.get_session(
                app_name="test-app",
                user_id="user-1",
                session_id=session_id,
            )
        await service_b.close()

    async def test_wrong_key_error_not_wrapped_in_statement_error(
        self, db_url: str
    ) -> None:
        """T: DecryptionError propagates directly, not wrapped in StatementError."""
        from cryptography.fernet import Fernet
        from sqlalchemy.exc import StatementError

        key_a = Fernet.generate_key()
        key_b = Fernet.generate_key()

        backend_a = FernetBackend(key_a)
        service_a = EncryptedSessionService(db_url=db_url, backend=backend_a)

        session = await service_a.create_session(
            app_name="test-app",
            user_id="user-1",
            state={"secret": "classified"},
        )
        session_id = session.id
        await service_a.close()

        backend_b = FernetBackend(key_b)
        service_b = EncryptedSessionService(db_url=db_url, backend=backend_b)

        try:
            await service_b.get_session(
                app_name="test-app",
                user_id="user-1",
                session_id=session_id,
            )
            pytest.fail("Expected DecryptionError")
        except DecryptionError:
            pass  # Expected — direct propagation, not wrapped
        except StatementError:
            pytest.fail(
                "DecryptionError was wrapped in StatementError — "
                "DontWrapMixin is not working"
            )
        finally:
            await service_b.close()


# =============================================================================
# Story 7.3: Sentinel Tests (ADK Compatibility)
# =============================================================================


class TestADKSentinels:
    """Sentinel tests that catch ADK signature changes in CI."""

    def test_database_session_service_has_get_schema_classes(self) -> None:
        """T: DatabaseSessionService has _get_schema_classes method."""
        assert hasattr(DatabaseSessionService, "_get_schema_classes")

    def test_database_session_service_has_prepare_tables(self) -> None:
        """T: DatabaseSessionService has _prepare_tables method."""
        assert hasattr(DatabaseSessionService, "_prepare_tables")

    def test_database_session_service_init_accepts_db_url(self) -> None:
        """T: DatabaseSessionService.__init__ accepts db_url parameter."""
        sig = inspect.signature(DatabaseSessionService.__init__)
        assert "db_url" in sig.parameters

    def test_encrypted_service_has_tables_created(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: EncryptedSessionService instance has _tables_created attribute."""
        service = EncryptedSessionService(db_url=db_url, backend=fernet_backend)
        assert hasattr(service, "_tables_created")

    def test_encrypted_service_has_table_creation_lock(
        self, db_url: str, fernet_backend: FernetBackend
    ) -> None:
        """T: EncryptedSessionService instance has _table_creation_lock attribute."""
        service = EncryptedSessionService(db_url=db_url, backend=fernet_backend)
        assert hasattr(service, "_table_creation_lock")

    def test_encrypted_service_zero_crud_overrides(self) -> None:
        """T: EncryptedSessionService does not override any CRUD methods."""
        crud_methods = [
            "create_session",
            "get_session",
            "list_sessions",
            "delete_session",
            "append_event",
        ]
        for method_name in crud_methods:
            # Method should be inherited from DatabaseSessionService,
            # not overridden in EncryptedSessionService
            assert method_name not in EncryptedSessionService.__dict__, (
                f"{method_name} is overridden in EncryptedSessionService — "
                f"should be inherited from DatabaseSessionService"
            )
