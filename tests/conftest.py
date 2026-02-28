"""Shared test fixtures for adk-secure-sessions.

Provides common fixtures used across unit and integration test suites,
including encryption backends, database paths, and service instances.

Typical usage::

    async def test_encrypt_decrypt(fernet_backend, db_path):
        # fernet_backend is a FernetBackend instance
        # db_path is a temporary SQLite database path
        ...

See Also:
    [`FernetBackend`][adk_secure_sessions.backends.fernet.FernetBackend]
    [`EncryptedSessionService`][adk_secure_sessions.services.encrypted_session.EncryptedSessionService]
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest

from adk_secure_sessions import BACKEND_FERNET, EncryptedSessionService, FernetBackend

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def encryption_key() -> str:
    """A valid encryption key string for testing.

    Returns a consistent test passphrase suitable for creating
    encryption backends in tests.

    Examples:
        ```python
        async def test_with_key(encryption_key):
            backend = FernetBackend(encryption_key)
            assert backend is not None
        ```
    """
    return "test-passphrase-for-unit-tests"


@pytest.fixture
def fernet_backend(encryption_key: str) -> FernetBackend:
    """A fresh FernetBackend instance with a test passphrase.

    Examples:
        ```python
        async def test_encrypt(fernet_backend):
            ciphertext = await fernet_backend.encrypt(b"hello")
            assert ciphertext != b"hello"
        ```
    """
    return FernetBackend(encryption_key)


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """A temporary database file path for testing.

    Creates a path within pytest's ``tmp_path`` directory.
    The database file is not created until first use.

    Examples:
        ```python
        async def test_with_db(db_path):
            import aiosqlite

            async with aiosqlite.connect(db_path) as conn:
                ...
        ```
    """
    return str(tmp_path / "test_sessions.db")


@pytest.fixture
async def encrypted_service(
    db_path: str, fernet_backend: FernetBackend
) -> AsyncGenerator[EncryptedSessionService, None]:
    """An initialized EncryptedSessionService with cleanup.

    Creates a service backed by a real FernetBackend and temporary
    SQLite database. Initializes the database schema before yielding
    and closes the connection after the test completes.

    Note: This is an integration-grade fixture (real backend + real DB).
    Unit tests requiring isolation should mock the backend or DB instead.

    Examples:
        ```python
        async def test_create(encrypted_service):
            session = await encrypted_service.create_session(
                app_name="test",
                user_id="user-1",
            )
            assert session.id is not None
        ```
    """
    svc = EncryptedSessionService(
        db_path=db_path,
        backend=fernet_backend,
        backend_id=BACKEND_FERNET,
    )
    await svc._init_db()
    yield svc
    await svc.close()
