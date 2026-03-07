"""Encrypted session service wrapping ADK's DatabaseSessionService.

Provides transparent field-level encryption for session state and event
data by subclassing ``DatabaseSessionService`` and injecting encrypted
SQLAlchemy model classes via ``_get_schema_classes()`` and
``_prepare_tables()`` overrides. All CRUD operations are delegated to
the parent class — no method overrides needed.

Examples:
    Basic usage with FernetBackend:

    ```python
    from adk_secure_sessions import FernetBackend, EncryptedSessionService

    backend = FernetBackend("my-secret-passphrase")
    service = EncryptedSessionService(
        db_url="sqlite+aiosqlite:///sessions.db",
        backend=backend,
    )
    session = await service.create_session(
        app_name="my-agent",
        user_id="user-123",
        state={"secret": "sensitive-data"},
    )
    ```

See Also:
    [`adk_secure_sessions.backends.fernet`][]: Fernet encryption backend.
    [`adk_secure_sessions.protocols`][]: EncryptionBackend protocol definition.
"""

from __future__ import annotations

import logging
from typing import Any

from google.adk.sessions.database_session_service import DatabaseSessionService

from adk_secure_sessions.exceptions import ConfigurationError
from adk_secure_sessions.protocols import EncryptionBackend
from adk_secure_sessions.services.models import (
    _EncryptedSchemaClasses,
    create_encrypted_models,
)
from adk_secure_sessions.services.type_decorator import EncryptedJSON

logger = logging.getLogger(__name__)


class EncryptedSessionService(DatabaseSessionService):
    """Encrypted session service wrapping DatabaseSessionService.

    Subclasses ADK's ``DatabaseSessionService`` to inject encrypted
    SQLAlchemy models via ``_get_schema_classes()`` and
    ``_prepare_tables()``. All CRUD methods (``create_session``,
    ``get_session``, ``list_sessions``, ``delete_session``,
    ``append_event``) are inherited without modification.

    Attributes:
        db_engine (AsyncEngine): The SQLAlchemy async engine (inherited).

    Examples:
        Create a service with SQLite:

        ```python
        from adk_secure_sessions import FernetBackend, EncryptedSessionService

        backend = FernetBackend("my-secret-passphrase")
        service = EncryptedSessionService(
            db_url="sqlite+aiosqlite:///sessions.db",
            backend=backend,
        )
        session = await service.create_session(
            app_name="my-agent",
            user_id="user-123",
            state={"secret": "sensitive-data"},
        )
        ```
    """

    def __init__(
        self,
        db_url: str,
        backend: EncryptionBackend,
        **kwargs: Any,
    ) -> None:
        """Initialize the encrypted session service.

        Uses ``backend.sync_encrypt``, ``backend.sync_decrypt``, and
        ``backend.backend_id`` from the protocol to configure the
        ``EncryptedJSON`` TypeDecorator.

        Args:
            db_url: SQLAlchemy connection string (e.g.,
                ``"sqlite+aiosqlite:///sessions.db"``).
            backend: Any object conforming to ``EncryptionBackend`` protocol.

        Other Parameters:
            **kwargs: Additional keyword arguments passed to
                ``DatabaseSessionService.__init__``.

        Raises:
            ConfigurationError: If *backend* does not conform to
                ``EncryptionBackend``.
        """
        if not isinstance(backend, EncryptionBackend):
            msg = (
                f"backend must conform to EncryptionBackend protocol, "
                f"got {type(backend).__name__}"
            )
            raise ConfigurationError(msg)

        self._encrypted_json = EncryptedJSON(
            encrypt_fn=backend.sync_encrypt,
            decrypt_fn=backend.sync_decrypt,
            backend_id=backend.backend_id,
        )
        self._encrypted_base, self._encrypted_schema = create_encrypted_models(
            self._encrypted_json
        )

        super().__init__(db_url=db_url, **kwargs)

    def _get_schema_classes(self) -> _EncryptedSchemaClasses:  # type: ignore[override]
        """Return encrypted model classes for CRUD operations.

        Returns:
            Duck-typed schema classes with encrypted models.
        """
        return self._encrypted_schema

    async def _prepare_tables(self) -> None:
        """Create encrypted tables using custom DeclarativeBase metadata.

        Overrides the parent method to use our encrypted model metadata
        instead of ADK's built-in schema.
        """
        if self._tables_created:
            return

        async with self._table_creation_lock:
            if self._tables_created:
                return

            async with self.db_engine.begin() as conn:
                await conn.run_sync(self._encrypted_base.metadata.create_all)

            self._tables_created = True
