"""Tests for EncryptionBackend protocol conformance and runtime validation."""

from __future__ import annotations

import pytest

from adk_secure_sessions.protocols import EncryptionBackend

pytestmark = pytest.mark.unit

# --- US2: Runtime Validation ---


class TestConformingBackend:
    """A class with matching async encrypt/decrypt passes isinstance."""

    def test_conforming_class_passes_isinstance(self) -> None:
        """Verify a class with all protocol methods passes isinstance check."""

        class GoodBackend:
            @property
            def backend_id(self) -> int:
                return 0x01

            def sync_encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

            async def encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

        assert isinstance(GoodBackend(), EncryptionBackend)

    def test_missing_decrypt_fails_isinstance(self) -> None:
        """Verify a class missing decrypt fails isinstance check."""

        class EncryptOnly:
            @property
            def backend_id(self) -> int:
                return 0x01

            def sync_encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

            async def encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

        assert not isinstance(EncryptOnly(), EncryptionBackend)

    def test_missing_encrypt_fails_isinstance(self) -> None:
        """Verify a class missing encrypt fails isinstance check."""

        class DecryptOnly:
            @property
            def backend_id(self) -> int:
                return 0x01

            def sync_encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

        assert not isinstance(DecryptOnly(), EncryptionBackend)

    def test_missing_sync_encrypt_fails_isinstance(self) -> None:
        """Verify a class missing sync_encrypt fails isinstance check."""

        class NoSyncEncrypt:
            @property
            def backend_id(self) -> int:
                return 0x01

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

            async def encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

        assert not isinstance(NoSyncEncrypt(), EncryptionBackend)

    def test_missing_backend_id_fails_isinstance(self) -> None:
        """Verify a class missing backend_id fails isinstance check."""

        class NoBackendId:
            def sync_encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

            async def encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

        assert not isinstance(NoBackendId(), EncryptionBackend)

    def test_empty_class_fails_isinstance(self) -> None:
        """Verify a class with no methods fails isinstance check."""

        class Empty:
            pass

        assert not isinstance(Empty(), EncryptionBackend)

    def test_sync_async_methods_pass_isinstance_known_limitation(self) -> None:
        """Sync encrypt/decrypt pass isinstance check.

        ``@runtime_checkable`` does not distinguish coroutine functions
        from regular functions. This is a known Python limitation
        documented in the protocol docstring. Static type checkers
        catch this mismatch.
        """

        class SyncAsyncBackend:
            @property
            def backend_id(self) -> int:
                return 0x01

            def sync_encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

            def encrypt(self, plaintext: bytes) -> bytes:
                return plaintext

            def decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext

        assert isinstance(SyncAsyncBackend(), EncryptionBackend)


# --- US3: Third-Party Extensibility ---


class TestThirdPartyExtensibility:
    """Structural subtyping works for third-party backends.

    A class defined without importing adk_secure_sessions passes the
    protocol check — verifying structural subtyping works for
    third-party backends.
    """

    def test_standalone_class_passes_isinstance(self) -> None:
        """Verify a standalone class conforms via structural subtyping."""

        # This class is defined here without inheriting from or
        # importing EncryptionBackend. It conforms purely via
        # structural subtyping.
        class ExternalKmsBackend:
            @property
            def backend_id(self) -> int:
                return 0x10

            def sync_encrypt(self, plaintext: bytes) -> bytes:
                return b"kms:" + plaintext

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext.removeprefix(b"kms:")

            async def encrypt(self, plaintext: bytes) -> bytes:
                return b"kms:" + plaintext

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext.removeprefix(b"kms:")

        backend = ExternalKmsBackend()
        assert isinstance(backend, EncryptionBackend)
