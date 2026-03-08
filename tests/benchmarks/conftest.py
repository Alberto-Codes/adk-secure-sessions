"""Benchmark-specific fixtures for encryption overhead tests.

Provides payloads at multiple sizes, a no-op backend for isolating
encryption cost, and backend fixtures needed by the encryption
overhead benchmarks.

Typical usage::

    async def test_benchmark(benchmark_payloads, noop_encrypted_service):
        # benchmark_payloads is a dict mapping size labels to state dicts
        # noop_encrypted_service is an EncryptedSessionService with no-op crypto
        ...

See Also:
    [`tests.conftest`][tests.conftest]: Shared fixtures (fernet_backend, db_path, etc.).
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Callable

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from adk_secure_sessions import AesGcmBackend, EncryptedSessionService
from adk_secure_sessions.serialization import BACKEND_REGISTRY

_NOOP_BACKEND_ID: int = 0xFF
"""Backend identifier for the no-op (passthrough) benchmark backend.

Registered in BACKEND_REGISTRY at fixture setup time so the envelope
parser accepts it. Used as the baseline for round-trip overhead tests
to isolate encryption cost from ORM/service layer overhead.
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

_PAYLOAD_SIZE_LOWER_BOUNDS: dict[str, int] = {
    "empty": 0,
    "1KB": 500,
    "10KB": 5000,
    "100KB": 50000,
}
"""Lower bounds (in bytes) for each benchmark payload size tier.

Prevents silent regressions where a payload generator refactor
accidentally produces payloads much smaller than intended.
"""


class NoOpBackend:
    """Passthrough backend that performs no encryption.

    Satisfies the ``EncryptionBackend`` protocol but returns plaintext
    unchanged. Used as the benchmark baseline to isolate encryption
    cost: comparing ``EncryptedSessionService(real_backend)`` against
    ``EncryptedSessionService(NoOpBackend())`` measures only the
    crypto overhead, not ORM/service-layer differences.
    """

    @property
    def backend_id(self) -> int:
        """Return the no-op backend identifier byte."""
        return _NOOP_BACKEND_ID

    def sync_encrypt(self, plaintext: bytes) -> bytes:
        """Return plaintext unchanged (no encryption)."""
        return plaintext

    def sync_decrypt(self, ciphertext: bytes) -> bytes:
        """Return ciphertext unchanged (no decryption)."""
        return ciphertext

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Return plaintext unchanged (async no-op)."""
        return plaintext

    async def decrypt(self, ciphertext: bytes) -> bytes:
        """Return ciphertext unchanged (async no-op)."""
        return ciphertext


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


_PAYLOAD_FACTORIES: dict[str, Callable[[], dict[str, object]]] = {
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
        upper = _PAYLOAD_SIZE_BOUNDS[label]
        lower = _PAYLOAD_SIZE_LOWER_BOUNDS[label]
        assert serialized_size >= lower, (
            f"Benchmark payload '{label}' is {serialized_size}B, "
            f"below {lower}B lower bound"
        )
        assert serialized_size <= upper, (
            f"Benchmark payload '{label}' is {serialized_size}B, "
            f"exceeds {upper}B upper bound"
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


@pytest.fixture(autouse=True)
def _register_noop_backend() -> None:
    """Register the NoOpBackend ID in BACKEND_REGISTRY for envelope parsing.

    Automatically applied to all benchmark tests. Registers the no-op
    backend ID so ``_parse_envelope()`` accepts envelopes written by
    the NoOpBackend. Cleans up after the test to avoid polluting the
    global registry.
    """
    BACKEND_REGISTRY[_NOOP_BACKEND_ID] = "NoOp"
    yield  # type: ignore[misc]
    BACKEND_REGISTRY.pop(_NOOP_BACKEND_ID, None)


@pytest.fixture
def noop_backend() -> NoOpBackend:
    """A no-op (passthrough) backend for baseline benchmarks.

    Examples:
        ```python
        def test_noop(noop_backend):
            assert noop_backend.sync_encrypt(b"x") == b"x"
        ```
    """
    return NoOpBackend()


@pytest.fixture
async def noop_encrypted_service(
    db_url: str, noop_backend: NoOpBackend
) -> AsyncGenerator[EncryptedSessionService, None]:
    """An EncryptedSessionService with no-op crypto for baseline measurement.

    Uses the same ORM/service stack as the encrypted services but
    performs no actual encryption. Shares the same ``db_url`` to
    eliminate SQLite I/O variance between separate database files.
    Session isolation is achieved via distinct ``user_id`` values
    in the round-trip helper (``"bench-noop"`` vs ``"bench-user"``).

    The overhead ratio ``encrypted_service / noop_encrypted_service``
    isolates the pure encryption cost.

    Examples:
        ```python
        async def test_baseline(noop_encrypted_service):
            session = await noop_encrypted_service.create_session(
                app_name="bench",
                user_id="bench-noop",
            )
            assert session.id is not None
        ```
    """
    svc = EncryptedSessionService(
        db_url=db_url,
        backend=noop_backend,
    )
    yield svc
    await svc.close()


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
