"""Benchmark-specific fixtures for encryption overhead tests.

Provides the payload, baseline database connection, and helpers
needed by the encryption overhead benchmark.

Typical usage::

    async def test_benchmark(benchmark_state, baseline_conn):
        # benchmark_state is a ~10KB dict payload
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

if TYPE_CHECKING:
    from pathlib import Path

_BASELINE_SCHEMA = """\
CREATE TABLE IF NOT EXISTS benchmark_baseline (
    id TEXT PRIMARY KEY,
    state BLOB NOT NULL,
    create_time REAL NOT NULL
);
"""

_TARGET_SIZE_BYTES = 10240


@pytest.fixture
def benchmark_state() -> dict[str, object]:
    """A ~10KB session state dict representative of real session data.

    Contains user profile, conversation history, and metadata keys
    to simulate a realistic ADK session payload.

    Examples:
        ```python
        def test_payload_size(benchmark_state):
            import json

            size = len(json.dumps(benchmark_state).encode())
            assert size <= 10240
        ```
    """
    state: dict[str, object] = {
        "user_profile": {"name": "Test User", "email": "test@example.com"},
        "conversation_history": [
            {"role": "user", "content": f"Message {i}" * 10} for i in range(30)
        ],
        "metadata": {f"key_{i}": f"value_{i}" * 10 for i in range(50)},
    }
    serialized_size = len(json.dumps(state).encode())
    assert serialized_size <= _TARGET_SIZE_BYTES, (
        f"Benchmark payload {serialized_size}B exceeds {_TARGET_SIZE_BYTES}B target"
    )
    return state


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

    Creates the ``benchmark_baseline`` table — a stripped-down schema
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
