"""Tests for the exception hierarchy.

Validates inheritance relationships, sibling independence, message
handling, exception chaining, and raise-site message safety.
"""

from __future__ import annotations

import pytest

from adk_secure_sessions.exceptions import (
    ConfigurationError,
    DecryptionError,
    EncryptionError,
    SecureSessionError,
    SerializationError,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# US1: Catch All Library Errors
# ---------------------------------------------------------------------------


class TestCatchAllLibraryErrors:
    """User Story 1 — SecureSessionError catches all library exceptions."""

    def test_secure_session_error_inherits_from_exception(self) -> None:
        """T003: SecureSessionError is a subclass of Exception."""
        assert issubclass(SecureSessionError, Exception)

    def test_encryption_error_caught_by_base(self) -> None:
        """T004: EncryptionError is caught by except SecureSessionError."""
        with pytest.raises(SecureSessionError):
            raise EncryptionError("encryption failed")

    def test_decryption_error_caught_by_base(self) -> None:
        """T005: DecryptionError is caught by except SecureSessionError."""
        with pytest.raises(SecureSessionError):
            raise DecryptionError("decryption failed")

    def test_secure_session_error_not_caught_by_unrelated(self) -> None:
        """T006: SecureSessionError is not caught by unrelated handlers."""
        with pytest.raises(SecureSessionError):
            try:
                raise SecureSessionError("test")
            except (ValueError, TypeError, KeyError):
                pytest.fail("SecureSessionError caught by unrelated handler")


# ---------------------------------------------------------------------------
# US2: Distinguish Encryption from Decryption Errors
# ---------------------------------------------------------------------------


class TestSiblingIndependence:
    """User Story 2 — EncryptionError and DecryptionError are siblings."""

    def test_both_are_subclasses_of_base(self) -> None:
        """T007: Both are subclasses of SecureSessionError."""
        assert issubclass(EncryptionError, SecureSessionError)
        assert issubclass(DecryptionError, SecureSessionError)

    def test_neither_is_subclass_of_the_other(self) -> None:
        """T008: Neither inherits from the other."""
        assert not issubclass(EncryptionError, DecryptionError)
        assert not issubclass(DecryptionError, EncryptionError)

    def test_decryption_error_not_caught_by_encryption_handler(self) -> None:
        """T009: DecryptionError is not caught by except EncryptionError."""
        with pytest.raises(DecryptionError):
            try:
                raise DecryptionError("wrong key")
            except EncryptionError:
                pytest.fail("DecryptionError caught by EncryptionError handler")

    def test_encryption_error_not_caught_by_decryption_handler(self) -> None:
        """T010: EncryptionError is not caught by except DecryptionError."""
        with pytest.raises(EncryptionError):
            try:
                raise EncryptionError("encrypt failed")
            except DecryptionError:
                pytest.fail("EncryptionError caught by DecryptionError handler")


# ---------------------------------------------------------------------------
# US3: Safe Error Messages
# ---------------------------------------------------------------------------


class TestSafeErrorMessages:
    """User Story 3 — Message handling, chaining, and raise-site safety."""

    @pytest.mark.parametrize(
        "exc_cls",
        [SecureSessionError, EncryptionError, DecryptionError],
        ids=["base", "encryption", "decryption"],
    )
    def test_exception_accepts_and_stores_message(
        self,
        exc_cls: type[SecureSessionError],
    ) -> None:
        """T011: All exception classes accept and store a message."""
        msg = "something went wrong"
        exc = exc_cls(msg)
        assert str(exc) == msg
        assert exc.args == (msg,)

    def test_encryption_error_chaining_preserves_cause(self) -> None:
        """T012: raise EncryptionError from original preserves __cause__."""
        original = RuntimeError("low-level failure")
        try:
            raise EncryptionError("encryption failed") from original
        except EncryptionError as exc:
            assert exc.__cause__ is original

    def test_decryption_error_chaining_preserves_cause(self) -> None:
        """T013: raise DecryptionError from original preserves __cause__."""
        original = RuntimeError("low-level failure")
        try:
            raise DecryptionError("decryption failed") from original
        except DecryptionError as exc:
            assert exc.__cause__ is original

    @pytest.mark.parametrize(
        "exc_cls",
        [
            SecureSessionError,
            EncryptionError,
            DecryptionError,
            SerializationError,
            ConfigurationError,
        ],
        ids=["base", "encryption", "decryption", "serialization", "configuration"],
    )
    def test_exception_accepts_empty_message(
        self,
        exc_cls: type[SecureSessionError],
    ) -> None:
        """All exception classes accept an empty message."""
        exc = exc_cls()
        assert str(exc) == ""

    async def test_existing_raise_sites_use_safe_messages(self) -> None:
        """T014: Raise sites in fernet.py use safe messages.

        Verifies that the DecryptionError raised by FernetBackend.decrypt
        does not contain key material, ciphertext, or plaintext.
        """
        from adk_secure_sessions.backends.fernet import FernetBackend

        backend = FernetBackend(key="test-key")
        with pytest.raises(DecryptionError) as exc_info:
            await backend.decrypt(b"not-valid-ciphertext")
        message = str(exc_info.value).lower()
        # Message should describe the failure category, not leak data
        assert "test-key" not in message
        assert "not-valid-ciphertext" not in message
        assert "failed" in message or "invalid" in message


# ---------------------------------------------------------------------------
# SerializationError Hierarchy
# ---------------------------------------------------------------------------


class TestSerializationErrorHierarchy:
    """SerializationError is a sibling of EncryptionError/DecryptionError."""

    def test_serialization_error_inherits_from_base(self) -> None:
        """SerializationError is a subclass of SecureSessionError."""
        assert issubclass(SerializationError, SecureSessionError)

    def test_serialization_error_caught_by_base(self) -> None:
        """SerializationError is caught by except SecureSessionError."""
        with pytest.raises(SecureSessionError):
            raise SerializationError("bad data")

    def test_serialization_error_not_subclass_of_encryption(self) -> None:
        """SerializationError is not a subclass of EncryptionError."""
        assert not issubclass(SerializationError, EncryptionError)

    def test_serialization_error_not_subclass_of_decryption(self) -> None:
        """SerializationError is not a subclass of DecryptionError."""
        assert not issubclass(SerializationError, DecryptionError)

    def test_serialization_error_not_caught_by_encryption_handler(self) -> None:
        """SerializationError is not caught by except EncryptionError."""
        with pytest.raises(SerializationError):
            try:
                raise SerializationError("bad json")
            except EncryptionError:
                pytest.fail("SerializationError caught by EncryptionError")

    def test_serialization_error_chaining_preserves_cause(self) -> None:
        """Raise SerializationError from original preserves __cause__."""
        original = TypeError("datetime not serializable")
        try:
            raise SerializationError("serialization failed") from original
        except SerializationError as exc:
            assert exc.__cause__ is original


# ---------------------------------------------------------------------------
# ConfigurationError Hierarchy
# ---------------------------------------------------------------------------


class TestConfigurationErrorHierarchy:
    """ConfigurationError is a sibling of other SecureSessionError subclasses."""

    def test_configuration_error_inherits_from_base(self) -> None:
        """ConfigurationError is a subclass of SecureSessionError."""
        assert issubclass(ConfigurationError, SecureSessionError)

    def test_configuration_error_caught_by_base(self) -> None:
        """ConfigurationError is caught by except SecureSessionError."""
        with pytest.raises(SecureSessionError):
            raise ConfigurationError("bad config")

    def test_configuration_error_not_subclass_of_encryption(self) -> None:
        """ConfigurationError is not a subclass of EncryptionError."""
        assert not issubclass(ConfigurationError, EncryptionError)

    def test_configuration_error_not_subclass_of_decryption(self) -> None:
        """ConfigurationError is not a subclass of DecryptionError."""
        assert not issubclass(ConfigurationError, DecryptionError)

    def test_configuration_error_not_subclass_of_serialization(self) -> None:
        """ConfigurationError is not a subclass of SerializationError."""
        assert not issubclass(ConfigurationError, SerializationError)

    def test_configuration_error_not_caught_by_encryption_handler(self) -> None:
        """ConfigurationError is not caught by except EncryptionError."""
        with pytest.raises(ConfigurationError):
            try:
                raise ConfigurationError("bad config")
            except EncryptionError:
                pytest.fail("ConfigurationError caught by EncryptionError")

    def test_configuration_error_chaining_preserves_cause(self) -> None:
        """Raise ConfigurationError from original preserves __cause__."""
        original = OSError("cannot open database")
        try:
            raise ConfigurationError("config failed") from original
        except ConfigurationError as exc:
            assert exc.__cause__ is original

    def test_configuration_error_has_docstring(self) -> None:
        """ConfigurationError has a non-empty docstring."""
        assert ConfigurationError.__doc__ is not None
        assert len(ConfigurationError.__doc__.strip()) > 0

    def test_configuration_error_accepts_and_stores_message(self) -> None:
        """ConfigurationError accepts and stores a message."""
        msg = "invalid encryption key"
        exc = ConfigurationError(msg)
        assert str(exc) == msg
        assert exc.args == (msg,)

    def test_configuration_error_accepts_empty_message(self) -> None:
        """ConfigurationError accepts an empty message."""
        exc = ConfigurationError()
        assert str(exc) == ""
