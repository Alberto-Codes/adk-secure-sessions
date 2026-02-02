"""Tests for the exception hierarchy.

Validates inheritance relationships, sibling independence, message
handling, exception chaining, and raise-site message safety.
"""

from __future__ import annotations

import pytest

from adk_secure_sessions.exceptions import (
    DecryptionError,
    EncryptionError,
    SecureSessionError,
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
