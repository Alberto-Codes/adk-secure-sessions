"""Tests for FernetBackend encryption backend."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from adk_secure_sessions import (
    ConfigurationError,
    DecryptionError,
    EncryptionBackend,
    FernetBackend,
    SecureSessionError,
)

# Pre-generated Fernet keys — skip PBKDF2 derivation in tests that don't
# need to validate passphrase-to-key conversion. Tests in TestFlexibleKeyInput
# intentionally use string/bytes passphrases to exercise the derivation path.
_KEY_A = Fernet.generate_key()
_KEY_B = Fernet.generate_key()

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# US1: Encrypt and Decrypt Round-Trip
# ---------------------------------------------------------------------------


class TestEncryptDecryptRoundTrip:
    """User Story 1: encrypt/decrypt round-trip."""

    async def test_round_trip(self) -> None:
        """T005: Encrypt then decrypt returns original plaintext."""
        backend = FernetBackend(key=_KEY_A)
        plaintext = b"hello, world"

        ciphertext = await backend.encrypt(plaintext)
        result = await backend.decrypt(ciphertext)

        assert result == plaintext

    async def test_non_deterministic_ciphertext(self) -> None:
        """T006: Same plaintext produces different ciphertext each time."""
        backend = FernetBackend(key=_KEY_A)
        plaintext = b"same input"

        ct1 = await backend.encrypt(plaintext)
        ct2 = await backend.encrypt(plaintext)

        assert ct1 != ct2

    async def test_empty_bytes_round_trip(self) -> None:
        """T007: Empty bytes can be encrypted and decrypted."""
        backend = FernetBackend(key=_KEY_A)

        ciphertext = await backend.encrypt(b"")
        result = await backend.decrypt(ciphertext)

        assert result == b""


# ---------------------------------------------------------------------------
# US2: Wrong Key Fails Decryption
# ---------------------------------------------------------------------------


class TestWrongKeyDecryption:
    """User Story 2: decryption failures raise DecryptionError."""

    async def test_wrong_key_raises_decryption_error(self) -> None:
        """T010: Decrypting with wrong key raises DecryptionError."""
        backend_a = FernetBackend(key=_KEY_A)
        backend_b = FernetBackend(key=_KEY_B)

        ciphertext = await backend_a.encrypt(b"secret")

        with pytest.raises(DecryptionError):
            await backend_b.decrypt(ciphertext)

    async def test_tampered_ciphertext_raises_decryption_error(self) -> None:
        """T011: Tampered ciphertext raises DecryptionError."""
        backend = FernetBackend(key=_KEY_A)
        ciphertext = await backend.encrypt(b"data")

        tampered = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])

        with pytest.raises(DecryptionError):
            await backend.decrypt(tampered)

    async def test_malformed_ciphertext_raises_decryption_error(self) -> None:
        """T012: Malformed/truncated ciphertext raises DecryptionError."""
        backend = FernetBackend(key=_KEY_A)

        with pytest.raises(DecryptionError):
            await backend.decrypt(b"not-valid-fernet-token")

    async def test_error_message_excludes_key_material(self) -> None:
        """T013: Error message does not contain key material."""
        backend_a = FernetBackend(key=_KEY_A)
        backend_b = FernetBackend(key=_KEY_B)

        ciphertext = await backend_a.encrypt(b"data")

        with pytest.raises(DecryptionError, match="Decryption failed") as exc_info:
            await backend_b.decrypt(ciphertext)

        error_msg = str(exc_info.value)
        assert _KEY_A.decode() not in error_msg
        assert _KEY_B.decode() not in error_msg


# ---------------------------------------------------------------------------
# US3: Flexible Key Input
# ---------------------------------------------------------------------------


class TestFlexibleKeyInput:
    """User Story 3: string, bytes, and Fernet key initialization."""

    async def test_string_key_round_trip(self) -> None:
        """T015: String key initialization produces working backend."""
        backend = FernetBackend(key="a-string-passphrase")

        ciphertext = await backend.encrypt(b"payload")
        result = await backend.decrypt(ciphertext)

        assert result == b"payload"

    async def test_bytes_key_round_trip(self) -> None:
        """T016: Bytes key initialization produces working backend."""
        backend = FernetBackend(key=b"a-bytes-passphrase")

        ciphertext = await backend.encrypt(b"payload")
        result = await backend.decrypt(ciphertext)

        assert result == b"payload"

    async def test_fernet_key_passthrough(self) -> None:
        """T017: Valid Fernet key is used directly without derivation."""
        fernet_key = Fernet.generate_key()
        backend = FernetBackend(key=fernet_key)

        # Verify it works
        ciphertext = await backend.encrypt(b"test")
        result = await backend.decrypt(ciphertext)
        assert result == b"test"

        # Verify it uses the key directly — a second backend with same
        # key should decrypt successfully
        backend2 = FernetBackend(key=fernet_key)
        result2 = await backend2.decrypt(ciphertext)
        assert result2 == b"test"

    def test_empty_string_key_raises_configuration_error(self) -> None:
        """T018: Empty string key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="must not be empty"):
            FernetBackend(key="")

    def test_empty_bytes_key_raises_configuration_error(self) -> None:
        """T018b: Empty bytes key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="must not be empty"):
            FernetBackend(key=b"")


# ---------------------------------------------------------------------------
# Key Derivation Stability (PBKDF2 constant pinning)
# ---------------------------------------------------------------------------


class TestKeyDerivationStability:
    """Pin PBKDF2 output to catch accidental changes to derivation constants.

    If ``_PBKDF2_ITERATIONS``, ``_PBKDF2_SALT``, or the hash algorithm change,
    all data encrypted with previously derived keys becomes permanently
    unreadable.  These tests fail fast when any constant drifts.
    """

    async def test_passphrase_derives_stable_key(self) -> None:
        """Derived key matches independent computation with pinned constants."""
        import base64
        import hashlib

        # Independently derive a key using the documented constants.
        reference_key = base64.urlsafe_b64encode(
            hashlib.pbkdf2_hmac(
                "sha256",
                b"test-pinning-passphrase",
                b"adk-secure-sessions-fernet-v1",  # _PBKDF2_SALT
                480_000,  # _PBKDF2_ITERATIONS
            )
        )

        # Encrypt with the reference key directly via cryptography.fernet
        reference_fernet = Fernet(reference_key)
        ciphertext = reference_fernet.encrypt(b"stability-check")

        # FernetBackend with the same passphrase must derive the same key
        backend = FernetBackend(key="test-pinning-passphrase")
        result = await backend.decrypt(ciphertext)

        assert result == b"stability-check"

    async def test_fernet_key_passthrough_interop(self) -> None:
        """Pre-generated Fernet key works interchangeably with raw Fernet.

        Guards against ``_resolve_key`` regressions that would route
        valid Fernet keys through PBKDF2 derivation.  If passthrough
        breaks, data encrypted by this library becomes unreadable by
        standard Fernet tools and vice versa.
        """
        fernet_key = Fernet.generate_key()
        raw_fernet = Fernet(fernet_key)
        backend = FernetBackend(key=fernet_key)

        # Direction 1: raw Fernet encrypt → FernetBackend decrypt
        raw_ciphertext = raw_fernet.encrypt(b"interop-check")
        result = await backend.decrypt(raw_ciphertext)
        assert result == b"interop-check"

        # Direction 2: FernetBackend encrypt → raw Fernet decrypt
        backend_ciphertext = await backend.encrypt(b"reverse-check")
        result2 = raw_fernet.decrypt(backend_ciphertext)
        assert result2 == b"reverse-check"


# ---------------------------------------------------------------------------
# Polish: Protocol Conformance and Type Guards
# ---------------------------------------------------------------------------


class TestPolish:
    """Cross-cutting concerns: protocol conformance, type guards."""

    def test_protocol_conformance(self) -> None:
        """T020: FernetBackend passes EncryptionBackend isinstance check."""
        backend = FernetBackend(key=_KEY_A)
        assert isinstance(backend, EncryptionBackend)

    async def test_non_bytes_plaintext_raises_type_error(self) -> None:
        """T021: Non-bytes plaintext raises TypeError."""
        backend = FernetBackend(key=_KEY_A)

        with pytest.raises(TypeError, match="plaintext must be bytes"):
            await backend.encrypt("not bytes")  # type: ignore[arg-type]

    async def test_non_bytes_ciphertext_raises_type_error(self) -> None:
        """Non-bytes ciphertext raises TypeError."""
        backend = FernetBackend(key=_KEY_A)

        with pytest.raises(TypeError, match="ciphertext must be bytes"):
            await backend.decrypt("not bytes")  # type: ignore[arg-type]

    def test_non_str_bytes_key_raises_configuration_error(self) -> None:
        """Key that is neither str nor bytes raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="key must be str or bytes"):
            FernetBackend(key=12345)  # type: ignore[arg-type]

    def test_key_validation_errors_do_not_contain_key_material(self) -> None:
        """Error messages from key validation never include the key value."""
        with pytest.raises(ConfigurationError) as exc_info:
            FernetBackend(key=12345)  # type: ignore[arg-type]
        assert "12345" not in str(exc_info.value)

    def test_decryption_error_inherits_secure_session_error(self) -> None:
        """DecryptionError is a SecureSessionError."""
        assert issubclass(DecryptionError, SecureSessionError)
