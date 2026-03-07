"""Encryption backend protocol for adk-secure-sessions.

Defines the contract that all encryption backends must satisfy.
Backends implement async methods (``encrypt``, ``decrypt``),
synchronous counterparts (``sync_encrypt``, ``sync_decrypt``),
and a ``backend_id`` property. No inheritance is required; any class
with matching signatures conforms via structural subtyping (PEP 544).

Note: while the protocol itself requires no registration, the
serialization layer (``adk_secure_sessions.serialization``) maintains
a ``BACKEND_REGISTRY`` of recognized backend IDs. Custom backends
must register their ``backend_id`` there to be usable with the
envelope functions.

Examples:
    Define a conforming backend and verify at runtime:

    ```python
    class MyBackend:
        @property
        def backend_id(self) -> int:
            return 0x10

        def sync_encrypt(self, plaintext: bytes) -> bytes: ...
        def sync_decrypt(self, ciphertext: bytes) -> bytes: ...
        async def encrypt(self, plaintext: bytes) -> bytes: ...
        async def decrypt(self, ciphertext: bytes) -> bytes: ...


    from adk_secure_sessions.protocols import EncryptionBackend

    assert isinstance(MyBackend(), EncryptionBackend)  # True
    ```

See Also:
    [`adk_secure_sessions.backends.fernet`][adk_secure_sessions.backends.fernet]:
    Reference implementation using Fernet symmetric encryption.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EncryptionBackend(Protocol):
    """Contract for all encryption backends.

    Implementors provide:

    * ``backend_id`` — read-only property returning the unique
      envelope backend identifier byte.
    * ``sync_encrypt`` / ``sync_decrypt`` — synchronous methods
      used by SQLAlchemy TypeDecorators in sync contexts.
    * ``encrypt`` / ``decrypt`` — async wrappers for use in
      async application code.

    The session service uses this protocol for runtime validation
    at initialization and static type checkers verify conformance
    at analysis time.

    This is a ``typing.Protocol`` — not an abstract base class.
    Conforming classes do not need to inherit from or import this
    protocol.

    Known limitations of ``@runtime_checkable``:

    * ``isinstance()`` checks verify method **existence** only. It
      does not validate parameter types, return types, or whether
      methods are coroutines. Use a static type checker (mypy,
      pyright) for full signature validation.

    Examples:
        Define a minimal conforming backend:

        ```python
        from adk_secure_sessions.protocols import EncryptionBackend


        class MyBackend:
            @property
            def backend_id(self) -> int:
                return 0x10

            def sync_encrypt(self, plaintext: bytes) -> bytes:
                return plaintext  # replace with real encryption

            def sync_decrypt(self, ciphertext: bytes) -> bytes:
                return ciphertext  # replace with real decryption

            async def encrypt(self, plaintext: bytes) -> bytes:
                return self.sync_encrypt(plaintext)

            async def decrypt(self, ciphertext: bytes) -> bytes:
                return self.sync_decrypt(ciphertext)


        assert isinstance(MyBackend(), EncryptionBackend)
        ```
    """

    @property
    def backend_id(self) -> int:
        """Unique backend identifier byte for the envelope header.

        Returns:
            Integer backend ID (e.g., ``0x01`` for Fernet,
            ``0x02`` for AES-GCM).

        Examples:
            ```python
            assert backend.backend_id == 0x01
            ```
        """
        ...

    def sync_encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes synchronously.

        Used by SQLAlchemy TypeDecorators that operate in sync
        contexts. The async ``encrypt`` method should delegate
        to this via ``asyncio.to_thread()``.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted ciphertext as bytes.

        Examples:
            ```python
            ciphertext = backend.sync_encrypt(b"hello")
            ```
        """
        ...

    def sync_decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes synchronously.

        Used by SQLAlchemy TypeDecorators that operate in sync
        contexts. The async ``decrypt`` method should delegate
        to this via ``asyncio.to_thread()``.

        Args:
            ciphertext: Encrypted bytes to decrypt.

        Returns:
            Decrypted plaintext as bytes.

        Examples:
            ```python
            plaintext = backend.sync_decrypt(ciphertext)
            ```
        """
        ...

    async def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext bytes asynchronously.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            Encrypted ciphertext as bytes.

        Examples:
            ```python
            ciphertext = await backend.encrypt(b"hello")
            ```
        """
        ...

    async def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext bytes asynchronously.

        Args:
            ciphertext: Encrypted bytes to decrypt.

        Returns:
            Decrypted plaintext as bytes.

        Examples:
            ```python
            plaintext = await backend.decrypt(ciphertext)
            ```
        """
        ...
