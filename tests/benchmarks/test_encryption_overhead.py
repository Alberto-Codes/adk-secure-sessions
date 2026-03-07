"""Encryption overhead benchmark for NFR1 validation.

Measures the relative overhead of encrypted vs. unencrypted session
round-trips to verify that encryption adds less than 20% to total
operation time.

Typical usage::

    uv run pytest tests/benchmarks/ -m benchmark -v

See Also:
    [`adk_secure_sessions.services.encrypted_session`][adk_secure_sessions.services.encrypted_session]:
    The encrypted session service under test.
"""

from __future__ import annotations

import json
import logging
import os
import statistics
import time
import uuid
import warnings

import aiosqlite
import pytest

from adk_secure_sessions import EncryptedSessionService

pytestmark = pytest.mark.benchmark

logger = logging.getLogger(__name__)

N_ITERATIONS = 20
"""Number of measurement iterations per benchmark path.

Set at 20 to balance statistical stability (enough samples for a
reliable median) against total benchmark runtime (~2s per path).
Derived from NFR1 validation requirement — the overhead measurement
must be repeatable across runs. Higher values increase precision but
slow CI feedback; lower values risk noisy medians on variable hardware.
"""

_OVERHEAD_THRESHOLD = 1.20
"""Maximum acceptable encrypted-vs-baseline overhead ratio.

NFR1 requires encryption overhead < 20% of total operation time.
Expressed as 1.20x multiplier: ``median_encrypted / median_baseline``
must stay below this value. Local runs assert hard failure; CI runs
emit a warning (hardware variance makes hard assertions unreliable
in shared runners).
"""


async def _baseline_round_trip(
    conn: aiosqlite.Connection,
    state: dict[str, object],
) -> None:
    """Execute a single unencrypted INSERT + SELECT round-trip.

    Args:
        conn: Raw aiosqlite connection with ``benchmark_baseline`` table.
        state: Session state dict to serialize and store.
    """
    row_id = uuid.uuid4().hex
    payload = json.dumps(state).encode()
    now = time.time()

    await conn.execute(
        "INSERT INTO benchmark_baseline (id, state, create_time) VALUES (?, ?, ?)",
        (row_id, payload, now),
    )
    await conn.commit()

    cursor = await conn.execute(
        "SELECT state FROM benchmark_baseline WHERE id = ?",
        (row_id,),
    )
    row = await cursor.fetchone()
    assert row is not None
    json.loads(row[0])

    await conn.execute(
        "DELETE FROM benchmark_baseline WHERE id = ?",
        (row_id,),
    )
    await conn.commit()


async def _encrypted_round_trip(
    service: EncryptedSessionService,
    state: dict[str, object],
) -> None:
    """Execute a single encrypted create + get + delete round-trip.

    Args:
        service: Initialized EncryptedSessionService instance.
        state: Session state dict to encrypt and store.
    """
    session = await service.create_session(
        app_name="benchmark",
        user_id="bench-user",
        state=state,
    )
    await service.get_session(
        app_name="benchmark",
        user_id="bench-user",
        session_id=session.id,
    )
    await service.delete_session(
        app_name="benchmark",
        user_id="bench-user",
        session_id=session.id,
    )


@pytest.mark.filterwarnings("default::UserWarning")
async def test_encryption_overhead(
    encrypted_service: EncryptedSessionService,
    baseline_conn: aiosqlite.Connection,
    benchmark_state: dict[str, object],
) -> None:
    """Verify encryption overhead is less than 20% of total operation time.

    Measures encrypted vs. unencrypted session round-trip times using
    ``time.perf_counter()`` over multiple iterations, comparing median
    values to compute relative overhead.

    The assertion mode depends on the ``CI`` environment variable:

    - **Local** (no ``CI`` env var): hard assertion failure if overhead
      exceeds 1.20x.
    - **CI** (``CI=true``): emits a warning but passes, since CI runner
      hardware performance varies.

    Examples:
        ```python
        # Run benchmark locally
        # uv run pytest tests/benchmarks/ -m benchmark -v
        ```
    """
    is_ci = os.environ.get("CI", "").lower() in ("true", "1", "yes")

    # --- Warm-up: exclude from measurement ---
    await _baseline_round_trip(baseline_conn, benchmark_state)
    await _encrypted_round_trip(encrypted_service, benchmark_state)

    # --- Measure baseline (unencrypted) ---
    baseline_times: list[float] = []
    for _ in range(N_ITERATIONS):
        start = time.perf_counter()
        await _baseline_round_trip(baseline_conn, benchmark_state)
        elapsed = time.perf_counter() - start
        baseline_times.append(elapsed)

    # --- Measure encrypted path ---
    encrypted_times: list[float] = []
    for _ in range(N_ITERATIONS):
        start = time.perf_counter()
        await _encrypted_round_trip(encrypted_service, benchmark_state)
        elapsed = time.perf_counter() - start
        encrypted_times.append(elapsed)

    # --- Compute overhead ---
    median_baseline = statistics.median(baseline_times)
    median_encrypted = statistics.median(encrypted_times)
    overhead = median_encrypted / median_baseline

    logger.info(
        "Benchmark results: baseline=%.4fs, encrypted=%.4fs, overhead=%.2fx",
        median_baseline,
        median_encrypted,
        overhead,
    )

    # --- Assert based on environment ---
    if overhead >= _OVERHEAD_THRESHOLD:
        msg = (
            f"Encryption overhead {overhead:.2f}x exceeds "
            f"{_OVERHEAD_THRESHOLD:.2f}x threshold "
            f"(baseline={median_baseline:.4f}s, encrypted={median_encrypted:.4f}s)"
        )
        if is_ci:
            warnings.warn(msg, stacklevel=1)
        else:
            pytest.fail(msg)
