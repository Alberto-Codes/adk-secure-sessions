"""Encryption overhead benchmark for NFR1 validation.

Measures the relative overhead of encrypted vs. unencrypted session
round-trips to verify that encryption adds less than 20% to total
operation time. Supports both Fernet and AES-256-GCM backends across
multiple payload sizes.

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
from adk_secure_sessions.protocols import EncryptionBackend

pytestmark = pytest.mark.benchmark

logger = logging.getLogger(__name__)

N_ITERATIONS = 20
"""Number of measurement iterations per benchmark path.

Set at 20 to balance statistical stability (enough samples for a
reliable median) against total benchmark runtime (~2s per path).
Derived from NFR1 validation requirement -- the overhead measurement
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

PAYLOAD_SIZES = ["empty", "1KB", "10KB", "100KB"]
"""Payload size labels for parameterized benchmark tests.

Covers the full range from empty dicts (baseline overhead) to
100KB (10x realistic session size -- sufficient upper bound).
1MB is explicitly out of scope.
"""

BACKEND_LABELS = ["fernet", "aesgcm"]
"""Backend labels for parameterized benchmark tests."""


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


def _measure_overhead(
    baseline_times: list[float],
    encrypted_times: list[float],
) -> tuple[float, float, float]:
    """Compute median times and overhead ratio.

    Args:
        baseline_times: Measured baseline durations.
        encrypted_times: Measured encrypted durations.

    Returns:
        Tuple of (median_baseline, median_encrypted, overhead_ratio).
    """
    median_baseline = statistics.median(baseline_times)
    median_encrypted = statistics.median(encrypted_times)
    overhead = median_encrypted / median_baseline
    return median_baseline, median_encrypted, overhead


def _assert_overhead(
    overhead: float,
    median_baseline: float,
    median_encrypted: float,
    *,
    label: str,
) -> None:
    """Assert overhead is within threshold, CI-aware.

    Args:
        overhead: Computed overhead ratio.
        median_baseline: Median baseline time.
        median_encrypted: Median encrypted time.
        label: Description for log/error messages.
    """
    is_ci = os.environ.get("CI", "").lower() in ("true", "1", "yes")

    logger.info(
        "Benchmark [%s]: baseline=%.4fs, encrypted=%.4fs, overhead=%.2fx",
        label,
        median_baseline,
        median_encrypted,
        overhead,
    )

    if overhead >= _OVERHEAD_THRESHOLD:
        msg = (
            f"Encryption overhead {overhead:.2f}x exceeds "
            f"{_OVERHEAD_THRESHOLD:.2f}x threshold for {label} "
            f"(baseline={median_baseline:.4f}s, encrypted={median_encrypted:.4f}s)"
        )
        if is_ci:
            warnings.warn(msg, stacklevel=2)
        else:
            pytest.fail(msg)


# ---------------------------------------------------------------------------
# Category A: Round-Trip Overhead Tests (Assertive, < 1.20x)
# ---------------------------------------------------------------------------


@pytest.mark.filterwarnings("default::UserWarning")
@pytest.mark.parametrize("payload_size", PAYLOAD_SIZES)
async def test_fernet_round_trip_overhead(
    encrypted_service: EncryptedSessionService,
    baseline_conn: aiosqlite.Connection,
    benchmark_payloads: dict[str, dict[str, object]],
    payload_size: str,
) -> None:
    """Verify Fernet round-trip overhead is below 20% for each payload size.

    Parameterized over empty, 1KB, 10KB, and 100KB payloads.
    """
    state = benchmark_payloads[payload_size]
    label = f"fernet/{payload_size}"

    # Warm-up
    await _baseline_round_trip(baseline_conn, state)
    await _encrypted_round_trip(encrypted_service, state)

    baseline_times: list[float] = []
    for _ in range(N_ITERATIONS):
        start = time.perf_counter()
        await _baseline_round_trip(baseline_conn, state)
        baseline_times.append(time.perf_counter() - start)

    encrypted_times: list[float] = []
    for _ in range(N_ITERATIONS):
        start = time.perf_counter()
        await _encrypted_round_trip(encrypted_service, state)
        encrypted_times.append(time.perf_counter() - start)

    median_baseline, median_encrypted, overhead = _measure_overhead(
        baseline_times, encrypted_times
    )
    _assert_overhead(overhead, median_baseline, median_encrypted, label=label)


@pytest.mark.filterwarnings("default::UserWarning")
@pytest.mark.parametrize("payload_size", PAYLOAD_SIZES)
async def test_aesgcm_round_trip_overhead(
    aesgcm_encrypted_service: EncryptedSessionService,
    baseline_conn: aiosqlite.Connection,
    benchmark_payloads: dict[str, dict[str, object]],
    payload_size: str,
) -> None:
    """Verify AES-256-GCM round-trip overhead is below 20% for each payload size.

    Parameterized over empty, 1KB, 10KB, and 100KB payloads.
    """
    state = benchmark_payloads[payload_size]
    label = f"aesgcm/{payload_size}"

    # Warm-up
    await _baseline_round_trip(baseline_conn, state)
    await _encrypted_round_trip(aesgcm_encrypted_service, state)

    baseline_times: list[float] = []
    for _ in range(N_ITERATIONS):
        start = time.perf_counter()
        await _baseline_round_trip(baseline_conn, state)
        baseline_times.append(time.perf_counter() - start)

    encrypted_times: list[float] = []
    for _ in range(N_ITERATIONS):
        start = time.perf_counter()
        await _encrypted_round_trip(aesgcm_encrypted_service, state)
        encrypted_times.append(time.perf_counter() - start)

    median_baseline, median_encrypted, overhead = _measure_overhead(
        baseline_times, encrypted_times
    )
    _assert_overhead(overhead, median_baseline, median_encrypted, label=label)


# ---------------------------------------------------------------------------
# Category B: Per-Operation Tests (Informational, No Assertion)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload_size", PAYLOAD_SIZES)
async def test_encrypt_only(
    fernet_backend: EncryptionBackend,
    aesgcm_backend: EncryptionBackend,
    benchmark_payloads: dict[str, dict[str, object]],
    payload_size: str,
) -> None:
    """Measure raw encrypt cost across backends and payload sizes.

    Informational only -- no threshold assertion. Logs timing data
    for the documentation page.
    """
    state = benchmark_payloads[payload_size]
    payload = json.dumps(state).encode()

    for backend, name in [(fernet_backend, "fernet"), (aesgcm_backend, "aesgcm")]:
        # Warm-up
        await backend.encrypt(payload)

        times: list[float] = []
        for _ in range(N_ITERATIONS):
            start = time.perf_counter()
            await backend.encrypt(payload)
            times.append(time.perf_counter() - start)

        median_time = statistics.median(times)
        logger.info(
            "Encrypt-only [%s/%s]: median=%.6fs",
            name,
            payload_size,
            median_time,
        )


@pytest.mark.parametrize("payload_size", PAYLOAD_SIZES)
async def test_decrypt_only(
    fernet_backend: EncryptionBackend,
    aesgcm_backend: EncryptionBackend,
    benchmark_payloads: dict[str, dict[str, object]],
    payload_size: str,
) -> None:
    """Measure raw decrypt cost across backends and payload sizes.

    Pre-encrypts data, then measures decrypt. Informational only --
    no threshold assertion. Logs timing data for documentation.
    """
    state = benchmark_payloads[payload_size]
    payload = json.dumps(state).encode()

    for backend, name in [(fernet_backend, "fernet"), (aesgcm_backend, "aesgcm")]:
        ciphertext = await backend.encrypt(payload)

        # Warm-up
        await backend.decrypt(ciphertext)

        times: list[float] = []
        for _ in range(N_ITERATIONS):
            start = time.perf_counter()
            await backend.decrypt(ciphertext)
            times.append(time.perf_counter() - start)

        median_time = statistics.median(times)
        logger.info(
            "Decrypt-only [%s/%s]: median=%.6fs",
            name,
            payload_size,
            median_time,
        )


async def test_backend_comparison(
    fernet_backend: EncryptionBackend,
    aesgcm_backend: EncryptionBackend,
    benchmark_payloads: dict[str, dict[str, object]],
) -> None:
    """Compare Fernet vs AES-256-GCM relative performance for all operations.

    Logs Fernet/AES-GCM timing ratios for each operation and size.
    These ratios are hardware-stable and suitable for documentation.
    Informational only -- no threshold assertion.
    """
    for payload_size in PAYLOAD_SIZES:
        state = benchmark_payloads[payload_size]
        payload = json.dumps(state).encode()

        for operation in ["encrypt", "decrypt"]:
            fernet_times: list[float] = []
            aesgcm_times: list[float] = []

            if operation == "encrypt":
                # Warm-up
                await fernet_backend.encrypt(payload)
                await aesgcm_backend.encrypt(payload)

                for _ in range(N_ITERATIONS):
                    start = time.perf_counter()
                    await fernet_backend.encrypt(payload)
                    fernet_times.append(time.perf_counter() - start)

                for _ in range(N_ITERATIONS):
                    start = time.perf_counter()
                    await aesgcm_backend.encrypt(payload)
                    aesgcm_times.append(time.perf_counter() - start)
            else:
                fernet_ct = await fernet_backend.encrypt(payload)
                aesgcm_ct = await aesgcm_backend.encrypt(payload)

                # Warm-up
                await fernet_backend.decrypt(fernet_ct)
                await aesgcm_backend.decrypt(aesgcm_ct)

                for _ in range(N_ITERATIONS):
                    start = time.perf_counter()
                    await fernet_backend.decrypt(fernet_ct)
                    fernet_times.append(time.perf_counter() - start)

                for _ in range(N_ITERATIONS):
                    start = time.perf_counter()
                    await aesgcm_backend.decrypt(aesgcm_ct)
                    aesgcm_times.append(time.perf_counter() - start)

            fernet_median = statistics.median(fernet_times)
            aesgcm_median = statistics.median(aesgcm_times)
            ratio = fernet_median / aesgcm_median if aesgcm_median > 0 else float("inf")

            logger.info(
                "Comparison [%s/%s]: fernet=%.6fs, aesgcm=%.6fs, fernet/aesgcm=%.2fx",
                operation,
                payload_size,
                fernet_median,
                aesgcm_median,
                ratio,
            )
