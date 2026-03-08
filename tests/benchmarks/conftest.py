"""Benchmark-specific fixtures for encryption overhead tests.

Provides payloads at multiple sizes, baseline database connections,
and backend fixtures needed by the encryption overhead benchmarks.

Typical usage::

    async def test_benchmark(benchmark_payloads, baseline_conn):
        # benchmark_payloads is a dict mapping size labels to state dicts
        # baseline_conn is a raw aiosqlite connection
        ...

See Also:
    [`tests.conftest`][tests.conftest]: Shared fixtures (fernet_backend, db_path, etc.).
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import aiosqlite
import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from adk_secure_sessions import AesGcmBackend, EncryptedSessionService

if TYPE_CHECKING:
    from pathlib import Path

_BASELINE_SCHEMA = """\
CREATE TABLE IF NOT EXISTS benchmark_baseline (
    id TEXT PRIMARY KEY,
    state BLOB NOT NULL,
    create_time REAL NOT NULL
);
"""

_PAYLOAD_SIZE_BOUNDS: dict[str, int] = {
    "empty": 10,
    "1KB": 1200,
    "10KB": 11000,
    "100KB": 110000,
}
"""Upper bounds (in bytes) for each benchmark payload size tier.

Each bound includes a small margin above the target size to
accommodate JSON serialization overhead (keys, quotes, commas).
The fixtures assert serialized size stays within these bounds.
"""


def _make_payload_empty() -> dict[str, object]:
    """Generate an empty dict payload."""
    return {}


def _make_payload_1kb() -> dict[str, object]:
    """Generate a ~1KB session state dict.

    Contains a small user profile and a handful of conversation
    entries to reach approximately 1KB when JSON-serialized.
    """
    return {
        "user_profile": {"name": "Test User", "email": "test@example.com"},
        "conversation_history": [
            {"role": "user", "content": f"Message {i}" * 5} for i in range(5)
        ],
        "metadata": {f"key_{i}": f"value_{i}" for i in range(10)},
    }


def _make_payload_10kb() -> dict[str, object]:
    """Generate a ~10KB session state dict.

    Represents a realistic ADK session payload with user profile,
    conversation history, and metadata.
    """
    return {
        "user_profile": {"name": "Test User", "email": "test@example.com"},
        "conversation_history": [
            {"role": "user", "content": f"Message {i}" * 10} for i in range(30)
        ],
        "metadata": {f"key_{i}": f"value_{i}" * 10 for i in range(50)},
    }


def _make_payload_100kb() -> dict[str, object]:
    """Generate a ~100KB session state dict.

    Extended conversation history and metadata to stress-test
    serialization and encryption overhead at 10x realistic size.
    """
    return {
        "user_profile": {
            "name": "Test User",
            "email": "test@example.com",
            "preferences": {f"pref_{i}": f"val_{i}" * 5 for i in range(20)},
        },
        "conversation_history": [
            {"role": "user", "content": f"Message {i} " * 30} for i in range(150)
        ],
        "metadata": {f"key_{i}": f"value_{i}" * 20 for i in range(200)},
    }


_PAYLOAD_FACTORIES: dict[str, object] = {
    "empty": _make_payload_empty,
    "1KB": _make_payload_1kb,
    "10KB": _make_payload_10kb,
    "100KB": _make_payload_100kb,
}
"""Factory functions for each payload size tier.

Each factory returns a dict[str, object] representing session state.
Size bounds are validated by the ``benchmark_payloads`` fixture.
"""


@pytest.fixture
def benchmark_payloads() -> dict[str, dict[str, object]]:
    """Payload dicts for all benchmark size tiers with size validation.

    Returns a dict mapping size labels (``"empty"``, ``"1KB"``,
    ``"10KB"``, ``"100KB"``) to session state dicts. Each payload's
    serialized size is validated against ``_PAYLOAD_SIZE_BOUNDS``.

    Examples:
        ```python
        def test_sizes(benchmark_payloads):
            assert len(benchmark_payloads) == 4
            assert "10KB" in benchmark_payloads
        ```
    """
    payloads: dict[str, dict[str, object]] = {}
    for label, factory in _PAYLOAD_FACTORIES.items():
        state = factory()
        serialized_size = len(json.dumps(state).encode())
        bound = _PAYLOAD_SIZE_BOUNDS[label]
        assert serialized_size <= bound, (
            f"Benchmark payload '{label}' is {serialized_size}B, exceeds {bound}B bound"
        )
        payloads[label] = state
    return payloads


@pytest.fixture
def benchmark_state() -> dict[str, object]:
    """A ~10KB session state dict representative of real session data.

    Contains user profile, conversation history, and metadata keys
    to simulate a realistic ADK session payload. Preserved for
    backward compatibility with existing benchmark tests.

    Examples:
        ```python
        def test_payload_size(benchmark_state):
            import json

            size = len(json.dumps(benchmark_state).encode())
            assert size <= 11000
        ```
    """
    return _make_payload_10kb()


@pytest.fixture
def aesgcm_backend() -> AesGcmBackend:
    """An AES-256-GCM backend instance for benchmarks.

    Examples:
        ```python
        async def test_encrypt(aesgcm_backend):
            ct = await aesgcm_backend.encrypt(b"hello")
            assert ct != b"hello"
        ```
    """
    key = AESGCM.generate_key(bit_length=256)
    return AesGcmBackend(key=key)


@pytest.fixture
async def aesgcm_encrypted_service(
    db_url: str, aesgcm_backend: AesGcmBackend
) -> AsyncGenerator[EncryptedSessionService, None]:
    """An EncryptedSessionService backed by AES-256-GCM for benchmarks.

    Examples:
        ```python
        async def test_create(aesgcm_encrypted_service):
            session = await aesgcm_encrypted_service.create_session(
                app_name="bench",
                user_id="user-1",
            )
            assert session.id is not None
        ```
    """
    svc = EncryptedSessionService(
        db_url=db_url,
        backend=aesgcm_backend,
    )
    yield svc
    await svc.close()


@pytest.fixture
def baseline_db_path(tmp_path: Path) -> str:
    """A separate database path for the unencrypted baseline measurement.

    Uses a distinct file from the encrypted service's database to
    prevent table collisions and isolate I/O.

    Examples:
        ```python
        async def test_baseline(baseline_db_path):
            import aiosqlite

            async with aiosqlite.connect(baseline_db_path) as conn:
                ...
        ```
    """
    return str(tmp_path / "baseline.db")


@pytest.fixture
async def baseline_conn(
    baseline_db_path: str,
) -> AsyncGenerator[aiosqlite.Connection, None]:
    """A raw aiosqlite connection with a minimal baseline schema.

    Creates the ``benchmark_baseline`` table -- a stripped-down schema
    with only ``id``, ``state``, and ``create_time`` columns. This
    isolates the pure serialization + I/O cost for comparison against
    the encrypted path.

    Examples:
        ```python
        async def test_insert(baseline_conn):
            await baseline_conn.execute(
                "INSERT INTO benchmark_baseline VALUES (?, ?, ?)",
                ("id-1", b"data", 1.0),
            )
        ```
    """
    conn = await aiosqlite.connect(baseline_db_path)
    await conn.executescript(_BASELINE_SCHEMA)
    yield conn
    await conn.close()


def get_backend_fixtures() -> list[str]:
    """Return the list of backend fixture names for parameterization.

    Used by benchmark tests to parameterize across backends.
    """
    return ["fernet_backend", "aesgcm_backend"]


def get_service_fixtures() -> list[str]:
    """Return the list of service fixture names for parameterization.

    Used by round-trip benchmark tests to parameterize across backends.
    """
    return ["encrypted_service", "aesgcm_encrypted_service"]
