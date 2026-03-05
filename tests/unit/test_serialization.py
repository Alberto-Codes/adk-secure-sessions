"""Tests for the serialization layer.

Validates envelope helpers, encrypt/decrypt round-trips for both
session state dicts and JSON strings, error handling, and edge cases.
"""

from __future__ import annotations

import pytest

from adk_secure_sessions.exceptions import DecryptionError, SerializationError
from adk_secure_sessions.serialization import (
    BACKEND_FERNET,
    ENVELOPE_VERSION_1,
    _build_envelope,
    _parse_envelope,
    decrypt_json,
    decrypt_session,
    encrypt_json,
    encrypt_session,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Envelope Helpers
# ---------------------------------------------------------------------------


class TestBuildEnvelope:
    """Tests for _build_envelope."""

    def test_builds_correct_header(self) -> None:
        """Output starts with version and backend_id bytes."""
        result = _build_envelope(ENVELOPE_VERSION_1, BACKEND_FERNET, b"cipher")
        assert result[0] == ENVELOPE_VERSION_1
        assert result[1] == BACKEND_FERNET
        assert result[2:] == b"cipher"

    def test_empty_ciphertext(self) -> None:
        """Envelope with empty ciphertext is 2 bytes."""
        result = _build_envelope(ENVELOPE_VERSION_1, BACKEND_FERNET, b"")
        assert len(result) == 2


class TestParseEnvelope:
    """Tests for _parse_envelope."""

    def test_round_trip(self) -> None:
        """Build then parse returns original components."""
        envelope = _build_envelope(ENVELOPE_VERSION_1, BACKEND_FERNET, b"data")
        version, backend_id, ciphertext = _parse_envelope(envelope)
        assert version == ENVELOPE_VERSION_1
        assert backend_id == BACKEND_FERNET
        assert ciphertext == b"data"

    def test_too_short_raises_decryption_error(self) -> None:
        """Envelope shorter than 3 bytes raises DecryptionError."""
        with pytest.raises(DecryptionError, match="too short"):
            _parse_envelope(b"\x01\x01")

    def test_empty_raises_decryption_error(self) -> None:
        """Empty envelope raises DecryptionError."""
        with pytest.raises(DecryptionError, match="too short"):
            _parse_envelope(b"")

    def test_unknown_version_raises_decryption_error(self) -> None:
        """Unrecognized version byte raises DecryptionError."""
        with pytest.raises(DecryptionError, match="Unsupported envelope version"):
            _parse_envelope(b"\xff\x01data")

    def test_unknown_backend_raises_decryption_error(self) -> None:
        """Unrecognized backend ID raises DecryptionError."""
        with pytest.raises(DecryptionError, match="Unsupported encryption backend"):
            _parse_envelope(b"\x01\xffdata")


# ---------------------------------------------------------------------------
# Helper: mock backend
# ---------------------------------------------------------------------------


class _MockBackend:
    """Minimal EncryptionBackend for testing (XOR with 0x42)."""

    async def encrypt(self, plaintext: bytes) -> bytes:
        return bytes(b ^ 0x42 for b in plaintext)

    async def decrypt(self, ciphertext: bytes) -> bytes:
        return bytes(b ^ 0x42 for b in ciphertext)


class _BadDecryptBackend:
    """Backend that always raises DecryptionError."""

    async def encrypt(self, plaintext: bytes) -> bytes:
        return plaintext

    async def decrypt(self, ciphertext: bytes) -> bytes:
        from adk_secure_sessions.exceptions import DecryptionError

        raise DecryptionError("Decryption failed")


class _BadEncryptBackend:
    """Backend that always raises EncryptionError on encrypt."""

    async def encrypt(self, plaintext: bytes) -> bytes:
        from adk_secure_sessions.exceptions import EncryptionError

        raise EncryptionError("Encryption hardware failure")

    async def decrypt(self, ciphertext: bytes) -> bytes:
        return ciphertext


# ---------------------------------------------------------------------------
# US1: encrypt_session
# ---------------------------------------------------------------------------


class TestEncryptSession:
    """User Story 1 — Encrypt session state dicts."""

    async def test_simple_dict(self) -> None:
        """T008: encrypt_session with simple dict produces envelope."""
        backend = _MockBackend()
        result = await encrypt_session({"ssn": "123-45-6789"}, backend, BACKEND_FERNET)
        assert isinstance(result, bytes)
        assert result[:2] == bytes([ENVELOPE_VERSION_1, BACKEND_FERNET])
        # Ciphertext should differ from plaintext JSON
        import json

        plaintext_json = json.dumps({"ssn": "123-45-6789"}).encode()
        assert result[2:] != plaintext_json

    async def test_nested_dict(self) -> None:
        """T009: encrypt_session with nested dict."""
        backend = _MockBackend()
        result = await encrypt_session(
            {"user": {"name": "Alice", "age": 30}}, backend, BACKEND_FERNET
        )
        assert isinstance(result, bytes)
        assert result[:2] == bytes([ENVELOPE_VERSION_1, BACKEND_FERNET])

    async def test_empty_dict(self) -> None:
        """T010: encrypt_session with empty dict."""
        backend = _MockBackend()
        result = await encrypt_session({}, backend, BACKEND_FERNET)
        assert isinstance(result, bytes)
        assert len(result) > 2  # header + ciphertext

    async def test_non_serializable_raises_serialization_error(self) -> None:
        """T011: encrypt_session with non-serializable input raises."""
        import datetime

        backend = _MockBackend()
        with pytest.raises(SerializationError):
            await encrypt_session(
                {"ts": datetime.datetime.now()}, backend, BACKEND_FERNET
            )


# ---------------------------------------------------------------------------
# US2: decrypt_session
# ---------------------------------------------------------------------------


class TestDecryptSession:
    """User Story 2 — Decrypt session state dicts."""

    async def test_round_trip_empty_dict(self) -> None:
        """T061: Round-trip encrypt/decrypt with empty dict returns empty dict."""
        backend = _MockBackend()
        envelope = await encrypt_session({}, backend, BACKEND_FERNET)
        restored = await decrypt_session(envelope, backend)
        assert restored == {}

    async def test_round_trip_type_diverse(self) -> None:
        """T014: Round-trip with strings, numbers, booleans, nulls, nested."""
        backend = _MockBackend()
        data = {
            "str": "hello",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "nested": {"a": [1, 2, 3]},
            "list": [1, "two", None],
        }
        envelope = await encrypt_session(data, backend, BACKEND_FERNET)
        restored = await decrypt_session(envelope, backend)
        assert restored == data

    async def test_tampered_ciphertext_raises(self) -> None:
        """T015: Tampered ciphertext raises DecryptionError."""
        backend = _MockBackend()
        envelope = await encrypt_session({"key": "value"}, backend, BACKEND_FERNET)
        # Flip a byte in the ciphertext portion
        tampered = bytearray(envelope)
        tampered[-1] ^= 0xFF
        # The XOR mock will "decrypt" to garbage JSON, causing json.loads to fail
        with pytest.raises((DecryptionError, SerializationError)):
            await decrypt_session(bytes(tampered), backend)

    async def test_truncated_envelope_raises(self) -> None:
        """T016: Truncated/empty envelope raises DecryptionError."""
        backend = _MockBackend()
        with pytest.raises(DecryptionError):
            await decrypt_session(b"\x01", backend)
        with pytest.raises(DecryptionError):
            await decrypt_session(b"", backend)

    async def test_wrong_key_backend_raises(self) -> None:
        """T017: Wrong-key backend raises DecryptionError."""
        encrypt_backend = _MockBackend()
        envelope = await encrypt_session(
            {"secret": "data"}, encrypt_backend, BACKEND_FERNET
        )
        with pytest.raises(DecryptionError):
            await decrypt_session(envelope, _BadDecryptBackend())


# ---------------------------------------------------------------------------
# US3: Self-Describing Envelope Format
# ---------------------------------------------------------------------------


class TestEnvelopeFormat:
    """User Story 3 — Envelope carries version and backend identifier."""

    async def test_first_bytes_are_version_and_backend(self) -> None:
        """T020: Byte 0 == ENVELOPE_VERSION_1, byte 1 == BACKEND_FERNET."""
        backend = _MockBackend()
        envelope = await encrypt_session({"x": 1}, backend, BACKEND_FERNET)
        assert envelope[0] == ENVELOPE_VERSION_1
        assert envelope[1] == BACKEND_FERNET

    def test_unrecognized_version_error_message(self) -> None:
        """T021: Unrecognized version byte gives clear error."""
        with pytest.raises(DecryptionError, match="Unsupported envelope version"):
            _parse_envelope(b"\xff\x01data")

    def test_unrecognized_backend_error_message(self) -> None:
        """T022: Unrecognized backend ID gives clear error."""
        with pytest.raises(DecryptionError, match="Unsupported encryption backend"):
            _parse_envelope(b"\x01\xffdata")

    async def test_different_backend_ids_produce_different_bytes(self) -> None:
        """T023: Different backend_id args produce different second bytes."""
        backend = _MockBackend()
        env1 = await encrypt_session({"a": 1}, backend, BACKEND_FERNET)
        # Use a different backend_id (0x02) — won't be in registry but
        # build_envelope doesn't validate, only parse does.
        env2 = _build_envelope(ENVELOPE_VERSION_1, 0x02, b"fake")
        assert env1[1] != env2[1]


# ---------------------------------------------------------------------------
# US4: encrypt_json / decrypt_json
# ---------------------------------------------------------------------------


class TestEncryptDecryptJson:
    """User Story 4 — Encrypt/decrypt pre-serialized JSON strings."""

    async def test_round_trip(self) -> None:
        """T025: encrypt_json → decrypt_json round-trip."""
        backend = _MockBackend()
        json_str = '{"event": "click", "ts": 1234567890}'
        envelope = await encrypt_json(json_str, backend, BACKEND_FERNET)
        restored = await decrypt_json(envelope, backend)
        assert restored == json_str

    async def test_envelope_header(self) -> None:
        """T026: encrypt_json output starts with envelope header."""
        backend = _MockBackend()
        envelope = await encrypt_json('{"a": 1}', backend, BACKEND_FERNET)
        assert envelope[:2] == bytes([ENVELOPE_VERSION_1, BACKEND_FERNET])

    async def test_tampered_envelope_raises(self) -> None:
        """T027: decrypt_json with tampered envelope raises."""
        backend = _MockBackend()
        envelope = await encrypt_json('{"a": 1}', backend, BACKEND_FERNET)
        tampered = bytearray(envelope)
        tampered[-1] ^= 0xFF
        with pytest.raises((DecryptionError, SerializationError)):
            await decrypt_json(bytes(tampered), backend)


# ---------------------------------------------------------------------------
# Edge Cases (Phase 7)
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Cross-cutting edge-case tests."""

    async def test_unicode_round_trip(self) -> None:
        """T032: Unicode data round-trips correctly."""
        backend = _MockBackend()
        data = {"name": "\u65e5\u672c\u8a9e", "emoji": "\U0001f600"}
        envelope = await encrypt_session(data, backend, BACKEND_FERNET)
        restored = await decrypt_session(envelope, backend)
        assert restored == data

    async def test_error_messages_no_plaintext(self) -> None:
        """T033: Error messages don't contain plaintext or key material."""
        import datetime

        backend = _MockBackend()
        secret_data = {"ssn": "123-45-6789", "ts": datetime.datetime.now()}
        with pytest.raises(SerializationError) as exc_info:
            await encrypt_session(secret_data, backend, BACKEND_FERNET)
        message = str(exc_info.value)
        assert "123-45-6789" not in message
        assert "ssn" not in message

    async def test_decrypt_error_messages_no_ciphertext(self) -> None:
        """T033b: Decryption error messages don't contain ciphertext."""
        with pytest.raises(DecryptionError) as exc_info:
            _parse_envelope(b"\xff\x01secret-ciphertext-here")
        message = str(exc_info.value)
        assert "secret-ciphertext-here" not in message

    async def test_encrypt_session_backend_failure_propagates(self) -> None:
        """T034: Backend encryption failure propagates to caller."""
        from adk_secure_sessions.exceptions import EncryptionError

        backend = _BadEncryptBackend()
        with pytest.raises(EncryptionError, match="Encryption hardware failure"):
            await encrypt_session({"key": "value"}, backend, BACKEND_FERNET)

    async def test_encrypt_json_backend_failure_propagates(self) -> None:
        """T035: Backend encryption failure in encrypt_json propagates."""
        from adk_secure_sessions.exceptions import EncryptionError

        backend = _BadEncryptBackend()
        with pytest.raises(EncryptionError, match="Encryption hardware failure"):
            await encrypt_json('{"key": "value"}', backend, BACKEND_FERNET)

    async def test_deeply_nested_dict_round_trip(self) -> None:
        """T036: Session state with 6+ levels of nesting round-trips correctly."""
        backend = _MockBackend()
        data = {
            "L1": {
                "L2": {
                    "L3": {
                        "L4": {
                            "L5": {
                                "L6": {"value": "deep", "num": 42},
                                "list": [1, {"inner": True}],
                            }
                        }
                    }
                }
            }
        }
        envelope = await encrypt_session(data, backend, BACKEND_FERNET)
        restored = await decrypt_session(envelope, backend)
        assert restored == data
        assert restored["L1"]["L2"]["L3"]["L4"]["L5"]["L6"]["value"] == "deep"
        assert restored["L1"]["L2"]["L3"]["L4"]["L5"]["list"][1]["inner"] is True
