"""Tests for FernetBackend per-key random salt (Story 3.2)."""

from __future__ import annotations

import base64
import hashlib

import pytest
from cryptography.fernet import Fernet, InvalidToken

from adk_secure_sessions import DecryptionError, FernetBackend
from adk_secure_sessions.backends.fernet import (
    _HKDF_INFO,
    _MIN_SALTED_LENGTH,
    _PBKDF2_ITERATIONS,
    _PBKDF2_ITERATIONS_LEGACY,
    _PBKDF2_SALT,
    _SALT_LENGTH,
    _SALT_MARKER,
)

_KEY_A = Fernet.generate_key()

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Per-Key Random Salt (Story 3.2)
# ---------------------------------------------------------------------------


class TestPerKeyRandomSalt:
    """Story 3.2: per-key random salt key derivation."""

    async def test_passphrase_string_round_trip_with_salt(self) -> None:
        """Passphrase (string) round-trips through salted encrypt/decrypt."""
        backend = FernetBackend(key="salt-test-passphrase")

        ciphertext = backend.sync_encrypt(b"hello salt")
        result = backend.sync_decrypt(ciphertext)

        assert result == b"hello salt"

    async def test_passphrase_bytes_round_trip_with_salt(self) -> None:
        """Passphrase (bytes) round-trips through salted encrypt/decrypt."""
        backend = FernetBackend(key=b"salt-test-bytes")

        ciphertext = backend.sync_encrypt(b"hello bytes salt")
        result = backend.sync_decrypt(ciphertext)

        assert result == b"hello bytes salt"

    def test_salt_uniqueness_100_encryptions(self) -> None:
        """100 encryptions of same plaintext produce 100 distinct ciphertexts."""
        backend = FernetBackend(key="uniqueness-test")
        plaintext = b"same-data"

        ciphertexts = {backend.sync_encrypt(plaintext) for _ in range(100)}

        assert len(ciphertexts) == 100

    def test_ciphertext_format_salt_marker(self) -> None:
        """Passphrase-mode ciphertext starts with SALT_MARKER (0x01)."""
        backend = FernetBackend(key="format-test")
        ciphertext = backend.sync_encrypt(b"format check")

        assert ciphertext[0:1] == _SALT_MARKER

    def test_ciphertext_format_salt_length(self) -> None:
        """Salt occupies bytes 1-17 of passphrase-mode ciphertext."""
        backend = FernetBackend(key="format-test")
        ciphertext = backend.sync_encrypt(b"format check")

        salt = ciphertext[1 : 1 + _SALT_LENGTH]
        assert len(salt) == _SALT_LENGTH

    def test_ciphertext_format_remainder_is_fernet_token(self) -> None:
        """Bytes after marker+salt are a valid Fernet token structure."""
        backend = FernetBackend(key="format-test")
        ciphertext = backend.sync_encrypt(b"format check")

        token = ciphertext[1 + _SALT_LENGTH :]
        # Fernet tokens are base64url-encoded, starting with 0x67 ('g')
        # for version byte 0x80 → base64 'gA...'
        assert token[0] >= 0x2B  # base64url character

    def test_direct_key_no_salt_marker(self) -> None:
        """Direct Fernet key mode produces no salt marker."""
        backend = FernetBackend(key=_KEY_A)
        ciphertext = backend.sync_encrypt(b"direct key test")

        assert ciphertext[0:1] != _SALT_MARKER
        assert ciphertext[0] >= 0x2B  # standard Fernet token

    def test_wrong_passphrase_raises_decryption_error(self) -> None:
        """Wrong passphrase raises DecryptionError on salted ciphertext."""
        backend1 = FernetBackend(key="correct-passphrase")
        backend2 = FernetBackend(key="wrong-passphrase")

        ciphertext = backend1.sync_encrypt(b"secret data")

        with pytest.raises(DecryptionError):
            backend2.sync_decrypt(ciphertext)

    def test_tampered_salt_raises_decryption_error(self) -> None:
        """Tampered salt causes DecryptionError (wrong derived key)."""
        backend = FernetBackend(key="tamper-test")
        ciphertext = backend.sync_encrypt(b"tamper target")

        # Flip a byte in the salt region (bytes 1-17)
        tampered = bytearray(ciphertext)
        tampered[5] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises(DecryptionError):
            backend.sync_decrypt(tampered)

    def test_empty_bytes_round_trip_with_salt(self) -> None:
        """Empty bytes round-trip through salted encrypt/decrypt."""
        backend = FernetBackend(key="empty-test")

        ciphertext = backend.sync_encrypt(b"")
        result = backend.sync_decrypt(ciphertext)

        assert result == b""

    def test_large_payload_round_trip_with_salt(self) -> None:
        """10KB payload round-trips through salted encrypt/decrypt."""
        backend = FernetBackend(key="large-payload-test")
        payload = b"x" * 10_240

        ciphertext = backend.sync_encrypt(payload)
        result = backend.sync_decrypt(ciphertext)

        assert result == payload

    def test_error_messages_no_sensitive_data(self) -> None:
        """Error messages contain no salt, key, or plaintext."""
        backend1 = FernetBackend(key="sensitive-test-key")
        backend2 = FernetBackend(key="other-test-key")

        ciphertext = backend1.sync_encrypt(b"sensitive-plaintext")

        with pytest.raises(DecryptionError) as exc_info:
            backend2.sync_decrypt(ciphertext)

        error_msg = str(exc_info.value)
        assert "sensitive-test-key" not in error_msg
        assert "other-test-key" not in error_msg
        assert "sensitive-plaintext" not in error_msg

    async def test_async_round_trip_with_salt(self) -> None:
        """Async encrypt/decrypt round-trips with salted ciphertext."""
        backend = FernetBackend(key="async-salt-test")

        ciphertext = await backend.encrypt(b"async payload")
        result = await backend.decrypt(ciphertext)

        assert result == b"async payload"

    def test_constants_match_design(self) -> None:
        """Verify constants match ADR-008 design values."""
        assert _PBKDF2_ITERATIONS == 600_000
        assert _PBKDF2_ITERATIONS_LEGACY == 480_000
        assert _SALT_MARKER == b"\x01"
        assert _SALT_LENGTH == 16
        assert _HKDF_INFO == b"adk-fernet-v2"
        assert _MIN_SALTED_LENGTH == 117
        assert _PBKDF2_SALT == b"adk-secure-sessions-fernet-v1"


class TestBackwardCompatibility:
    """Backward compatibility: legacy ciphertext decrypts with new backend."""

    def test_legacy_fixed_salt_ciphertext_decrypts(self) -> None:
        """Pre-3.2 ciphertext (fixed salt, 480k iterations) decrypts."""
        # Simulate legacy ciphertext: PBKDF2 at 480k with fixed salt
        legacy_key = base64.urlsafe_b64encode(
            hashlib.pbkdf2_hmac(
                "sha256",
                b"legacy-passphrase",
                _PBKDF2_SALT,
                _PBKDF2_ITERATIONS_LEGACY,
            )
        )
        legacy_fernet = Fernet(legacy_key)
        legacy_ct = legacy_fernet.encrypt(b"legacy data")

        # New backend with same passphrase should decrypt
        backend = FernetBackend(key="legacy-passphrase")
        result = backend.sync_decrypt(legacy_ct)

        assert result == b"legacy data"

    def test_new_ciphertext_not_readable_by_legacy(self) -> None:
        """New salted ciphertext cannot be decrypted by legacy Fernet."""
        backend = FernetBackend(key="forward-test")
        new_ct = backend.sync_encrypt(b"new format data")

        # Legacy derivation at 480k iterations
        legacy_key = base64.urlsafe_b64encode(
            hashlib.pbkdf2_hmac(
                "sha256",
                b"forward-test",
                _PBKDF2_SALT,
                _PBKDF2_ITERATIONS_LEGACY,
            )
        )
        legacy_fernet = Fernet(legacy_key)

        # New format has salt marker prefix — legacy Fernet can't decrypt
        with pytest.raises(InvalidToken):
            legacy_fernet.decrypt(new_ct)

    def test_direct_key_backward_compat(self) -> None:
        """Direct-key mode is fully backward compatible with raw Fernet."""
        fernet_key = Fernet.generate_key()
        raw_fernet = Fernet(fernet_key)
        backend = FernetBackend(key=fernet_key)

        # Raw Fernet → backend
        raw_ct = raw_fernet.encrypt(b"raw data")
        assert backend.sync_decrypt(raw_ct) == b"raw data"

        # Backend → raw Fernet
        backend_ct = backend.sync_encrypt(b"backend data")
        assert raw_fernet.decrypt(backend_ct) == b"backend data"

    def test_invalid_format_byte_raises_decryption_error(self) -> None:
        """Ciphertext with invalid first byte (< 0x2B, != 0x01) raises."""
        backend = FernetBackend(key="format-test")

        with pytest.raises(DecryptionError, match="invalid ciphertext format"):
            backend.sync_decrypt(b"\x00" + b"\x00" * 50)

    def test_marker_byte_short_ciphertext_raises(self) -> None:
        """Ciphertext with 0x01 marker but < _MIN_SALTED_LENGTH raises.

        When the first byte is 0x01 but the ciphertext is too short to be
        a valid salted format, it falls through to the format check and
        raises because 0x01 < 0x2B.
        """
        backend = FernetBackend(key="boundary-test")

        # 0x01 prefix + padding, total 50 bytes (well below 117)
        short_ct = b"\x01" + b"\x00" * 49
        with pytest.raises(DecryptionError, match="invalid ciphertext format"):
            backend.sync_decrypt(short_ct)

    def test_marker_byte_exact_boundary_raises(self) -> None:
        """Ciphertext at exactly _MIN_SALTED_LENGTH with marker is parsed.

        At 117 bytes with 0x01 prefix, dispatch enters the salted path
        but the Fernet token is garbage, so it raises DecryptionError.
        """
        backend = FernetBackend(key="exact-boundary-test")

        # Exactly 117 bytes: marker + 16 salt + 100 garbage token
        exact_ct = b"\x01" + b"\x00" * 16 + b"A" * 100
        with pytest.raises(DecryptionError):
            backend.sync_decrypt(exact_ct)

    def test_empty_ciphertext_raises_decryption_error(self) -> None:
        """Empty ciphertext raises DecryptionError."""
        backend = FernetBackend(key="empty-ct-test")

        with pytest.raises(DecryptionError):
            backend.sync_decrypt(b"")

    def test_salted_marker_direct_key_raises(self) -> None:
        """Salted ciphertext with direct-key backend raises DecryptionError.

        A direct-key backend has no passphrase_key for HKDF derivation.
        """
        # Create salted ciphertext with passphrase backend
        passphrase_backend = FernetBackend(key="passphrase-key")
        salted_ct = passphrase_backend.sync_encrypt(b"passphrase data")

        # Try to decrypt with direct-key backend
        direct_backend = FernetBackend(key=_KEY_A)

        with pytest.raises(DecryptionError):
            direct_backend.sync_decrypt(salted_ct)
