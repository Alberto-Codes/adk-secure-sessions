"""Tests for EncryptedJSON TypeDecorator.

Validates encryption/decryption at the TypeDecorator boundary,
including None passthrough, error handling, and envelope format.

See Also:
    `adk_secure_sessions.services.type_decorator` for the implementation.
"""

from __future__ import annotations

import base64

import pytest
from cryptography.fernet import Fernet

from adk_secure_sessions.exceptions import DecryptionError
from adk_secure_sessions.serialization import (
    BACKEND_AES_GCM,
    BACKEND_FERNET,
    ENVELOPE_VERSION_1,
    _build_envelope,
)
from adk_secure_sessions.services.type_decorator import EncryptedJSON

pytestmark = pytest.mark.unit


# --- Fixtures ---


@pytest.fixture
def fernet_instance() -> Fernet:
    """A Fernet instance for sync encrypt/decrypt."""
    return Fernet(Fernet.generate_key())


@pytest.fixture
def encrypted_json(fernet_instance: Fernet) -> EncryptedJSON:
    """An EncryptedJSON TypeDecorator with real Fernet callables."""
    return EncryptedJSON(
        encrypt_fn=fernet_instance.encrypt,
        decrypt_dispatch={BACKEND_FERNET: fernet_instance.decrypt},
        backend_id=BACKEND_FERNET,
    )


# --- Task 1.2: process_bind_param ---


class TestProcessBindParam:
    """Tests for EncryptedJSON.process_bind_param."""

    def test_encrypts_dict_to_base64_string(
        self, encrypted_json: EncryptedJSON
    ) -> None:
        """T001: process_bind_param returns a base64-encoded string."""
        result = encrypted_json.process_bind_param({"key": "value"}, dialect=None)
        assert isinstance(result, str)
        # Should be valid base64
        decoded = base64.b64decode(result.encode("ascii"))
        assert decoded[0] == ENVELOPE_VERSION_1
        assert decoded[1] == BACKEND_FERNET

    def test_envelope_contains_encrypted_data(
        self,
        encrypted_json: EncryptedJSON,
    ) -> None:
        """T002: Envelope ciphertext is not the raw plaintext."""
        state = {"secret": "sensitive-data"}
        result = encrypted_json.process_bind_param(state, dialect=None)
        decoded = base64.b64decode(result.encode("ascii"))
        # Ciphertext (after 2-byte header) should not contain plaintext
        assert b"sensitive-data" not in decoded[2:]


# --- Task 1.3: process_result_value ---


class TestProcessResultValue:
    """Tests for EncryptedJSON.process_result_value."""

    def test_round_trip_simple_dict(self, encrypted_json: EncryptedJSON) -> None:
        """T003: Encrypt then decrypt returns original dict."""
        original = {"key": "value", "count": 42}
        encrypted = encrypted_json.process_bind_param(original, dialect=None)
        result = encrypted_json.process_result_value(encrypted, dialect=None)
        assert result == original

    def test_round_trip_nested_dict(self, encrypted_json: EncryptedJSON) -> None:
        """T004: Nested dict survives round-trip."""
        original = {"a": {"b": {"c": [1, 2, 3]}}}
        encrypted = encrypted_json.process_bind_param(original, dialect=None)
        result = encrypted_json.process_result_value(encrypted, dialect=None)
        assert result == original

    def test_round_trip_empty_dict(self, encrypted_json: EncryptedJSON) -> None:
        """T005: Empty dict survives round-trip."""
        original: dict[str, object] = {}
        encrypted = encrypted_json.process_bind_param(original, dialect=None)
        result = encrypted_json.process_result_value(encrypted, dialect=None)
        assert result == original


# --- Task 1.4: None passthrough ---


class TestNonePassthrough:
    """Tests for None value handling."""

    def test_bind_param_none_returns_none(self, encrypted_json: EncryptedJSON) -> None:
        """T006: process_bind_param passes None through."""
        assert encrypted_json.process_bind_param(None, dialect=None) is None

    def test_result_value_none_returns_none(
        self, encrypted_json: EncryptedJSON
    ) -> None:
        """T007: process_result_value passes None through."""
        assert encrypted_json.process_result_value(None, dialect=None) is None


# --- Task 1.5: Wrong key raises DecryptionError ---


class TestWrongKeyDecryption:
    """Tests for wrong-key error handling."""

    def test_wrong_key_raises_decryption_error(self) -> None:
        """T008: Decrypting with wrong key raises DecryptionError."""
        key_a = Fernet.generate_key()
        key_b = Fernet.generate_key()

        enc_json_a = EncryptedJSON(
            encrypt_fn=Fernet(key_a).encrypt,
            decrypt_dispatch={BACKEND_FERNET: Fernet(key_a).decrypt},
            backend_id=BACKEND_FERNET,
        )
        enc_json_b = EncryptedJSON(
            encrypt_fn=Fernet(key_b).encrypt,
            decrypt_dispatch={BACKEND_FERNET: Fernet(key_b).decrypt},
            backend_id=BACKEND_FERNET,
        )

        encrypted = enc_json_a.process_bind_param({"secret": "data"}, dialect=None)

        with pytest.raises(DecryptionError, match="wrong key"):
            enc_json_b.process_result_value(encrypted, dialect=None)


# --- Task 1.6: cache_ok ---


class TestCacheOk:
    """Tests for cache_ok attribute."""

    def test_cache_ok_is_true(self, encrypted_json: EncryptedJSON) -> None:
        """T009: EncryptedJSON.cache_ok is True."""
        assert encrypted_json.cache_ok is True


# --- Story 3.3: Multi-Backend Decrypt Dispatch ---


class TestDecryptDispatch:
    """Tests for multi-backend decrypt dispatch in process_result_value."""

    def test_dispatch_routes_to_correct_backend_by_envelope_id(self) -> None:
        """T010: Decrypt dispatches to correct backend based on envelope backend_id."""
        fernet_a = Fernet(Fernet.generate_key())
        fernet_b = Fernet(Fernet.generate_key())

        # Encrypt data with fernet_b, tag envelope as BACKEND_AES_GCM
        plaintext = b'{"from": "backend_b"}'
        ciphertext_b = fernet_b.encrypt(plaintext)
        envelope = _build_envelope(ENVELOPE_VERSION_1, BACKEND_AES_GCM, ciphertext_b)
        b64_value = base64.b64encode(envelope).decode("ascii")

        # Dispatch: BACKEND_FERNET -> fernet_a, BACKEND_AES_GCM -> fernet_b
        enc_json = EncryptedJSON(
            encrypt_fn=fernet_a.encrypt,
            decrypt_dispatch={
                BACKEND_FERNET: fernet_a.decrypt,
                BACKEND_AES_GCM: fernet_b.decrypt,
            },
            backend_id=BACKEND_FERNET,
        )

        result = enc_json.process_result_value(b64_value, dialect=None)
        assert result == {"from": "backend_b"}

    def test_dispatch_routes_primary_backend_on_read(self) -> None:
        """T011: Data encrypted with primary backend decrypts via dispatch."""
        fernet_a = Fernet(Fernet.generate_key())
        fernet_b = Fernet(Fernet.generate_key())

        enc_json = EncryptedJSON(
            encrypt_fn=fernet_a.encrypt,
            decrypt_dispatch={
                BACKEND_FERNET: fernet_a.decrypt,
                BACKEND_AES_GCM: fernet_b.decrypt,
            },
            backend_id=BACKEND_FERNET,
        )

        # Write with primary (Fernet A)
        encrypted = enc_json.process_bind_param({"key": "value"}, dialect=None)
        # Read — should dispatch to Fernet A based on envelope header
        result = enc_json.process_result_value(encrypted, dialect=None)
        assert result == {"key": "value"}

    def test_unregistered_backend_in_dispatch_raises_decryption_error(self) -> None:
        """T012: Backend_id in envelope but not in dispatch raises DecryptionError."""
        fernet_a = Fernet(Fernet.generate_key())
        fernet_b = Fernet(Fernet.generate_key())

        # Encrypt with fernet_b, tag envelope as BACKEND_AES_GCM
        ciphertext = fernet_b.encrypt(b'{"key": "value"}')
        envelope = _build_envelope(ENVELOPE_VERSION_1, BACKEND_AES_GCM, ciphertext)
        b64_value = base64.b64encode(envelope).decode("ascii")

        # Dispatch only has BACKEND_FERNET — missing BACKEND_AES_GCM
        enc_json = EncryptedJSON(
            encrypt_fn=fernet_a.encrypt,
            decrypt_dispatch={BACKEND_FERNET: fernet_a.decrypt},
            backend_id=BACKEND_FERNET,
        )

        with pytest.raises(DecryptionError, match="No decrypt function"):
            enc_json.process_result_value(b64_value, dialect=None)

    def test_write_always_uses_primary_backend_id(self) -> None:
        """T013: Write path uses primary backend_id regardless of dispatch map."""
        fernet_a = Fernet(Fernet.generate_key())
        fernet_b = Fernet(Fernet.generate_key())

        enc_json = EncryptedJSON(
            encrypt_fn=fernet_a.encrypt,
            decrypt_dispatch={
                BACKEND_FERNET: fernet_a.decrypt,
                BACKEND_AES_GCM: fernet_b.decrypt,
            },
            backend_id=BACKEND_FERNET,
        )

        result = enc_json.process_bind_param({"key": "value"}, dialect=None)
        decoded = base64.b64decode(result.encode("ascii"))
        assert decoded[0] == ENVELOPE_VERSION_1
        assert decoded[1] == BACKEND_FERNET
