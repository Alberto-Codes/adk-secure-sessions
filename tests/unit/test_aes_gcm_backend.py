"""Tests for AesGcmBackend encryption backend."""

from __future__ import annotations

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from adk_secure_sessions.backends.aes_gcm import AesGcmBackend
from adk_secure_sessions.exceptions import ConfigurationError, DecryptionError
from adk_secure_sessions.protocols import EncryptionBackend
from adk_secure_sessions.serialization import BACKEND_AES_GCM

pytestmark = pytest.mark.unit

_NONCE_LENGTH = 12
_TAG_LENGTH = 16


@pytest.fixture()
def key() -> bytes:
    """Generate a valid 256-bit AES key."""
    return AESGCM.generate_key(bit_length=256)


@pytest.fixture()
def backend(key: bytes) -> AesGcmBackend:
    """Create an AesGcmBackend with a generated key."""
    return AesGcmBackend(key=key)


# --- Round-Trip ---


class TestEncryptDecryptRoundTrip:
    """Encrypt/decrypt round-trip tests."""

    async def test_round_trip(self, backend: AesGcmBackend) -> None:
        """Encrypt then decrypt returns original plaintext."""
        plaintext = b"hello, world"
        ciphertext = await backend.encrypt(plaintext)
        result = await backend.decrypt(ciphertext)
        assert result == plaintext

    async def test_non_deterministic_ciphertext(self, backend: AesGcmBackend) -> None:
        """Two encryptions of the same plaintext produce different ciphertexts."""
        plaintext = b"same input"
        ct1 = await backend.encrypt(plaintext)
        ct2 = await backend.encrypt(plaintext)
        assert ct1 != ct2

    async def test_empty_bytes_round_trip(self, backend: AesGcmBackend) -> None:
        """Empty plaintext round-trips correctly."""
        ciphertext = await backend.encrypt(b"")
        assert len(ciphertext) == _NONCE_LENGTH + _TAG_LENGTH  # 28 bytes
        result = await backend.decrypt(ciphertext)
        assert result == b""

    async def test_large_payload_round_trip(self, backend: AesGcmBackend) -> None:
        """10KB payload round-trips correctly."""
        plaintext = b"x" * 10_240
        ciphertext = await backend.encrypt(plaintext)
        result = await backend.decrypt(ciphertext)
        assert result == plaintext


# --- Wrong Key / Tampered ---


class TestWrongKeyDecryption:
    """Decryption failure scenarios."""

    async def test_wrong_key_raises_decryption_error(self) -> None:
        """Decrypting with a different key raises DecryptionError."""
        key1 = AESGCM.generate_key(bit_length=256)
        key2 = AESGCM.generate_key(bit_length=256)
        backend1 = AesGcmBackend(key=key1)
        backend2 = AesGcmBackend(key=key2)

        ciphertext = await backend1.encrypt(b"secret")
        with pytest.raises(DecryptionError):
            await backend2.decrypt(ciphertext)

    async def test_tampered_ciphertext_raises_decryption_error(
        self, backend: AesGcmBackend
    ) -> None:
        """Tampered ciphertext raises DecryptionError."""
        ciphertext = await backend.encrypt(b"secret")
        tampered = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])
        with pytest.raises(DecryptionError):
            await backend.decrypt(tampered)

    async def test_malformed_ciphertext_raises_decryption_error(
        self, backend: AesGcmBackend
    ) -> None:
        """Too-short ciphertext raises DecryptionError."""
        with pytest.raises(DecryptionError, match="ciphertext too short"):
            await backend.decrypt(b"short")

    async def test_error_message_excludes_key_material(
        self, backend: AesGcmBackend
    ) -> None:
        """Error messages do not contain key material or ciphertext."""
        ciphertext = await backend.encrypt(b"secret")
        tampered = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])
        with pytest.raises(DecryptionError) as exc_info:
            await backend.decrypt(tampered)
        msg = str(exc_info.value)
        assert b"secret" not in msg.encode()
        assert "key" not in msg.lower() or "wrong key" in msg.lower()

    async def test_cross_backend_confusion(self) -> None:
        """Fernet ciphertext passed to AesGcmBackend raises DecryptionError."""
        from adk_secure_sessions.backends.fernet import FernetBackend

        fernet = FernetBackend(key="my-secret")
        aesgcm = AesGcmBackend(key=AESGCM.generate_key(bit_length=256))

        fernet_ct = await fernet.encrypt(b"hello")
        with pytest.raises(DecryptionError):
            await aesgcm.decrypt(fernet_ct)


# --- Key Validation ---


class TestKeyValidation:
    """Constructor key validation tests."""

    def test_non_bytes_key_raises_configuration_error(self) -> None:
        """String key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="key must be bytes"):
            AesGcmBackend(key="not-bytes")  # type: ignore[arg-type]

    def test_empty_key_raises_configuration_error(self) -> None:
        """Empty bytes key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="exactly 32 bytes"):
            AesGcmBackend(key=b"")

    def test_short_key_raises_configuration_error(self) -> None:
        """16-byte key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="exactly 32 bytes"):
            AesGcmBackend(key=b"x" * 16)

    def test_long_key_raises_configuration_error(self) -> None:
        """64-byte key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="exactly 32 bytes"):
            AesGcmBackend(key=b"x" * 64)

    def test_int_key_raises_configuration_error(self) -> None:
        """Integer key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="key must be bytes"):
            AesGcmBackend(key=12345)  # type: ignore[arg-type]


# --- Nonce Uniqueness ---


class TestNonceUniqueness:
    """Nonce security tests."""

    async def test_100_encryptions_produce_distinct_nonces(
        self, backend: AesGcmBackend
    ) -> None:
        """100 encryptions of the same plaintext produce 100 distinct nonces."""
        plaintext = b"same"
        nonces = set()
        for _ in range(100):
            ct = await backend.encrypt(plaintext)
            nonces.add(ct[:_NONCE_LENGTH])
        assert len(nonces) == 100


# --- Ciphertext Format ---


class TestCiphertextFormat:
    """Ciphertext layout verification."""

    async def test_ciphertext_starts_with_12_byte_nonce(
        self, backend: AesGcmBackend
    ) -> None:
        """First 12 bytes are the nonce, remainder is ciphertext+tag."""
        plaintext = b"hello"
        ciphertext = await backend.encrypt(plaintext)
        assert len(ciphertext) > _NONCE_LENGTH + _TAG_LENGTH
        assert len(ciphertext) == _NONCE_LENGTH + len(plaintext) + _TAG_LENGTH

    async def test_empty_plaintext_produces_28_bytes(
        self, backend: AesGcmBackend
    ) -> None:
        """Empty plaintext produces exactly 28 bytes (12 nonce + 16 tag)."""
        ciphertext = await backend.encrypt(b"")
        assert len(ciphertext) == 28


# --- Interoperability ---


class TestInteroperability:
    """Interop with raw cryptography library."""

    async def test_interop_with_raw_aesgcm(self, key: bytes) -> None:
        """Backend ciphertext can be decrypted by raw AESGCM."""
        backend = AesGcmBackend(key=key)
        plaintext = b"interop test"
        ciphertext = await backend.encrypt(plaintext)

        raw = AESGCM(key)
        nonce = ciphertext[:_NONCE_LENGTH]
        ct_and_tag = ciphertext[_NONCE_LENGTH:]
        result = raw.decrypt(nonce, ct_and_tag, None)
        assert result == plaintext

    async def test_raw_aesgcm_ciphertext_decrypted_by_backend(self, key: bytes) -> None:
        """Raw AESGCM ciphertext can be decrypted by the backend."""
        import os

        backend = AesGcmBackend(key=key)
        raw = AESGCM(key)
        plaintext = b"reverse interop"
        nonce = os.urandom(_NONCE_LENGTH)
        ct_and_tag = raw.encrypt(nonce, plaintext, None)

        result = await backend.decrypt(nonce + ct_and_tag)
        assert result == plaintext


# --- Polish ---


class TestPolish:
    """Protocol conformance and type validation."""

    def test_protocol_conformance(self, backend: AesGcmBackend) -> None:
        """AesGcmBackend conforms to EncryptionBackend protocol."""
        assert isinstance(backend, EncryptionBackend)

    def test_backend_id(self, backend: AesGcmBackend) -> None:
        """backend_id returns BACKEND_AES_GCM (0x02)."""
        assert backend.backend_id == BACKEND_AES_GCM
        assert backend.backend_id == 0x02

    async def test_non_bytes_plaintext_raises_type_error(
        self, backend: AesGcmBackend
    ) -> None:
        """Non-bytes plaintext raises TypeError."""
        with pytest.raises(TypeError, match="plaintext must be bytes"):
            await backend.encrypt("not bytes")  # type: ignore[arg-type]

    async def test_non_bytes_ciphertext_raises_type_error(
        self, backend: AesGcmBackend
    ) -> None:
        """Non-bytes ciphertext raises TypeError."""
        with pytest.raises(TypeError, match="ciphertext must be bytes"):
            await backend.decrypt("not bytes")  # type: ignore[arg-type]

    def test_decryption_error_inherits_secure_session_error(self) -> None:
        """DecryptionError is a SecureSessionError."""
        from adk_secure_sessions.exceptions import SecureSessionError

        assert issubclass(DecryptionError, SecureSessionError)

    def test_sync_encrypt_non_bytes_raises_type_error(
        self, backend: AesGcmBackend
    ) -> None:
        """sync_encrypt with non-bytes raises TypeError."""
        with pytest.raises(TypeError, match="plaintext must be bytes"):
            backend.sync_encrypt("not bytes")  # type: ignore[arg-type]

    def test_sync_decrypt_non_bytes_raises_type_error(
        self, backend: AesGcmBackend
    ) -> None:
        """sync_decrypt with non-bytes raises TypeError."""
        with pytest.raises(TypeError, match="ciphertext must be bytes"):
            backend.sync_decrypt("not bytes")  # type: ignore[arg-type]

    def test_sync_round_trip(self, backend: AesGcmBackend) -> None:
        """sync_encrypt/sync_decrypt round-trips correctly."""
        plaintext = b"sync test"
        ciphertext = backend.sync_encrypt(plaintext)
        result = backend.sync_decrypt(ciphertext)
        assert result == plaintext
