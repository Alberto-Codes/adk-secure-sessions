"""Shared test fixtures for adk-secure-sessions.

Provides common fixtures used across unit and integration test suites,
including encryption backends, database paths, and service instances.

Performance note:
    Key fixtures use pre-generated Fernet keys to skip PBKDF2 derivation
    (480K iterations, ~0.5s per call). Only tests that explicitly validate
    passphrase-to-key derivation should construct FernetBackend from strings.

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
from cryptography.fernet import Fernet

from adk_secure_sessions import BACKEND_FERNET, EncryptedSessionService, FernetBackend

if TYPE_CHECKING:
    from pathlib import Path

# Pre-generated Fernet keys — valid base64url-encoded 32-byte keys that
# skip PBKDF2 derivation entirely in FernetBackend._resolve_key().
# Two distinct keys are provided for wrong-key / key-isolation tests.
TEST_FERNET_KEY_A: bytes = Fernet.generate_key()
TEST_FERNET_KEY_B: bytes = Fernet.generate_key()
assert TEST_FERNET_KEY_A != TEST_FERNET_KEY_B  # 2^-256 collision guard


@pytest.fixture(scope="session")
def fernet_key_bytes() -> bytes:
    """A pre-generated Fernet key for the entire test session.

    Returns a valid Fernet key (base64url-encoded 32-byte key) that
    bypasses PBKDF2 derivation in FernetBackend. This fixture is
    session-scoped — the key is generated once and reused across all
    tests.

    Examples:
        ```python
        def test_with_key(fernet_key_bytes):
            backend = FernetBackend(key=fernet_key_bytes)
            assert backend is not None
        ```
    """
    return TEST_FERNET_KEY_A


@pytest.fixture(scope="session")
def alt_fernet_key_bytes() -> bytes:
    """A second pre-generated Fernet key for wrong-key tests.

    Guaranteed different from ``fernet_key_bytes``. Session-scoped.
    """
    return TEST_FERNET_KEY_B


@pytest.fixture
def fernet_backend(fernet_key_bytes: bytes) -> FernetBackend:
    """A fresh FernetBackend instance with a pre-generated Fernet key.

    Uses a session-scoped pre-generated key to skip PBKDF2 derivation.

    Examples:
        ```python
        async def test_encrypt(fernet_backend):
            ciphertext = await fernet_backend.encrypt(b"hello")
            assert ciphertext != b"hello"
        ```
    """
    return FernetBackend(fernet_key_bytes)


@pytest.fixture
def alt_fernet_backend(alt_fernet_key_bytes: bytes) -> FernetBackend:
    """A FernetBackend with a different key for wrong-key tests.

    Uses ``alt_fernet_key_bytes`` — guaranteed different from
    ``fernet_backend``.
    """
    return FernetBackend(alt_fernet_key_bytes)


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
