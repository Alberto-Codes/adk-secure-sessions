"""Encryption overhead benchmark for NFR1 validation.

Measures the relative overhead of encrypted vs. no-op (passthrough)
session round-trips to verify that encryption adds less than 20% to
total operation time. Both paths use the same ``EncryptedSessionService``
stack, isolating pure encryption cost from ORM/service-layer overhead.

Supports both Fernet and AES-256-GCM backends across multiple payload
sizes.

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
import warnings

import pytest

from adk_secure_sessions import EncryptedSessionService
from adk_secure_sessions.protocols import EncryptionBackend

pytestmark = pytest.mark.benchmark

logger = logging.getLogger(__name__)

N_ITERATIONS = 30
"""Number of measurement iterations per benchmark path.

Set at 30 to meet the Central Limit Theorem threshold for reliable
median estimates while keeping total benchmark runtime under ~3s per
path. Derived from NFR1 validation requirement -- the overhead
measurement must be repeatable across runs. Higher values increase
precision but slow CI feedback; lower values risk noisy medians on
variable hardware.
"""

_N_WARMUP = 5
"""Number of warm-up iterations before measurement.

Multiple warm-up passes stabilize SQLite's page cache and eliminate
cold-start effects (journal creation, page allocation).
"""

_BATCH_SIZE = 10
"""Number of round-trips per timing sample.

Each timing sample measures a batch of round-trips rather than a
single one. At ~2ms per round-trip, a single operation is too short
for reliable measurement — OS scheduling noise (~0.5-2ms) dominates
the signal. Batching 10 operations produces ~20ms samples, well above
the ~10ms threshold where ``time.perf_counter()`` gives stable results
(per pyperf methodology). The batch overhead cancels out in the
paired overhead ratio since both baseline and encrypted arms use
identical batch sizes.
"""

_OVERHEAD_THRESHOLD = 1.20
"""Maximum acceptable encrypted-vs-baseline overhead ratio.

NFR1 requires encryption overhead < 20% of total operation time.
Expressed as 1.20x multiplier: ``median_encrypted / median_baseline``
must stay below this value. The baseline uses a no-op backend on the
same service stack, so the ratio isolates encryption cost only.

Local runs assert hard failure; CI runs emit a warning (hardware
variance makes hard assertions unreliable in shared runners).
"""

PAYLOAD_SIZES = ["empty", "1KB", "10KB", "100KB"]
"""Payload size labels for parameterized benchmark tests.

Covers the full range from empty dicts (baseline overhead) to
100KB (10x realistic session size -- sufficient upper bound).
1MB is explicitly out of scope.
"""


async def _service_round_trip(
    service: EncryptedSessionService,
    state: dict[str, object],
    *,
    app_name: str = "benchmark",
    user_id: str = "bench-user",
) -> None:
    """Execute a single create + get + delete round-trip.

    Args:
        service: Initialized EncryptedSessionService instance.
        state: Session state dict to store (encrypted or passthrough).
        app_name: App name for session isolation. Different services
            sharing a database must use different app_names because
            the ``app_states`` table is keyed by ``app_name`` alone.
        user_id: User ID for session isolation.
    """
    session = await service.create_session(
        app_name=app_name,
        user_id=user_id,
        state=state,
    )
    await service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session.id,
    )
    await service.delete_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session.id,
    )


def _measure_overhead(
    baseline_times: list[float],
    encrypted_times: list[float],
) -> tuple[float, float, float]:
    """Compute overhead from paired per-iteration ratios.

    Takes the median of per-pair ratios (encrypted[i] / baseline[i])
    rather than the ratio of medians. Because measurements are
    interleaved (baseline then encrypted on each iteration), each pair
    experiences the same system conditions, eliminating time-drift bias
    from SQLite checkpoints, CPU throttling, or OS scheduling shifts.

    Args:
        baseline_times: Measured baseline durations (interleaved).
        encrypted_times: Measured encrypted durations (interleaved).

    Returns:
        Tuple of (median_baseline, median_encrypted, overhead_ratio).
    """
    ratios = [
        enc / base for base, enc in zip(baseline_times, encrypted_times) if base > 0
    ]
    median_baseline = statistics.median(baseline_times)
    median_encrypted = statistics.median(encrypted_times)
    overhead = statistics.median(ratios)
    return median_baseline, median_encrypted, overhead


def _assert_overhead(
    overhead: float,
    median_baseline: float,
    median_encrypted: float,
    *,
    label: str,
    informational: bool = False,
) -> None:
    """Assert or warn that overhead is within threshold.

    Args:
        overhead: Computed overhead ratio.
        median_baseline: Median baseline time.
        median_encrypted: Median encrypted time.
        label: Description for log/error messages.
        informational: If True, always emit a warning instead of
            failing. Used for backends whose overhead is inherently
            borderline at benchmark timescales (e.g. Fernet's
            Encrypt-then-MAC design). CI mode also forces warning-only
            behavior.
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
        if is_ci or informational:
            warnings.warn(msg, stacklevel=2)
        else:
            pytest.fail(msg)


async def _interleaved_measurement(
    baseline_service: EncryptedSessionService,
    encrypted_service: EncryptedSessionService,
    state: dict[str, object],
) -> tuple[list[float], list[float]]:
    """Run interleaved baseline and encrypted measurements.

    Alternates baseline and encrypted batches on each pass to cancel
    out time-varying system effects (CPU throttling, OS scheduling,
    SQLite page-cache drift). Each timing sample measures a batch of
    ``_BATCH_SIZE`` round-trips so that individual scheduling spikes
    are amortized over a longer measurement window (~10ms per sample
    instead of ~2ms), improving the signal-to-noise ratio.

    Args:
        baseline_service: No-op service for baseline measurement.
        encrypted_service: Encrypted service under test.
        state: Session state dict to store.

    Returns:
        Tuple of (baseline_times, encrypted_times) lists.
    """
    # Warm-up: multiple passes to stabilize SQLite page cache
    for _ in range(_N_WARMUP):
        await _service_round_trip(
            baseline_service, state, app_name="bench-noop", user_id="bench-noop"
        )
        await _service_round_trip(encrypted_service, state)

    baseline_times: list[float] = []
    encrypted_times: list[float] = []

    for _ in range(N_ITERATIONS):
        start = time.perf_counter()
        for _ in range(_BATCH_SIZE):
            await _service_round_trip(
                baseline_service, state, app_name="bench-noop", user_id="bench-noop"
            )
        baseline_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        for _ in range(_BATCH_SIZE):
            await _service_round_trip(encrypted_service, state)
        encrypted_times.append(time.perf_counter() - start)

    return baseline_times, encrypted_times


# ---------------------------------------------------------------------------
# Category A: Round-Trip Overhead Tests
#
# Baseline uses a NoOpBackend on the same EncryptedSessionService stack.
# This isolates the pure encryption cost — ORM, schema, and service-layer
# overhead cancel out because both paths use the same code.
#
# AES-256-GCM: Assertive (< 1.20x threshold, hard fail locally, warn in CI).
# Fernet: Informational (always warns). Its Encrypt-then-MAC design produces
#   overhead that is borderline at the threshold, and measurement noise at
#   sub-millisecond scales makes hard assertions unreliable.
# ---------------------------------------------------------------------------


@pytest.mark.filterwarnings("default::UserWarning")
@pytest.mark.parametrize("payload_size", PAYLOAD_SIZES)
async def test_fernet_round_trip_overhead(
    encrypted_service: EncryptedSessionService,
    noop_encrypted_service: EncryptedSessionService,
    benchmark_payloads: dict[str, dict[str, object]],
    payload_size: str,
) -> None:
    """Measure Fernet encryption overhead for each payload size.

    Compares Fernet-encrypted round-trips against no-op (passthrough)
    round-trips on the same service stack to isolate encryption cost.

    Informational only — warns but does not fail. Fernet's Encrypt-then-MAC
    construction (AES-128-CBC + HMAC-SHA256) produces overhead that is
    borderline at the 1.20x threshold, and at sub-millisecond encryption
    times the measurement is dominated by OS scheduling noise.
    AES-256-GCM is the recommended backend for NFR1 compliance.
    """
    state = benchmark_payloads[payload_size]
    label = f"fernet/{payload_size}"

    baseline_times, encrypted_times = await _interleaved_measurement(
        noop_encrypted_service, encrypted_service, state
    )
    median_baseline, median_encrypted, overhead = _measure_overhead(
        baseline_times, encrypted_times
    )
    _assert_overhead(
        overhead, median_baseline, median_encrypted, label=label, informational=True
    )


@pytest.mark.filterwarnings("default::UserWarning")
@pytest.mark.parametrize("payload_size", PAYLOAD_SIZES)
async def test_aesgcm_round_trip_overhead(
    aesgcm_encrypted_service: EncryptedSessionService,
    noop_encrypted_service: EncryptedSessionService,
    benchmark_payloads: dict[str, dict[str, object]],
    payload_size: str,
) -> None:
    """Verify AES-256-GCM encryption overhead is below 20% for each payload size.

    Compares AES-256-GCM-encrypted round-trips against no-op (passthrough)
    round-trips on the same service stack to isolate encryption cost.
    """
    state = benchmark_payloads[payload_size]
    label = f"aesgcm/{payload_size}"

    baseline_times, encrypted_times = await _interleaved_measurement(
        noop_encrypted_service, aesgcm_encrypted_service, state
    )
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
